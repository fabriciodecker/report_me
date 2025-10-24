"""
Testes para o sistema de conexões do ReportMe
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Connection
from tests import (
    BaseAPITestCase, 
    DatabaseTestCase,
    TestConstants, 
    TestDataFactory,
    PermissionTestMixin,
    ValidationTestMixin
)
import json
import tempfile
import os

User = get_user_model()


class ConnectionViewSetTestCase(BaseAPITestCase, PermissionTestMixin, ValidationTestMixin):
    """
    Testes para ConnectionViewSet (CRUD de conexões)
    """
    
    def test_list_connections_authenticated_admin(self):
        """Testa listagem de conexões como admin"""
        self.authenticate_admin()
        
        response = self.client.get(TestConstants.CONNECTIONS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) >= 1)  # Pelo menos a conexão de teste
    
    def test_list_connections_authenticated_readonly(self):
        """Testa listagem de conexões como readonly"""
        self.authenticate_readonly()
        
        response = self.client.get(TestConstants.CONNECTIONS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Readonly só vê conexões próprias
        self.assertIn('results', response.data)
    
    def test_list_connections_unauthenticated(self):
        """Testa listagem sem autenticação"""
        response = self.client.get(TestConstants.CONNECTIONS_URL)
        self.assert_permission_denied(response)
    
    def test_create_sqlite_connection_success(self):
        """Testa criação de conexão SQLite"""
        self.authenticate_admin()
        
        data = {
            'name': 'Nova Conexão SQLite',
            'sgbd': 'sqlite',
            'database': '/tmp/test.db'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Nova Conexão SQLite')
        self.assertEqual(response.data['sgbd'], 'sqlite')
        self.assertEqual(response.data['created_by'], self.admin_user.id)
        
        # Verificar se foi criada no banco
        connection = Connection.objects.get(id=response.data['id'])
        self.assertEqual(connection.name, 'Nova Conexão SQLite')
    
    def test_create_postgresql_connection_success(self):
        """Testa criação de conexão PostgreSQL"""
        self.authenticate_admin()
        
        data = {
            'name': 'Conexão PostgreSQL',
            'sgbd': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sgbd'], 'postgresql')
        self.assertEqual(response.data['host'], 'localhost')
        self.assertEqual(response.data['port'], 5432)
    
    def test_create_mysql_connection_success(self):
        """Testa criação de conexão MySQL"""
        self.authenticate_admin()
        
        data = {
            'name': 'Conexão MySQL',
            'sgbd': 'mysql',
            'host': 'localhost',
            'port': 3306,
            'database': 'testdb',
            'user': 'root',
            'password': 'rootpass'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sgbd'], 'mysql')
        self.assertEqual(response.data['port'], 3306)
    
    def test_create_sqlserver_connection_success(self):
        """Testa criação de conexão SQL Server"""
        self.authenticate_admin()
        
        data = {
            'name': 'Conexão SQL Server',
            'sgbd': 'sqlserver',
            'host': 'localhost',
            'port': 1433,
            'database': 'testdb',
            'user': 'sa',
            'password': 'Passw0rd!'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sgbd'], 'sqlserver')
    
    def test_create_oracle_connection_success(self):
        """Testa criação de conexão Oracle"""
        self.authenticate_admin()
        
        data = {
            'name': 'Conexão Oracle',
            'sgbd': 'oracle',
            'host': 'localhost',
            'port': 1521,
            'database': 'XE',
            'user': 'system',
            'password': 'oracle'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sgbd'], 'oracle')
    
    def test_create_connection_readonly_permission_denied(self):
        """Testa criação de conexão como readonly (deve falhar)"""
        self.authenticate_readonly()
        
        data = {
            'name': 'Conexão Readonly',
            'sgbd': 'sqlite',
            'database': ':memory:'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        self.assert_permission_denied(response)
    
    def test_create_connection_invalid_sgbd(self):
        """Testa criação com tipo de banco inválido"""
        self.authenticate_admin()
        
        data = {
            'name': 'Conexão Inválida',
            'sgbd': 'invalid_db',
            'database': 'test'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        self.assert_validation_error(response, 'sgbd')
    
    def test_create_connection_missing_required_fields(self):
        """Testa criação com campos obrigatórios faltando"""
        self.authenticate_admin()
        
        # PostgreSQL sem host
        data = {
            'name': 'Conexão Incompleta',
            'sgbd': 'postgresql',
            'database': 'testdb'
        }
        
        response = self.client.post(TestConstants.CONNECTIONS_URL, data)
        self.assert_validation_error(response)
    
    def test_retrieve_connection_success(self):
        """Testa recuperação de conexão específica"""
        self.authenticate_admin()
        
        url = f"{TestConstants.CONNECTIONS_URL}{self.test_connection.id}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.test_connection.id)
        self.assertEqual(response.data['name'], self.test_connection.name)
        # Password deve ser omitido na resposta
        self.assertNotIn('password', response.data)
    
    def test_update_connection_success(self):
        """Testa atualização de conexão"""
        self.authenticate_admin()
        
        data = {
            'name': 'Conexão Atualizada',
            'sgbd': 'sqlite',
            'database': ':memory:'
        }
        
        url = f"{TestConstants.CONNECTIONS_URL}{self.test_connection.id}/"
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Conexão Atualizada')
        
        # Verificar se foi atualizado no banco
        self.test_connection.refresh_from_db()
        self.assertEqual(self.test_connection.name, 'Conexão Atualizada')
    
    def test_update_connection_partial(self):
        """Testa atualização parcial de conexão"""
        self.authenticate_admin()
        
        data = {'name': 'Novo Nome'}
        
        url = f"{TestConstants.CONNECTIONS_URL}{self.test_connection.id}/"
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Novo Nome')
        # SGBD deve permanecer o mesmo
        self.assertEqual(response.data['sgbd'], self.test_connection.sgbd)
    
    def test_delete_connection_success(self):
        """Testa exclusão de conexão"""
        # Criar conexão para deletar
        connection_to_delete = TestDataFactory.create_connection(
            self.admin_user,
            name='Conexão para Deletar'
        )
        
        self.authenticate_admin()
        
        url = f"{TestConstants.CONNECTIONS_URL}{connection_to_delete.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar se foi deletado
        with self.assertRaises(Connection.DoesNotExist):
            Connection.objects.get(id=connection_to_delete.id)
    
    def test_delete_connection_permission_denied(self):
        """Testa exclusão por usuário sem permissão"""
        self.authenticate_readonly()
        
        url = f"{TestConstants.CONNECTIONS_URL}{self.test_connection.id}/"
        response = self.client.delete(url)
        
        self.assert_permission_denied(response)
    
    def test_duplicate_connection_action(self):
        """Testa duplicação de conexão"""
        self.authenticate_admin()
        
        data = {'name': 'Conexão Duplicada'}
        
        url = f"{TestConstants.CONNECTIONS_URL}{self.test_connection.id}/duplicate/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Conexão Duplicada')
        self.assertEqual(response.data['sgbd'], self.test_connection.sgbd)
        
        # Verificar se foi criado novo registro
        duplicated_connection = Connection.objects.get(id=response.data['id'])
        self.assertNotEqual(duplicated_connection.id, self.test_connection.id)


class ConnectionTestViewSetTestCase(DatabaseTestCase, BaseAPITestCase):
    """
    Testes para teste de conectividade de conexões
    """
    
    def test_test_sqlite_connection_success(self):
        """Testa conectividade SQLite com sucesso"""
        # Criar arquivo temporário SQLite
        temp_db = tempfile.mktemp(suffix='.db')
        
        try:
            self.authenticate_admin()
            
            data = {
                'sgbd': 'sqlite',
                'database': temp_db
            }
            
            url = f"{TestConstants.CONNECTIONS_URL}test-connection/"
            response = self.client.post(url, data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('success', response.data)
            self.assertTrue(response.data['success'])
            self.assertIn('message', response.data)
            
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)
    
    def test_test_sqlite_connection_invalid_path(self):
        """Testa SQLite com caminho inválido"""
        self.authenticate_admin()
        
        data = {
            'sgbd': 'sqlite',
            'database': '/invalid/path/database.db'
        }
        
        url = f"{TestConstants.CONNECTIONS_URL}test-connection/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
    
    def test_test_postgresql_connection_invalid_host(self):
        """Testa PostgreSQL com host inválido"""
        self.authenticate_admin()
        
        data = {
            'sgbd': 'postgresql',
            'host': 'invalid.host.com',
            'port': 5432,
            'database': 'testdb',
            'user': 'testuser',
            'password': 'testpass'
        }
        
        url = f"{TestConstants.CONNECTIONS_URL}test-connection/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
    
    def test_test_connection_unauthenticated(self):
        """Testa conectividade sem autenticação"""
        data = {
            'sgbd': 'sqlite',
            'database': ':memory:'
        }
        
        url = f"{TestConstants.CONNECTIONS_URL}test-connection/"
        response = self.client.post(url, data)
        
        self.assert_permission_denied(response)
    
    def test_test_connection_invalid_db_type(self):
        """Testa com tipo de banco inválido"""
        self.authenticate_admin()
        
        data = {
            'sgbd': 'invalid_db',
            'database': 'test'
        }
        
        url = f"{TestConstants.CONNECTIONS_URL}test-connection/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_test_connection_missing_required_fields(self):
        """Testa com campos obrigatórios faltando"""
        self.authenticate_admin()
        
        data = {
            'sgbd': 'postgresql'
            # Faltando host, database, etc.
        }
        
        url = f"{TestConstants.CONNECTIONS_URL}test-connection/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ConnectionModelTestCase(TestCase):
    """
    Testes para o modelo Connection
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_sqlite_connection_creation(self):
        """Testa criação de conexão SQLite"""
        connection = Connection.objects.create(
            name='SQLite Teste',
            sgbd='sqlite',
            database='/tmp/test.db',
            created_by=self.user
        )
        
        self.assertEqual(connection.name, 'SQLite Teste')
        self.assertEqual(connection.sgbd, 'sqlite')
        self.assertEqual(connection.database, '/tmp/test.db')
        self.assertEqual(connection.created_by, self.user)
        self.assertIsNotNone(connection.created_at)
    
    def test_postgresql_connection_creation(self):
        """Testa criação de conexão PostgreSQL"""
        connection = Connection.objects.create(
            name='PostgreSQL Teste',
            sgbd='postgresql',
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass',
            created_by=self.user
        )
        
        self.assertEqual(connection.sgbd, 'postgresql')
        self.assertEqual(connection.host, 'localhost')
        self.assertEqual(connection.port, 5432)
        self.assertEqual(connection.user, 'testuser')
    
    def test_connection_string_representation(self):
        """Testa representação string da conexão"""
        connection = Connection.objects.create(
            name='Conexão Teste',
            sgbd='sqlite',
            database=':memory:',
            created_by=self.user
        )
        
        expected = 'Conexão Teste (sqlite)'
        self.assertEqual(str(connection), expected)
    
    def test_get_connection_string_sqlite(self):
        """Testa geração de string de conexão SQLite"""
        connection = Connection.objects.create(
            name='SQLite Teste',
            sgbd='sqlite',
            database='/path/to/database.db',
            created_by=self.user
        )
        
        conn_string = connection.get_connection_string()
        self.assertIn('sqlite', conn_string)
        self.assertIn('/path/to/database.db', conn_string)
    
    def test_get_connection_string_postgresql(self):
        """Testa geração de string de conexão PostgreSQL"""
        connection = Connection.objects.create(
            name='PostgreSQL Teste',
            sgbd='postgresql',
            host='localhost',
            port=5432,
            database='testdb',
            user='testuser',
            password='testpass',
            created_by=self.user
        )
        
        conn_string = connection.get_connection_string()
        self.assertIn('postgresql', conn_string)
        self.assertIn('localhost', conn_string)
        self.assertIn('5432', conn_string)
        self.assertIn('testdb', conn_string)
        self.assertIn('testuser', conn_string)
    
    def test_connection_validation_postgresql_missing_host(self):
        """Testa validação de conexão PostgreSQL"""
        # Este teste seria implementado se houvesse validação no modelo
        # Por enquanto, apenas verificamos se o modelo aceita os campos
        connection = Connection.objects.create(
            name='PostgreSQL Teste',
            sgbd='postgresql',
            database='testdb',
            user='testuser',
            password='testpass',
            created_by=self.user
            # Host não é obrigatório no modelo atual
        )
        self.assertEqual(connection.sgbd, 'postgresql')
    
    def test_connection_ordering(self):
        """Testa ordenação das conexões"""
        connection1 = Connection.objects.create(
            name='B Conexão',
            sgbd='sqlite',
            database=':memory:',
            created_by=self.user
        )
        
        connection2 = Connection.objects.create(
            name='A Conexão',
            sgbd='sqlite',
            database=':memory:',
            created_by=self.user
        )
        
        connections = Connection.objects.all()
        # Deve ser ordenado por nome
        self.assertEqual(connections.first().name, 'A Conexão')
        self.assertEqual(connections.last().name, 'B Conexão')