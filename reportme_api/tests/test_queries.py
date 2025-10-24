"""
Testes para o módulo de consultas (core.queries)
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock

from core.models import Query, Parameter, QueryExecution, Connection, Project, ProjectNode
from core.serializers import QuerySerializer, ParameterSerializer, QueryExecutionSerializer
from tests import BaseAPITestCase, BaseTestCase, TestDataFactory, TestConstants, ValidationTestMixin

User = get_user_model()


class QueryViewSetTestCase(BaseAPITestCase):
    """Testa API views do modelo Query"""
    
    def setUp(self):
        super().setUp()
        self.list_url = reverse('query-list')
        
    def test_create_query_success(self):
        """Testa criação de consulta com sucesso"""
        data = {
            'name': 'Nova Consulta',
            'query': TestConstants.VALID_SELECT_QUERY,
            'connection': self.test_connection.id,
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Nova Consulta')
        self.assertEqual(response.data['query'], TestConstants.VALID_SELECT_QUERY)
        
    def test_create_query_with_parameters(self):
        """Testa criação de consulta com parâmetros"""
        data = {
            'name': 'Consulta com Parâmetros',
            'query': TestConstants.QUERY_WITH_PARAMS,
            'connection': self.test_connection.id,
            'query_parameters': [
                {
                    'name': 'user_id',
                    'type': 'number',
                    'allow_null': False,
                    'default_value': '1'
                }
            ]
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['query_parameters']), 1)
        self.assertEqual(response.data['query_parameters'][0]['name'], 'user_id')
        
    def test_create_query_permission_denied(self):
        """Testa criação de consulta sem permissão"""
        self.client.logout()
        
        data = {
            'name': 'Consulta Negada',
            'query': TestConstants.VALID_SELECT_QUERY,
            'connection': self.test_connection.id,
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_create_query_invalid_sql(self):
        """Testa criação de consulta com SQL inválido"""
        data = {
            'name': 'Consulta Inválida',
            'query': TestConstants.INVALID_INSERT_QUERY,
            'connection': self.test_connection.id,
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_list_queries_success(self):
        """Testa listagem de consultas"""
        # Criar consulta de teste
        TestDataFactory.create_query(
            connection=self.test_connection,
            query=TestConstants.VALID_SELECT_QUERY,
            created_by=self.admin_user
        )
        
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
        
    def test_update_query_success(self):
        """Testa atualização de consulta"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        url = reverse('query-detail', kwargs={'pk': query.id})
        data = {
            'name': query.name,
            'query': 'SELECT 2 as updated_column',
            'connection': self.test_connection.id,
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], 'SELECT 2 as updated_column')
        
    def test_delete_query_success(self):
        """Testa exclusão de consulta"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        url = reverse('query-detail', kwargs={'pk': query.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Query.objects.filter(id=query.id).exists())
        
    def test_delete_query_permission_denied(self):
        """Testa exclusão de consulta sem permissão"""
        other_user = TestDataFactory.create_user(username='other_user')
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=other_user
        )
        
        url = reverse('query-detail', kwargs={'pk': query.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_validate_sql_success(self):
        """Testa validação de SQL bem-sucedida"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        url = reverse('query-validate-sql', kwargs={'pk': query.id})
        data = {'query': TestConstants.VALID_SELECT_QUERY}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_validate_sql_invalid(self):
        """Testa validação de SQL inválido"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        url = reverse('query-validate-sql', kwargs={'pk': query.id})
        data = {'query': TestConstants.INVALID_INSERT_QUERY}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_get_query_detail_success(self):
        """Testa obtenção de detalhes da consulta"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        url = reverse('query-detail', kwargs={'pk': query.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], query.query)


