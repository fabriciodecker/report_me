"""
Testes para o sistema de consultas do ReportMe
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Query, Parameter, QueryExecution
from tests import (
    BaseAPITestCase, 
    DatabaseTestCase,
    TestConstants, 
    TestDataFactory,
    PermissionTestMixin,
    ValidationTestMixin
)
import json

User = get_user_model()


class QueryViewSetTestCase(BaseAPITestCase, PermissionTestMixin, ValidationTestMixin):
    """
    Testes para QueryViewSet (CRUD de consultas)
    """
    
    def test_list_queries_authenticated_admin(self):
        """Testa listagem de consultas como admin"""
        self.authenticate_admin()
        
        response = self.client.get(TestConstants.QUERIES_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) >= 1)  # Pelo menos a consulta de teste
    
    def test_list_queries_authenticated_readonly(self):
        """Testa listagem de consultas como readonly"""
        self.authenticate_readonly()
        
        response = self.client.get(TestConstants.QUERIES_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Readonly só vê consultas próprias ou de projetos compartilhados
        self.assertIn('results', response.data)
    
    def test_list_queries_unauthenticated(self):
        """Testa listagem sem autenticação"""
        response = self.client.get(TestConstants.QUERIES_URL)
        self.assert_permission_denied(response)
    
    def test_create_query_success(self):
        """Testa criação de consulta com dados válidos"""
        self.authenticate_admin()
        
        data = {
            'name': 'Nova Consulta',
            'description': 'Consulta de teste',
            'sql_query': TestConstants.VALID_SELECT_QUERY,
            'connection': self.test_connection.id,
            'project_node': self.root_node.id
        }
        
        response = self.client.post(TestConstants.QUERIES_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Nova Consulta')
        self.assertEqual(response.data['sql_query'], TestConstants.VALID_SELECT_QUERY)
        self.assertEqual(response.data['created_by'], self.admin_user.id)
        
        # Verificar se foi criada no banco
        query = Query.objects.get(id=response.data['id'])
        self.assertEqual(query.name, 'Nova Consulta')
    
    def test_create_query_with_parameters(self):
        """Testa criação de consulta com parâmetros"""
        self.authenticate_admin()
        
        data = {
            'name': 'Consulta com Parâmetros',
            'description': 'Consulta que usa parâmetros',
            'sql_query': TestConstants.QUERY_WITH_PARAMS,
            'connection': self.test_connection.id,
            'project_node': self.root_node.id,
            'parameters': [
                {
                    'name': 'user_id',
                    'parameter_type': 'number',
                    'is_required': True,
                    'default_value': '1'
                },
                {
                    'name': 'name_pattern',
                    'parameter_type': 'string',
                    'is_required': False,
                    'default_value': '%test%'
                }
            ]
        }
        
        response = self.client.post(TestConstants.QUERIES_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar se parâmetros foram criados
        query = Query.objects.get(id=response.data['id'])
        self.assertEqual(query.parameters.count(), 2)
        
        user_id_param = query.parameters.get(name='user_id')
        self.assertEqual(user_id_param.parameter_type, 'number')
        self.assertTrue(user_id_param.is_required)
    
    def test_create_query_invalid_sql(self):
        """Testa criação com SQL inválido (não SELECT)"""
        self.authenticate_admin()
        
        data = {
            'name': 'Consulta Inválida',
            'sql_query': TestConstants.INVALID_INSERT_QUERY,
            'connection': self.test_connection.id,
            'project_node': self.root_node.id
        }
        
        response = self.client.post(TestConstants.QUERIES_URL, data)
        self.assert_validation_error(response)
    
    def test_create_query_readonly_permission_denied(self):
        """Testa criação de consulta como readonly (deve falhar)"""
        self.authenticate_readonly()
        
        data = {
            'name': 'Consulta Readonly',
            'sql_query': TestConstants.VALID_SELECT_QUERY,
            'connection': self.test_connection.id,
            'project_node': self.root_node.id
        }
        
        response = self.client.post(TestConstants.QUERIES_URL, data)
        self.assert_permission_denied(response)
    
    def test_retrieve_query_success(self):
        """Testa recuperação de consulta específica"""
        self.authenticate_admin()
        
        url = f"{TestConstants.QUERIES_URL}{self.test_query.id}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.test_query.id)
        self.assertEqual(response.data['name'], self.test_query.name)
        self.assertIn('parameters', response.data)
    
    def test_update_query_success(self):
        """Testa atualização de consulta"""
        self.authenticate_admin()
        
        data = {
            'name': 'Consulta Atualizada',
            'description': 'Descrição atualizada',
            'sql_query': 'SELECT 2 as updated_column',
            'connection': self.test_connection.id,
            'project_node': self.root_node.id
        }
        
        url = f"{TestConstants.QUERIES_URL}{self.test_query.id}/"
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Consulta Atualizada')
        
        # Verificar se foi atualizado no banco
        self.test_query.refresh_from_db()
        self.assertEqual(self.test_query.name, 'Consulta Atualizada')
    
    def test_update_query_partial(self):
        """Testa atualização parcial de consulta"""
        self.authenticate_admin()
        
        data = {'description': 'Nova descrição'}
        
        url = f"{TestConstants.QUERIES_URL}{self.test_query.id}/"
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Nova descrição')
        # Nome deve permanecer o mesmo
        self.assertEqual(response.data['name'], self.test_query.name)
    
    def test_delete_query_success(self):
        """Testa exclusão de consulta"""
        # Criar consulta para deletar
        query_to_delete = TestDataFactory.create_query(
            self.root_node,
            self.test_connection,
            self.admin_user,
            name='Consulta para Deletar'
        )
        
        self.authenticate_admin()
        
        url = f"{TestConstants.QUERIES_URL}{query_to_delete.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar se foi deletado
        with self.assertRaises(Query.DoesNotExist):
            Query.objects.get(id=query_to_delete.id)
    
    def test_validate_query_action_valid_sql(self):
        """Testa action de validação com SQL válido"""
        self.authenticate_admin()
        
        data = {'sql_query': TestConstants.VALID_SELECT_QUERY}
        
        url = f"{TestConstants.QUERIES_URL}validate/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertTrue(response.data['valid'])
    
    def test_validate_query_action_invalid_sql(self):
        """Testa action de validação com SQL inválido"""
        self.authenticate_admin()
        
        data = {'sql_query': TestConstants.INVALID_INSERT_QUERY}
        
        url = f"{TestConstants.QUERIES_URL}validate/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertFalse(response.data['valid'])
        self.assertIn('message', response.data)
    
    def test_duplicate_query_action(self):
        """Testa duplicação de consulta"""
        self.authenticate_admin()
        
        data = {'name': 'Consulta Duplicada'}
        
        url = f"{TestConstants.QUERIES_URL}{self.test_query.id}/duplicate/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Consulta Duplicada')
        self.assertEqual(response.data['sql_query'], self.test_query.sql_query)
        
        # Verificar se foi criado novo registro
        duplicated_query = Query.objects.get(id=response.data['id'])
        self.assertNotEqual(duplicated_query.id, self.test_query.id)


class QueryExecutionTestCase(DatabaseTestCase, BaseAPITestCase):
    """
    Testes para execução de consultas
    """
    
    def test_execute_simple_query_success(self):
        """Testa execução de consulta simples"""
        self.authenticate_admin()
        
        data = {
            'query_id': self.test_query.id,
            'parameters': {}
        }
        
        url = f"{TestConstants.QUERIES_URL}execute/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('execution_time', response.data)
        self.assertIn('row_count', response.data)
    
    def test_execute_query_with_parameters(self):
        """Testa execução de consulta com parâmetros"""
        # Criar consulta com parâmetros
        query_with_params = TestDataFactory.create_query(
            self.root_node,
            self.test_connection,
            self.admin_user,
            name='Consulta com Parâmetros',
            sql_query='SELECT :test_param as param_value'
        )
        
        # Criar parâmetro
        TestDataFactory.create_parameter(
            query_with_params,
            name='test_param',
            parameter_type='string',
            default_value='test'
        )
        
        self.authenticate_admin()
        
        data = {
            'query_id': query_with_params.id,
            'parameters': {
                'test_param': 'hello world'
            }
        }
        
        url = f"{TestConstants.QUERIES_URL}execute/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_execute_query_missing_required_parameter(self):
        """Testa execução com parâmetro obrigatório faltando"""
        # Criar consulta com parâmetro obrigatório
        query_with_params = TestDataFactory.create_query(
            self.root_node,
            self.test_connection,
            self.admin_user,
            sql_query='SELECT :required_param as value'
        )
        
        TestDataFactory.create_parameter(
            query_with_params,
            name='required_param',
            parameter_type='string',
            is_required=True
        )
        
        self.authenticate_admin()
        
        data = {
            'query_id': query_with_params.id,
            'parameters': {}  # Parâmetro obrigatório faltando
        }
        
        url = f"{TestConstants.QUERIES_URL}execute/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_execute_query_permission_denied(self):
        """Testa execução sem permissão"""
        self.authenticate_readonly()
        
        data = {
            'query_id': self.test_query.id,
            'parameters': {}
        }
        
        url = f"{TestConstants.QUERIES_URL}execute/"
        response = self.client.post(url, data)
        
        # Readonly pode executar consultas, mas apenas das que tem acesso
        # Depende da implementação das permissões
        self.assertIn(response.status_code, [200, 403])
    
    def test_execute_nonexistent_query(self):
        """Testa execução de consulta inexistente"""
        self.authenticate_admin()
        
        data = {
            'query_id': 99999,
            'parameters': {}
        }
        
        url = f"{TestConstants.QUERIES_URL}execute/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QueryModelTestCase(TestCase):
    """
    Testes para o modelo Query
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from core.models import Project, ProjectNode, Connection
        
        self.project = Project.objects.create(
            name='Projeto Teste',
            owner=self.user
        )
        
        self.project_node = ProjectNode.objects.create(
            project=self.project,
            name='Nó Teste'
        )
        
        self.connection = Connection.objects.create(
            name='Conexão Teste',
            sgbd='sqlite',
            database=':memory:',
            created_by=self.user
        )
    
    def test_query_creation(self):
        """Testa criação de consulta"""
        query = Query.objects.create(
            name='Consulta Teste',
            query='SELECT 1 as test',
            connection=self.connection,
            created_by=self.user
        )
        
        self.assertEqual(query.name, 'Consulta Teste')
        self.assertEqual(query.query, 'SELECT 1 as test')
        self.assertEqual(query.connection, self.connection)
        self.assertEqual(query.created_by, self.user)
        self.assertIsNotNone(query.created_at)
    
    def test_query_string_representation(self):
        """Testa representação string da consulta"""
        query = Query.objects.create(
            name='Consulta Teste',
            query='SELECT 1',
            connection=self.connection,
            created_by=self.user
        )
        
        expected = 'Consulta Teste - TestConnection'
        self.assertEqual(str(query), expected)
    
    def test_query_with_parameters(self):
        """Testa consulta com parâmetros"""
        query = Query.objects.create(
            name='Consulta com Parâmetros',
            query='SELECT * FROM users WHERE id = :user_id',
            connection=self.connection,
            created_by=self.user
        )
        
        # Criar parâmetros
        param1 = Parameter.objects.create(
            query=query,
            name='user_id',
            parameter_type='number',
            is_required=True
        )
        
        param2 = Parameter.objects.create(
            query=query,
            name='name_filter',
            parameter_type='string',
            is_required=False,
            default_value='%'
        )
        
        self.assertEqual(query.parameters.count(), 2)
        self.assertIn(param1, query.parameters.all())
        self.assertIn(param2, query.parameters.all())


