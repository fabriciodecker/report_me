"""
Classe base e utilitários para testes do ReportMe
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import PasswordResetToken
from core.models import Project, ProjectNode, Connection, Query, Parameter
import tempfile
import os

User = get_user_model()


class BaseTestCase(TestCase):
    """
    Classe base para testes com fixtures comuns
    """
    
    @classmethod
    def setUpTestData(cls):
        """Configuração de dados para toda a classe de teste"""
        # Usuários de teste
        cls.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='admin123',
            is_admin=True,
            is_staff=True,
            name='Admin Teste'
        )
        
        cls.editor_user = User.objects.create_user(
            username='editor_test',
            email='editor@test.com', 
            password='editor123',
            is_staff=True,
            name='Editor Teste'
        )
        
        cls.readonly_user = User.objects.create_user(
            username='readonly_test',
            email='readonly@test.com',
            password='readonly123',
            name='Readonly Teste'
        )
        
        # Projeto de teste
        cls.test_project = Project.objects.create(
            name='Projeto Teste',
            description='Projeto para testes unitários',
            owner=cls.admin_user
        )
        
        # Nós de projeto de teste
        cls.root_node = ProjectNode.objects.create(
            project=cls.test_project,
            name='Raiz',
            description='Nó raiz de teste',
            parent=None
        )
        
        cls.child_node = ProjectNode.objects.create(
            project=cls.test_project,
            name='Filho',
            description='Nó filho de teste',
            parent=cls.root_node
        )
        
        # Conexão de teste
        cls.test_connection = Connection.objects.create(
            name='SQLite Teste',
            sgbd='sqlite',
            database=':memory:',
            created_by=cls.admin_user
        )
        
        # Consulta de teste
        cls.test_query = Query.objects.create(
            name='Consulta Teste',
            query='SELECT 1 as test_column',
            connection=cls.test_connection,
            created_by=cls.admin_user
        )
    
    def setUp(self):
        """Configuração executada antes de cada teste"""
        super().setUp()
        self.client = APIClient()


class BaseAPITestCase(APITestCase, BaseTestCase):
    """
    Classe base para testes de API com autenticação JWT
    """
    
    def setUp(self):
        super().setUp()
        self.client = APIClient()
        # Autenticar automaticamente como admin
        self.user = self.admin_user  # Alias para compatibilidade
        self.authenticate_admin()
    
    def authenticate_user(self, user):
        """Autentica um usuário e configura o token JWT"""
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        return refresh
    
    def authenticate_admin(self):
        """Autentica como admin"""
        return self.authenticate_user(self.admin_user)
    
    def authenticate_editor(self):
        """Autentica como editor"""
        return self.authenticate_user(self.editor_user)
    
    def authenticate_readonly(self):
        """Autentica como usuário readonly"""
        return self.authenticate_user(self.readonly_user)
    
    def logout(self):
        """Remove autenticação"""
        self.client.credentials()


class DatabaseTestCase(TransactionTestCase):
    """
    Classe base para testes que precisam de transações (conexões reais com BD)
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_db_path = tempfile.mktemp(suffix='.db')
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
    
    def create_sqlite_connection(self, name="SQLite Test"):
        """Cria uma conexão SQLite real para testes"""
        return Connection.objects.create(
            name=name,
            description=f'Conexão {name} para testes',
            db_type='sqlite',
            database=self.test_db_path,
            created_by=self.admin_user if hasattr(self, 'admin_user') else User.objects.first()
        )


# Mixins para funcionalidades específicas
class PermissionTestMixin:
    """
    Mixin para testes de permissões
    """
    
    def assert_permission_denied(self, response):
        """Verifica se a resposta indica permissão negada"""
        self.assertIn(response.status_code, [401, 403])
    
    def assert_permission_granted(self, response):
        """Verifica se a respissão indica permissão concedida"""
        self.assertIn(response.status_code, [200, 201, 204])


class ValidationTestMixin:
    """
    Mixin para testes de validação
    """
    
    def assert_validation_error(self, response, field=None):
        """Verifica se a resposta indica erro de validação"""
        self.assertEqual(response.status_code, 400)
        if field:
            self.assertIn(field, response.data)