class QueryExecutionViewSetTestCase(BaseAPITestCase):
    """Testa execução de consultas"""
    
    def setUp(self):
        super().setUp()
        self.test_query = TestDataFactory.create_query(
            connection=self.test_connection,
            query='SELECT :test_param as param_value',
            created_by=self.admin_user
        )
        # Criar parâmetro para a consulta
        Parameter.objects.create(
            name='test_param',
            type='string',
            query=self.test_query,
            default_value='test_value'
        )
        
    def test_execute_query_success(self):
        """Testa execução de consulta com sucesso"""
        url = reverse('query-execute', kwargs={'pk': self.test_query.id})
        data = {
            'parameters': {
                'test_param': 'valor_teste'
            }
        }
        
        with patch('core.services.QueryExecutionService.execute_query') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'data': [{'param_value': 'valor_teste'}],
                'execution_time': 0.1,
                'rows_count': 1
            }
            
            response = self.client.post(url, data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
    def test_execute_query_missing_parameters(self):
        """Testa execução de consulta com parâmetros obrigatórios ausentes"""
        required_query = TestDataFactory.create_query(
            connection=self.test_connection,
            query='SELECT :required_param as value',
            created_by=self.admin_user
        )
        Parameter.objects.create(
            name='required_param',
            type='string',
            query=required_query,
            allow_null=False
        )
        
        url = reverse('query-execute', kwargs={'pk': required_query.id})
        data = {'parameters': {}}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_execute_query_permission_denied(self):
        """Testa execução de consulta sem permissão"""
        other_user = TestDataFactory.create_user(username='other_user')
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=other_user
        )
        
        url = reverse('query-execute', kwargs={'pk': query.id})
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_get_execution_history(self):
        """Testa obtenção do histórico de execuções"""
        # Criar histórico de execução
        QueryExecution.objects.create(
            query=self.test_query,
            user=self.admin_user,
            parameters={'test_param': 'value'},
            status='success',
            execution_time=0.1,
            rows_returned=1
        )
        
        url = reverse('query-execution-history', kwargs={'pk': self.test_query.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)


class ParameterModelTestCase(BaseTestCase):
    """Testa modelo Parameter"""
    
    def setUp(self):
        super().setUp()
        self.test_query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
    def test_parameter_creation(self):
        """Testa criação de parâmetro"""
        parameter = Parameter.objects.create(
            name='test_param',
            type='string',
            query=self.test_query,
            allow_null=True,
            default_value='default'
        )
        
        self.assertEqual(parameter.name, 'test_param')
        self.assertEqual(parameter.type, 'string')
        self.assertEqual(parameter.query, self.test_query)
        self.assertTrue(parameter.allow_null)
        self.assertEqual(parameter.default_value, 'default')
        
    def test_parameter_string_representation(self):
        """Testa representação string do parâmetro"""
        parameter = Parameter.objects.create(
            name='test_param',
            type='number',
            query=self.test_query
        )
        
        expected = 'test_param (number)'
        self.assertEqual(str(parameter), expected)
        
    def test_parameter_types(self):
        """Testa diferentes tipos de parâmetros"""
        types = ['string', 'number', 'date', 'datetime', 'boolean', 'list']
        
        for param_type in types:
            parameter = Parameter.objects.create(
                name=f'param_{param_type}',
                type=param_type,
                query=self.test_query
            )
            self.assertEqual(parameter.type, param_type)
            
    def test_parameter_with_options(self):
        """Testa parâmetro com opções (tipo lista)"""
        parameter = Parameter.objects.create(
            name='list_param',
            type='list',
            query=self.test_query,
            options=['option1', 'option2', 'option3']
        )
        
        self.assertEqual(parameter.options, ['option1', 'option2', 'option3'])
        self.assertEqual(len(parameter.options), 3)


class QueryModelTestCase(BaseTestCase):
    """Testa modelo Query"""
    
    def test_query_creation(self):
        """Testa criação de consulta"""
        query = Query.objects.create(
            name='Consulta Teste',
            query='SELECT 1 as test',
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        self.assertEqual(query.name, 'Consulta Teste')
        self.assertEqual(query.query, 'SELECT 1 as test')
        self.assertEqual(query.connection, self.test_connection)
        self.assertEqual(query.created_by, self.admin_user)
        self.assertIsNotNone(query.created_at)
    
    def test_query_string_representation(self):
        """Testa representação string da consulta"""
        query = Query.objects.create(
            name='Consulta Teste',
            query='SELECT 1',
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        expected = 'Consulta Teste - SQLite Teste'
        self.assertEqual(str(query), expected)
    
    def test_query_with_parameters(self):
        """Testa consulta com parâmetros"""
        query = Query.objects.create(
            name='Consulta com Parâmetros',
            query='SELECT * FROM users WHERE id = :user_id',
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        # Adicionar parâmetro
        Parameter.objects.create(
            name='user_id',
            type='number',
            query=query,
            allow_null=False
        )
        
        self.assertEqual(query.query_parameters.count(), 1)
        self.assertEqual(query.query_parameters.first().name, 'user_id')
        
    def test_get_sql_parameters_method(self):
        """Testa método get_sql_parameters"""
        query = Query.objects.create(
            name='Query com Params',
            query='SELECT * FROM table WHERE id = :id AND name = :name',
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        params = query.get_sql_parameters()
        self.assertIn('id', params)
        self.assertIn('name', params)
        self.assertEqual(len(params), 2)
        
    def test_extract_parameters_from_sql_method(self):
        """Testa método extract_parameters_from_sql"""
        query = Query.objects.create(
            name='Query Extraction Test',
            query='SELECT * FROM users WHERE age > :min_age AND city = :city',
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        extracted = query.extract_parameters_from_sql()
        self.assertEqual(len(extracted), 2)
        
        param_names = [p['name'] for p in extracted]
        self.assertIn('min_age', param_names)
        self.assertIn('city', param_names)


class QueryExecutionModelTestCase(BaseTestCase):
    """Testa modelo QueryExecution"""
    
    def setUp(self):
        super().setUp()
        self.test_query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
    def test_execution_creation(self):
        """Testa criação de execução"""
        execution = QueryExecution.objects.create(
            query=self.test_query,
            user=self.admin_user,
            parameters={'param1': 'value1'},
            status='success',
            execution_time=0.5,
            rows_returned=10
        )
        
        self.assertEqual(execution.query, self.test_query)
        self.assertEqual(execution.user, self.admin_user)
        self.assertEqual(execution.parameters, {'param1': 'value1'})
        self.assertEqual(execution.status, 'success')
        self.assertEqual(execution.execution_time, 0.5)
        self.assertEqual(execution.rows_returned, 10)
        
    def test_execution_string_representation(self):
        """Testa representação string da execução"""
        execution = QueryExecution.objects.create(
            query=self.test_query,
            user=self.admin_user,
            status='success'
        )
        
        expected_start = f"{self.test_query.name} -"
        self.assertTrue(str(execution).startswith(expected_start))
        
    def test_execution_status_choices(self):
        """Testa diferentes status de execução"""
        statuses = ['success', 'error', 'timeout']
        
        for status_choice in statuses:
            execution = QueryExecution.objects.create(
                query=self.test_query,
                user=self.admin_user,
                status=status_choice
            )
            self.assertEqual(execution.status, status_choice)
            
    def test_execution_with_error(self):
        """Testa execução com erro"""
        execution = QueryExecution.objects.create(
            query=self.test_query,
            user=self.admin_user,
            status='error',
            error_message='Syntax error in SQL'
        )
        
        self.assertEqual(execution.status, 'error')
        self.assertEqual(execution.error_message, 'Syntax error in SQL')


class QuerySerializerTestCase(BaseTestCase, ValidationTestMixin):
    """Testa serializers do módulo Query"""
    
    def setUp(self):
        super().setUp()
        
    def test_query_serializer_valid_data(self):
        """Testa serializer com dados válidos"""
        data = {
            'name': 'Test Query',
            'query': 'SELECT 1 as test',
            'connection': self.test_connection.id,
        }
        
        serializer = QuerySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_query_serializer_invalid_data(self):
        """Testa serializer com dados inválidos"""
        data = {
            'name': '',  # Nome obrigatório
            'query': '',  # Query obrigatória
        }
        
        serializer = QuerySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
        self.assertIn('query', serializer.errors)
        
    def test_parameter_serializer_valid_data(self):
        """Testa serializer de parâmetro com dados válidos"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        data = {
            'name': 'test_param',
            'type': 'string',
            'query': query.id,
            'allow_null': True
        }
        
        serializer = ParameterSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
    def test_query_execution_serializer(self):
        """Testa serializer de execução"""
        query = TestDataFactory.create_query(
            connection=self.test_connection,
            created_by=self.admin_user
        )
        
        execution = QueryExecution.objects.create(
            query=query,
            user=self.admin_user,
            parameters={'test': 'value'},
            status='success'
        )
        
        serializer = QueryExecutionSerializer(execution)
        data = serializer.data
        
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['parameters'], {'test': 'value'})


class QueryIntegrationTestCase(BaseAPITestCase):
    """Testes de integração do módulo Query"""
    
    def test_full_query_lifecycle(self):
        """Testa ciclo completo de uma consulta"""
        # 1. Criar consulta
        create_data = {
            'name': 'Lifecycle Test Query',
            'query': 'SELECT :test_param as result',
            'connection': self.test_connection.id,
        }
        
        response = self.client.post(reverse('query-list'), create_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        query_id = response.data['id']
        
        # 2. Adicionar parâmetro
        param_data = {
            'name': 'test_param',
            'type': 'string',
            'query': query_id,
            'default_value': 'default_test'
        }
        
        response = self.client.post(reverse('parameter-list'), param_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 3. Executar consulta
        with patch('core.services.QueryExecutionService.execute_query') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'data': [{'result': 'test_value'}],
                'execution_time': 0.1,
                'rows_count': 1
            }
            
            execute_data = {
                'parameters': {'test_param': 'test_value'}
            }
            
            response = self.client.post(
                reverse('query-execute', kwargs={'pk': query_id}),
                execute_data,
                format='json'
            )
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # 4. Verificar histórico
        response = self.client.get(
            reverse('query-execution-history', kwargs={'pk': query_id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 5. Atualizar consulta
        update_data = {
            'name': 'Updated Lifecycle Query',
            'query': 'SELECT :test_param as updated_result',
            'connection': self.test_connection.id,
        }
        
        response = self.client.put(
            reverse('query-detail', kwargs={'pk': query_id}),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Lifecycle Query')
        
        # 6. Deletar consulta
        response = self.client.delete(reverse('query-detail', kwargs={'pk': query_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)