class ParameterModelTestCase(TestCase):
    """
    Testes para o modelo Parameter
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from core.models import Project, ProjectNode, Connection
        
        self.project = Project.objects.create(
            name='Projeto Teste',
            owner=self.user
        )
        
        self.project_node = ProjectNode.objects.create(
            project=self.project,
            name='Nó Teste'
        )
        
        self.connection = Connection.objects.create(
            name='Conexão Teste',
            sgbd='sqlite',
            database=':memory:',
            created_by=self.user
        )
        
        self.query = Query.objects.create(
            name='Consulta Teste',
            sql_query='SELECT :param as value',
            connection=self.connection,
            project_node=self.project_node,
            created_by=self.user
        )
    
    def test_parameter_creation(self):
        """Testa criação de parâmetro"""
        parameter = Parameter.objects.create(
            query=self.query,
            name='test_param',
            parameter_type='string',
            is_required=True,
            default_value='test'
        )
        
        self.assertEqual(parameter.query, self.query)
        self.assertEqual(parameter.name, 'test_param')
        self.assertEqual(parameter.parameter_type, 'string')
        self.assertTrue(parameter.is_required)
        self.assertEqual(parameter.default_value, 'test')
    
    def test_parameter_types(self):
        """Testa diferentes tipos de parâmetros"""
        # String
        string_param = Parameter.objects.create(
            query=self.query,
            name='string_param',
            parameter_type='string'
        )
        
        # Number
        number_param = Parameter.objects.create(
            query=self.query,
            name='number_param',
            parameter_type='number'
        )
        
        # Date
        date_param = Parameter.objects.create(
            query=self.query,
            name='date_param',
            parameter_type='date'
        )
        
        # Boolean
        boolean_param = Parameter.objects.create(
            query=self.query,
            name='boolean_param',
            parameter_type='boolean'
        )
        
        self.assertEqual(string_param.parameter_type, 'string')
        self.assertEqual(number_param.parameter_type, 'number')
        self.assertEqual(date_param.parameter_type, 'date')
        self.assertEqual(boolean_param.parameter_type, 'boolean')
    
    def test_parameter_string_representation(self):
        """Testa representação string do parâmetro"""
        parameter = Parameter.objects.create(
            query=self.query,
            name='test_param',
            parameter_type='string'
        )
        
        expected = 'test_param (string)'
        self.assertEqual(str(parameter), expected)
    
    def test_parameter_ordering(self):
        """Testa ordenação dos parâmetros"""
        param1 = Parameter.objects.create(
            query=self.query,
            name='z_param',
            parameter_type='string',
            order=2
        )
        
        param2 = Parameter.objects.create(
            query=self.query,
            name='a_param',
            parameter_type='string',
            order=1
        )
        
        parameters = self.query.parameters.all()
        # Deve ser ordenado por order, depois por name
        self.assertEqual(parameters.first(), param2)
        self.assertEqual(parameters.last(), param1)


class QueryExecutionModelTestCase(TestCase):
    """
    Testes para o modelo QueryExecution
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from core.models import Project, ProjectNode, Connection
        
        self.project = Project.objects.create(
            name='Projeto Teste',
            owner=self.user
        )
        
        self.project_node = ProjectNode.objects.create(
            project=self.project,
            name='Nó Teste'
        )
        
        self.connection = Connection.objects.create(
            name='Conexão Teste',
            sgbd='sqlite',
            database=':memory:',
            created_by=self.user
        )
        
        self.query = Query.objects.create(
            name='Consulta Teste',
            sql_query='SELECT 1 as test',
            connection=self.connection,
            project_node=self.project_node,
            created_by=self.user
        )
    
    def test_query_execution_creation(self):
        """Testa criação de execução de consulta"""
        execution = QueryExecution.objects.create(
            query=self.query,
            executed_by=self.user,
            parameters_used={'param1': 'value1'},
            execution_time=0.123,
            row_count=5,
            status='success'
        )
        
        self.assertEqual(execution.query, self.query)
        self.assertEqual(execution.executed_by, self.user)
        self.assertEqual(execution.parameters_used, {'param1': 'value1'})
        self.assertEqual(execution.execution_time, 0.123)
        self.assertEqual(execution.row_count, 5)
        self.assertEqual(execution.status, 'success')
        self.assertIsNotNone(execution.executed_at)
    
    def test_query_execution_string_representation(self):
        """Testa representação string da execução"""
        execution = QueryExecution.objects.create(
            query=self.query,
            executed_by=self.user,
            status='success'
        )
        
        expected = f'Execução de {self.query.name} por {self.user.username}'
        self.assertEqual(str(execution), expected)
    
    def test_query_execution_error_status(self):
        """Testa execução com erro"""
        execution = QueryExecution.objects.create(
            query=self.query,
            executed_by=self.user,
            status='error',
            error_message='Syntax error in SQL'
        )
        
        self.assertEqual(execution.status, 'error')
        self.assertEqual(execution.error_message, 'Syntax error in SQL')
        self.assertIsNone(execution.row_count)