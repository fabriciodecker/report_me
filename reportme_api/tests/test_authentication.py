"""
Testes para o sistema de autenticação do ReportMe
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from authentication.models import PasswordResetToken
from tests import (
    BaseAPITestCase, 
    TestConstants, 
    TestDataFactory,
    PermissionTestMixin,
    ValidationTestMixin
)
import json

User = get_user_model()


class AuthenticationViewsTestCase(BaseAPITestCase, PermissionTestMixin, ValidationTestMixin):
    """
    Testes para views de autenticação (login, registro, etc.)
    """
    
    def test_user_registration_success(self):
        """Testa registro de usuário com dados válidos"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': TestConstants.VALID_PASSWORD,
            'name': 'New User'
        }
        
        response = self.client.post(TestConstants.REGISTER_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verificar se usuário foi criado
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertEqual(user.name, 'New User')
    
    def test_user_registration_invalid_email(self):
        """Testa registro com email inválido"""
        data = {
            'username': 'newuser',
            'email': TestConstants.INVALID_EMAIL,
            'password': TestConstants.VALID_PASSWORD,
            'name': 'New User'
        }
        
        response = self.client.post(TestConstants.REGISTER_URL, data)
        self.assert_validation_error(response, 'email')
    
    def test_user_registration_weak_password(self):
        """Testa registro com senha fraca"""
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': TestConstants.INVALID_PASSWORD,
            'name': 'New User'
        }
        
        response = self.client.post(TestConstants.REGISTER_URL, data)
        self.assert_validation_error(response, 'password')
    
    def test_user_registration_duplicate_username(self):
        """Testa registro com username duplicado"""
        data = {
            'username': self.admin_user.username,
            'email': 'different@test.com',
            'password': TestConstants.VALID_PASSWORD,
            'name': 'Different User'
        }
        
        response = self.client.post(TestConstants.REGISTER_URL, data)
        self.assert_validation_error(response, 'username')
    
    def test_user_login_success(self):
        """Testa login com credenciais válidas"""
        data = {
            'username': self.admin_user.username,
            'password': 'admin123'
        }
        
        response = self.client.post(TestConstants.LOGIN_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        
        # Verificar dados do usuário
        user_data = response.data['user']
        self.assertEqual(user_data['username'], self.admin_user.username)
        self.assertEqual(user_data['email'], self.admin_user.email)
    
    def test_user_login_invalid_credentials(self):
        """Testa login com credenciais inválidas"""
        data = {
            'username': self.admin_user.username,
            'password': 'wrong_password'
        }
        
        response = self.client.post(TestConstants.LOGIN_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_user_login_inactive_user(self):
        """Testa login com usuário inativo"""
        inactive_user = TestDataFactory.create_user('inactive', is_active=False)
        
        data = {
            'username': inactive_user.username,
            'password': 'test123'
        }
        
        response = self.client.post(TestConstants.LOGIN_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh_success(self):
        """Testa renovação de token com refresh token válido"""
        refresh = RefreshToken.for_user(self.admin_user)
        
        data = {'refresh': str(refresh)}
        response = self.client.post(TestConstants.REFRESH_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_refresh_invalid_token(self):
        """Testa renovação com refresh token inválido"""
        data = {'refresh': 'invalid_token'}
        response = self.client.post(TestConstants.REFRESH_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_view_authenticated(self):
        """Testa visualização de perfil com usuário autenticado"""
        self.authenticate_admin()
        
        response = self.client.get(TestConstants.PROFILE_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.admin_user.username)
        self.assertEqual(response.data['email'], self.admin_user.email)
        self.assertIn('user_type', response.data)
    
    def test_profile_view_unauthenticated(self):
        """Testa visualização de perfil sem autenticação"""
        response = self.client.get(TestConstants.PROFILE_URL)
        self.assert_permission_denied(response)
    
    def test_profile_update_success(self):
        """Testa atualização de perfil com dados válidos"""
        self.authenticate_admin()
        
        data = {
            'name': 'Nome Atualizado',
            'email': 'updated@test.com'
        }
        
        response = self.client.put(TestConstants.PROFILE_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se dados foram atualizados
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.name, 'Nome Atualizado')
        self.assertEqual(self.admin_user.email, 'updated@test.com')


class PasswordResetTestCase(BaseAPITestCase):
    """
    Testes para sistema de recuperação de senha
    """
    
    def test_password_reset_request_success(self):
        """Testa solicitação de recuperação de senha com email válido"""
        data = {'email': self.admin_user.email}
        
        response = self.client.post(TestConstants.PASSWORD_RESET_REQUEST_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verificar se token foi criado
        token = PasswordResetToken.objects.filter(user=self.admin_user).first()
        self.assertIsNotNone(token)
        self.assertTrue(token.is_valid())
        
        # Verificar se email foi enviado
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.admin_user.email, mail.outbox[0].to)
    
    def test_password_reset_request_nonexistent_email(self):
        """Testa solicitação com email que não existe"""
        data = {'email': 'nonexistent@test.com'}
        
        response = self.client.post(TestConstants.PASSWORD_RESET_REQUEST_URL, data)
        
        # Por segurança, sempre retorna sucesso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Mas não cria token nem envia email
        self.assertEqual(PasswordResetToken.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_password_reset_request_invalid_email(self):
        """Testa solicitação com email inválido"""
        data = {'email': TestConstants.INVALID_EMAIL}
        
        response = self.client.post(TestConstants.PASSWORD_RESET_REQUEST_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_success(self):
        """Testa redefinição de senha com token válido"""
        # Criar token de recuperação
        reset_token = PasswordResetToken.objects.create(user=self.admin_user)
        
        data = {
            'token': reset_token.token,
            'new_password': 'NewPassword123!'
        }
        
        response = self.client.post(TestConstants.PASSWORD_RESET_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se senha foi alterada
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('NewPassword123!'))
        
        # Verificar se token foi marcado como usado
        reset_token.refresh_from_db()
        self.assertTrue(reset_token.is_used)
    
    def test_password_reset_invalid_token(self):
        """Testa redefinição com token inválido"""
        data = {
            'token': 'invalid_token',
            'new_password': 'NewPassword123!'
        }
        
        response = self.client.post(TestConstants.PASSWORD_RESET_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_expired_token(self):
        """Testa redefinição com token expirado"""
        # Criar token expirado
        from django.utils import timezone
        from datetime import timedelta
        
        reset_token = PasswordResetToken.objects.create(user=self.admin_user)
        reset_token.expires_at = timezone.now() - timedelta(hours=2)
        reset_token.save()
        
        data = {
            'token': reset_token.token,
            'new_password': 'NewPassword123!'
        }
        
        response = self.client.post(TestConstants.PASSWORD_RESET_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_reset_used_token(self):
        """Testa redefinição com token já usado"""
        reset_token = PasswordResetToken.objects.create(user=self.admin_user)
        reset_token.mark_as_used()
        
        data = {
            'token': reset_token.token,
            'new_password': 'NewPassword123!'
        }
        
        response = self.client.post(TestConstants.PASSWORD_RESET_URL, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserPermissionsTestCase(BaseAPITestCase):
    """
    Testes para sistema de permissões de usuários
    """
    
    def test_admin_permissions(self):
        """Testa permissões de usuário admin"""
        user = self.admin_user
        
        # Admin pode criar projetos
        self.assertTrue(user.can_create_project())
        
        # Admin pode editar qualquer projeto
        self.assertTrue(user.can_edit_project(self.test_project))
        
        # Admin pode visualizar qualquer projeto
        self.assertTrue(user.can_view_project(self.test_project))
        
        # Admin pode excluir qualquer projeto
        self.assertTrue(user.can_delete_project(self.test_project))
    
    def test_editor_permissions(self):
        """Testa permissões de usuário editor"""
        user = self.editor_user
        
        # Editor pode criar projetos
        self.assertTrue(user.can_create_project())
        
        # Editor pode editar projetos (é manager)
        self.assertTrue(user.can_edit_project(self.test_project))
        
        # Editor pode visualizar projetos
        self.assertTrue(user.can_view_project(self.test_project))
        
        # Editor não pode excluir projetos de outros
        self.assertFalse(user.can_delete_project(self.test_project))
    
    def test_readonly_permissions(self):
        """Testa permissões de usuário readonly"""
        user = self.readonly_user
        
        # Readonly não pode criar projetos
        self.assertFalse(user.can_create_project())
        
        # Readonly não pode editar projetos de outros
        self.assertFalse(user.can_edit_project(self.test_project))
        
        # Readonly não pode visualizar projetos de outros por padrão
        self.assertFalse(user.can_view_project(self.test_project))
        
        # Readonly não pode excluir projetos
        self.assertFalse(user.can_delete_project(self.test_project))


class UserModelTestCase(TestCase):
    """
    Testes para o modelo User customizado
    """
    
    def test_user_creation(self):
        """Testa criação de usuário"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_admin)
    
    def test_user_full_name_property(self):
        """Testa propriedade full_name"""
        # Com nome
        user1 = User(name='Test User')
        self.assertEqual(user1.full_name, 'Test User')
        
        # Com first_name e last_name
        user2 = User(first_name='John', last_name='Doe')
        self.assertEqual(user2.full_name, 'John Doe')
        
        # Apenas com username
        user3 = User(username='testuser')
        self.assertEqual(user3.full_name, 'testuser')
    
    def test_user_type_property(self):
        """Testa propriedade user_type"""
        # Super admin
        user1 = User(is_superuser=True)
        self.assertEqual(user1.user_type, 'Super Administrador')
        
        # Admin
        user2 = User(is_admin=True)
        self.assertEqual(user2.user_type, 'Administrador')
        
        # Editor/Staff
        user3 = User(is_staff=True)
        self.assertEqual(user3.user_type, 'Editor')
        
        # Readonly
        user4 = User()
        self.assertEqual(user4.user_type, 'Somente Leitura')
    
    def test_user_string_representation(self):
        """Testa representação string do usuário"""
        user = User(username='testuser', email='test@example.com')
        expected = 'testuser (test@example.com)'
        self.assertEqual(str(user), expected)


class PasswordResetTokenModelTestCase(TestCase):
    """
    Testes para o modelo PasswordResetToken
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_token_creation(self):
        """Testa criação de token"""
        token = PasswordResetToken.objects.create(user=self.user)
        
        self.assertIsNotNone(token.token)
        self.assertIsNotNone(token.expires_at)
        self.assertFalse(token.is_used)
        self.assertIsNone(token.used_at)
    
    def test_token_validity(self):
        """Testa validação de token"""
        token = PasswordResetToken.objects.create(user=self.user)
        
        # Token recém criado deve ser válido
        self.assertTrue(token.is_valid())
        
        # Token usado não deve ser válido
        token.mark_as_used()
        self.assertFalse(token.is_valid())
    
    def test_token_expiration(self):
        """Testa expiração de token"""
        from django.utils import timezone
        from datetime import timedelta
        
        token = PasswordResetToken.objects.create(user=self.user)
        
        # Simular expiração
        token.expires_at = timezone.now() - timedelta(minutes=1)
        token.save()
        
        self.assertFalse(token.is_valid())
    
    def test_mark_as_used(self):
        """Testa marcação de token como usado"""
        token = PasswordResetToken.objects.create(user=self.user)
        
        self.assertFalse(token.is_used)
        self.assertIsNone(token.used_at)
        
        token.mark_as_used()
        
        self.assertTrue(token.is_used)
        self.assertIsNotNone(token.used_at)