# Factories para criar dados de teste
class TestDataFactory:
    """
    Factory para criar dados de teste padronizados
    """
    
    @staticmethod
    def create_user(username_suffix="", **kwargs):
        """Cria um usuário de teste"""
        defaults = {
            'username': f'user_test_{username_suffix}',
            'email': f'user_{username_suffix}@test.com',
            'password': 'test123',
            'name': f'User Test {username_suffix}'
        }
        defaults.update(kwargs)
        
        password = defaults.pop('password')
        user = User(**defaults)
        user.set_password(password)
        user.save()
        return user
    
    @staticmethod
    def create_project(owner, **kwargs):
        """Cria um projeto de teste"""
        defaults = {
            'name': 'Projeto Teste',
            'description': 'Projeto criado pela factory de testes',
            'owner': owner
        }
        defaults.update(kwargs)
        return Project.objects.create(**defaults)
    
    @staticmethod
    def create_connection(created_by, **kwargs):
        """Cria uma conexão de teste"""
        defaults = {
            'name': 'Conexão Teste',
            'sgbd': 'sqlite',
            'database': ':memory:',
            'created_by': created_by
        }
        defaults.update(kwargs)
        return Connection.objects.create(**defaults)
    
    @staticmethod
    def create_query(connection, created_by, **kwargs):
        """Cria uma consulta de teste"""
        defaults = {
            'name': 'Consulta Teste',
            'query': 'SELECT 1 as test',
            'connection': connection,
            'created_by': created_by
        }
        defaults.update(kwargs)
        return Query.objects.create(**defaults)
    
    @staticmethod
    def create_parameter(query, **kwargs):
        """Cria um parâmetro de teste"""
        defaults = {
            'query': query,
            'name': 'test_param',
            'type': 'string',
            'allow_null': True,
            'default_value': ''
        }
        defaults.update(kwargs)
        return Parameter.objects.create(**defaults)
    
    @staticmethod
    def create_project_node(project, parent, **kwargs):
        """Cria um nó de projeto de teste"""
        defaults = {
            'name': 'Nó Teste',
            'project': project,
            'parent': parent,
            'description': 'Nó criado para testes'
        }
        defaults.update(kwargs)
        return ProjectNode.objects.create(**defaults)


# Constantes para testes
class TestConstants:
    """
    Constantes utilizadas nos testes
    """
    
    # URLs da API
    LOGIN_URL = '/api/auth/login/'
    REGISTER_URL = '/api/auth/register/'
    REFRESH_URL = '/api/auth/refresh/'
    PROFILE_URL = '/api/auth/profile/'
    PASSWORD_RESET_REQUEST_URL = '/api/auth/password-reset-request/'
    PASSWORD_RESET_URL = '/api/auth/password-reset/'
    
    PROJECTS_URL = '/api/core/projects/'
    PROJECT_NODES_URL = '/api/core/project-nodes/'
    CONNECTIONS_URL = '/api/core/connections/'
    QUERIES_URL = '/api/core/queries/'
    
    # Dados de teste
    VALID_PASSWORD = 'TestPassword123!'
    INVALID_PASSWORD = '123'
    
    VALID_EMAIL = 'test@example.com'
    INVALID_EMAIL = 'invalid_email'
    
    # SQL queries para testes
    VALID_SELECT_QUERY = 'SELECT 1 as test_column'
    INVALID_INSERT_QUERY = 'INSERT INTO test (id) VALUES (1)'
    QUERY_WITH_PARAMS = 'SELECT * FROM users WHERE id = :user_id AND name LIKE :name_pattern'
    
    # Campos de conexão para testes
    SQLITE_CONNECTION = {
        'name': 'SQLite Teste',
        'sgbd': 'sqlite',
        'database': ':memory:'
    }
    
    POSTGRESQL_CONNECTION = {
        'name': 'PostgreSQL Teste',
        'sgbd': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'testdb',
        'user': 'testuser',
        'password': 'testpass'
    }
    
    # Dados de conexão para testes
    SQLITE_CONNECTION_DATA = {
        'name': 'SQLite Test',
        'sgbd': 'sqlite',
        'database': ':memory:'
    }
    
    POSTGRESQL_CONNECTION_DATA = {
        'name': 'PostgreSQL Test',
        'sgbd': 'postgresql',
        'host': 'localhost',
        'port': 5432,
        'database': 'testdb',
        'user': 'testuser',
        'password': 'testpass'
    }