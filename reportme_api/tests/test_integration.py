"""
Testes de Integração - FASE 7 - PASSO 7.2
Testa fluxos completos entre módulos da aplicação
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import tempfile
import os

from core.models import Project, ProjectNode, Connection, Query, Parameter, QueryExecution
from tests import BaseAPITestCase, TestDataFactory

User = get_user_model()


class FullWorkflowIntegrationTestCase(BaseAPITestCase):
    """
    Testa o fluxo completo da aplicação:
    1. Usuário se autentica
    2. Cria projeto e estrutura hierárquica
    3. Configura conexão com banco
    4. Cria consulta com parâmetros
    5. Executa consulta e obtém resultados
    """
    
    def test_complete_workflow_admin_user(self):
        """Testa fluxo completo como usuário administrador"""
        
        # 1. AUTENTICAÇÃO
        # Verificar se usuário está logado (usuário já autenticado no setUp)
        self.assertIsNotNone(self.admin_user)
        self.assertTrue(self.admin_user.is_authenticated)
        
        # 2. CRIAÇÃO DE PROJETO
        project_data = {
            'name': 'Projeto Integração',
            'description': 'Projeto criado no teste de integração'
        }
        response = self.client.post(reverse('project-list'), project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data['id']
        
        # Verificar que o projeto foi criado com nó raiz
        project = Project.objects.get(id=project_id)
        self.assertIsNotNone(project.first_node)
        
        # 3. CRIAÇÃO DE ESTRUTURA HIERÁRQUICA
        # Criar nó filho no projeto
        node_data = {
            'name': 'Relatórios Financeiros',
            'project': project_id,
            'parent': project.first_node.id,
            'description': 'Nó para relatórios financeiros'
        }
        response = self.client.post(reverse('projectnode-list'), node_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        financial_node_id = response.data['id']
        
        # 4. CONFIGURAÇÃO DE CONEXÃO
        connection_data = {
            'name': 'Base Vendas SQLite',
            'sgbd': 'sqlite',
            'database': ':memory:',
            'host': '',
            'port': None,
            'user': '',
            'password': ''
        }
        response = self.client.post(reverse('connection-list'), connection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        connection_id = response.data['id']
        
        # 5. CRIAÇÃO DE CONSULTA COM PARÂMETROS
        query_data = {
            'name': 'Vendas por Período',
            'query': 'SELECT COUNT(*) as total_vendas FROM vendas WHERE data_venda BETWEEN :data_inicio AND :data_fim',
            'connection': connection_id,
            'timeout': 30,
            'cache_duration': 0
        }
        response = self.client.post(reverse('query-list'), query_data, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        query_id = response.data['id']
        
        # 6. CRIAÇÃO DE PARÂMETROS DA CONSULTA
        parameters = [
            {
                'name': 'data_inicio',
                'type': 'date',
                'query': query_id,
                'allow_null': False,
                'default_value': '2024-01-01'
            },
            {
                'name': 'data_fim',
                'type': 'date',
                'query': query_id,
                'allow_null': False,
                'default_value': '2024-12-31'
            }
        ]
        
        for param_data in parameters:
            response = self.client.post(reverse('parameter-list'), param_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 7. VERIFICAÇÃO DA ESTRUTURA COMPLETA
        # Listar projetos
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
        
        # Listar conexões
        response = self.client.get(reverse('connection-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
        
        # Listar consultas
        response = self.client.get(reverse('query-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
        
        # 8. VERIFICAÇÃO DE INTEGRIDADE
        # Verificar que a query tem os parâmetros corretos
        query = Query.objects.get(id=query_id)
        self.assertEqual(query.query_parameters.count(), 2)
        
        param_names = [p.name for p in query.query_parameters.all()]
        self.assertIn('data_inicio', param_names)
        self.assertIn('data_fim', param_names)


class UserPermissionsIntegrationTestCase(BaseAPITestCase):
    """
    Testa integração do sistema de permissões entre módulos
    """
    
    def setUp(self):
        super().setUp()
        # Criar usuários com diferentes permissões
        self.readonly_user = TestDataFactory.create_user(
            username='readonly_user',
            email='readonly@test.com',
            is_staff=False
        )
        self.editor_user = TestDataFactory.create_user(
            username='editor_user',
            email='editor@test.com',
            is_staff=True
        )
        
    def test_readonly_user_permissions(self):
        """Testa permissões de usuário somente leitura"""
        
        # Logar como usuário readonly
        self.client.force_authenticate(user=self.readonly_user)
        
        # Deve conseguir listar projetos
        response = self.client.get(reverse('project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Não deve conseguir criar projeto
        project_data = {
            'name': 'Projeto Negado',
            'description': 'Não deve ser criado'
        }
        response = self.client.post(reverse('project-list'), project_data, format='json')
        self.assertIn(response.status_code, [401, 403])
        
        # Deve conseguir listar conexões próprias se tiver
        response = self.client.get(reverse('connection-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Não deve conseguir criar conexão
        connection_data = {
            'name': 'Conexão Negada',
            'sgbd': 'sqlite',
            'database': ':memory:'
        }
        response = self.client.post(reverse('connection-list'), connection_data, format='json')
        self.assertIn(response.status_code, [401, 403])
        
    def test_editor_user_permissions(self):
        """Testa permissões de usuário editor"""
        
        # Logar como usuário editor
        self.client.force_authenticate(user=self.editor_user)
        
        # Deve conseguir criar projeto
        project_data = {
            'name': 'Projeto Editor',
            'description': 'Criado por editor'
        }
        response = self.client.post(reverse('project-list'), project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data['id']
        
        # Deve conseguir criar conexão
        connection_data = {
            'name': 'Conexão Editor',
            'sgbd': 'sqlite',
            'database': ':memory:'
        }
        response = self.client.post(reverse('connection-list'), connection_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        connection_id = response.data['id']
        
        # Deve conseguir criar consulta
        query_data = {
            'name': 'Consulta Editor',
            'query': 'SELECT 1 as test',
            'connection': connection_id
        }
        response = self.client.post(reverse('query-list'), query_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DataIntegrityIntegrationTestCase(BaseAPITestCase):
    """
    Testa integridade referencial entre módulos
    """
    
    def test_cascade_deletion_project(self):
        """Testa exclusão em cascata quando projeto é deletado"""
        
        # Criar estrutura completa
        project = TestDataFactory.create_project(owner=self.user)
        connection = TestDataFactory.create_connection(created_by=self.user)
        query = TestDataFactory.create_query(
            connection=connection,
            created_by=self.user
        )
        
        # Associar query ao nó
        project.first_node.query = query
        project.first_node.save()
        
        # Criar execução
        execution = QueryExecution.objects.create(
            query=query,
            user=self.user,
            parameters={},
            status='success'
        )
        
        # IDs para verificar após exclusão
        project_id = project.id
        node_id = project.first_node.id
        query_id = query.id
        execution_id = execution.id
        
        # Deletar projeto
        response = self.client.delete(reverse('project-detail', kwargs={'pk': project_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que projeto e nós foram deletados
        self.assertFalse(Project.objects.filter(id=project_id).exists())
        self.assertFalse(ProjectNode.objects.filter(id=node_id).exists())
        
        # Query e execução devem permanecer (SET_NULL)
        self.assertTrue(Query.objects.filter(id=query_id).exists())
        self.assertTrue(QueryExecution.objects.filter(id=execution_id).exists())
        
    def test_cascade_deletion_connection(self):
        """Testa comportamento quando conexão é deletada"""
        
        # Criar estrutura
        connection = TestDataFactory.create_connection(created_by=self.user)
        query = TestDataFactory.create_query(
            connection=connection,
            created_by=self.user
        )
        
        # Criar execução
        execution = QueryExecution.objects.create(
            query=query,
            user=self.user,
            parameters={},
            status='success'
        )
        
        connection_id = connection.id
        query_id = query.id
        execution_id = execution.id
        
        # Deletar conexão
        response = self.client.delete(reverse('connection-detail', kwargs={'pk': connection_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Conexão deve ser deletada
        self.assertFalse(Connection.objects.filter(id=connection_id).exists())
        
        # Query e execução devem ser deletadas (CASCADE)
        self.assertFalse(Query.objects.filter(id=query_id).exists())
        self.assertFalse(QueryExecution.objects.filter(id=execution_id).exists())


class APIConsistencyIntegrationTestCase(BaseAPITestCase):
    """
    Testa consistência de comportamento entre diferentes APIs
    """
    
    def test_consistent_error_responses(self):
        """Testa que todas as APIs retornam erros de forma consistente"""
        
        # Testar 404 para recursos inexistentes
        endpoints = [
            ('project-detail', {'pk': 99999}),
            ('projectnode-detail', {'pk': 99999}),
            ('connection-detail', {'pk': 99999}),
            ('query-detail', {'pk': 99999}),
        ]
        
        for endpoint, kwargs in endpoints:
            response = self.client.get(reverse(endpoint, kwargs=kwargs))
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            
    def test_consistent_authentication_behavior(self):
        """Testa que todas as APIs protegidas requerem autenticação"""
        
        # Deslogar usuário
        self.client.force_authenticate(user=None)
        
        # Testar endpoints protegidos
        protected_endpoints = [
            'project-list',
            'projectnode-list',
            'connection-list',
            'query-list',
        ]
        
        for endpoint in protected_endpoints:
            response = self.client.get(reverse(endpoint))
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
    def test_consistent_pagination(self):
        """Testa que todas as APIs usam paginação consistente"""
        
        # Criar múltiplos registros
        for i in range(15):
            TestDataFactory.create_project(
                owner=self.user,
                name=f'Projeto {i}'
            )
            TestDataFactory.create_connection(
                created_by=self.user,
                name=f'Conexão {i}'
            )
        
        # Testar paginação
        paginated_endpoints = [
            'project-list',
            'connection-list',
        ]
        
        for endpoint in paginated_endpoints:
            response = self.client.get(reverse(endpoint))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verificar estrutura de paginação
            self.assertIn('results', response.data)
            self.assertIn('count', response.data)
            self.assertIn('next', response.data)
            self.assertIn('previous', response.data)
            
            # Verificar tamanho da página
            self.assertLessEqual(len(response.data['results']), 20)  # Page size padrão


class PerformanceIntegrationTestCase(BaseAPITestCase):
    """
    Testa performance e eficiência de consultas entre módulos
    """
    
    def test_efficient_queries_complex_structure(self):
        """Testa que consultas complexas são eficientes"""
        
        # Criar estrutura com múltiplos níveis
        project = TestDataFactory.create_project(owner=self.user)
        connection = TestDataFactory.create_connection(created_by=self.user)
        
        # Criar árvore com 3 níveis e múltiplos nós
        level1_nodes = []
        for i in range(5):
            node = TestDataFactory.create_project_node(
                project=project,
                parent=project.first_node,
                name=f'Nível 1 - {i}'
            )
            level1_nodes.append(node)
            
            # Nível 2
            for j in range(3):
                level2_node = TestDataFactory.create_project_node(
                    project=project,
                    parent=node,
                    name=f'Nível 2 - {i}.{j}'
                )
                
                # Nível 3 com queries
                for k in range(2):
                    query = TestDataFactory.create_query(
                        connection=connection,
                        created_by=self.user,
                        name=f'Query {i}.{j}.{k}'
                    )
                    TestDataFactory.create_project_node(
                        project=project,
                        parent=level2_node,
                        name=f'Nível 3 - {i}.{j}.{k}',
                        query=query
                    )
        
        # Testar que a árvore é carregada eficientemente
        with self.assertNumQueries(10):  # Máximo de 10 queries esperadas
            response = self.client.get(reverse('project-tree', kwargs={'pk': project.id}))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
        # Verificar estrutura retornada
        tree = response.data
        self.assertEqual(len(tree['children']), 5)  # 5 nós nível 1
        
        # Verificar primeiro nó nível 1
        level1_node = tree['children'][0]
        self.assertEqual(len(level1_node['children']), 3)  # 3 nós nível 2
        
        # Verificar primeiro nó nível 2
        level2_node = level1_node['children'][0]
        self.assertEqual(len(level2_node['children']), 2)  # 2 nós nível 3


class ErrorHandlingIntegrationTestCase(BaseAPITestCase):
    """
    Testa tratamento de erros em cenários de integração
    """
    
    def test_query_execution_with_invalid_connection(self):
        """Testa execução de query com conexão inválida"""
        
        # Criar query com conexão que será deletada
        connection = TestDataFactory.create_connection(created_by=self.user)
        query = TestDataFactory.create_query(
            connection=connection,
            created_by=self.user
        )
        
        # Deletar conexão
        connection.delete()
        
        # Tentar executar query
        execute_data = {'parameters': {}}
        response = self.client.post(
            reverse('query-execute', kwargs={'pk': query.id}),
            execute_data,
            format='json'
        )
        
        # Deve retornar erro graciosamente
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_circular_reference_prevention(self):
        """Testa prevenção de referências circulares em nós"""
        
        project = TestDataFactory.create_project(owner=self.user)
        
        # Criar nó filho
        child_data = {
            'name': 'Nó Filho',
            'project': project.id,
            'parent': project.first_node.id
        }
        response = self.client.post(reverse('projectnode-list'), child_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        child_id = response.data['id']
        
        # Tentar fazer o nó raiz ser filho do nó filho (referência circular)
        update_data = {
            'name': project.first_node.name,
            'project': project.id,
            'parent': child_id
        }
        response = self.client.put(
            reverse('projectnode-detail', kwargs={'pk': project.first_node.id}),
            update_data,
            format='json'
        )
        
        # Deve falhar com erro de validação
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)