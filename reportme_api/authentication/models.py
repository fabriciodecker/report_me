from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import uuid
import secrets
# Importar modelos de auditoria
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class User(AbstractUser):
    """
    Modelo customizado de usuário para o ReportMe
    Baseado nos requisitos: core_user
    """
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    is_admin = models.BooleanField(default=False, help_text="Usuário administrador do sistema")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Campo para armazenar preferências do usuário
    preferences = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'core_user'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.username} ({self.email})"

    @property
    def full_name(self):
        return self.name or f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def user_type(self):
        if self.is_superuser:
            return "Super Administrador"
        elif self.is_admin:
            return "Administrador"
        elif self.is_staff:
            return "Editor"
        else:
            return "Somente Leitura"
    
    # Métodos de permissão
    def can_create_project(self):
        """Verificar se o usuário pode criar projetos"""
        return self.is_superuser or self.is_admin or self.is_staff
    
    def can_edit_project(self, project):
        """Verificar se o usuário pode editar um projeto específico"""
        if self.is_superuser or self.is_admin:
            return True
        if self.is_staff:
            return True  # Managers podem editar todos os projetos
        return project.owner == self  # Users podem editar apenas seus próprios projetos
    
    def can_view_project(self, project):
        """Verificar se o usuário pode visualizar um projeto específico"""
        if self.is_superuser or self.is_admin or self.is_staff:
            return True
        return project.owner == self or self in project.shared_with.all()
    
    def can_delete_project(self, project):
        """Verificar se o usuário pode excluir um projeto específico"""
        if self.is_superuser or self.is_admin:
            return True
        return project.owner == self
    
    # Métodos de permissão para conexões
    def can_create_connection(self):
        """Verificar se o usuário pode criar conexões"""
        return self.is_superuser or self.is_admin or self.is_staff
    
    def can_edit_connection(self, connection):
        """Verificar se o usuário pode editar uma conexão específica"""
        if self.is_superuser or self.is_admin:
            return True
        if self.is_staff:
            return True  # Managers podem editar todas as conexões
        return connection.created_by == self  # Users podem editar apenas suas próprias conexões
    
    def can_view_connection(self, connection):
        """Verificar se o usuário pode visualizar uma conexão específica"""
        if self.is_superuser or self.is_admin or self.is_staff:
            return True
        return connection.created_by == self
    
    def can_delete_connection(self, connection):
        """Verificar se o usuário pode excluir uma conexão específica"""
        if self.is_superuser or self.is_admin:
            return True
        return connection.created_by == self
    
    def can_view_project_or_connection(self, obj):
        """Método genérico para verificar permissão de visualização"""
        if hasattr(obj, 'owner'):
            if obj.__class__.__name__ == 'Project':
                return self.can_view_project(obj)
            elif obj.__class__.__name__ == 'Connection':
                return self.can_view_connection(obj)
        return False


class AuditLog(models.Model):
    """
    Modelo para log de auditoria das ações dos usuários
    """
    ACTION_CHOICES = [
        ('create', 'Criar'),
        ('read', 'Visualizar'),
        ('update', 'Atualizar'),
        ('delete', 'Excluir'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('execute_query', 'Executar Consulta'),
        ('test_connection', 'Testar Conexão'),
        ('export', 'Exportar'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Objeto relacionado (genérico)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalhes da ação
    object_repr = models.TextField(blank=True)
    changes = models.JSONField(default=dict, blank=True)
    
    # Metadados
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_log'
        ordering = ['-timestamp']
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.timestamp}"


class UserSession(models.Model):
    """
    Modelo para controlar sessões ativas dos usuários
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_session'
        ordering = ['-last_activity']
        verbose_name = 'Sessão do Usuário'
        verbose_name_plural = 'Sessões dos Usuários'
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.created_at}"


class PasswordResetToken(models.Model):
    """
    Modelo para tokens de recuperação de senha
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'password_reset_token'
        ordering = ['-created_at']
        verbose_name = 'Token de Recuperação de Senha'
        verbose_name_plural = 'Tokens de Recuperação de Senha'
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            # Token válido por 1 hora
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Verificar se o token ainda é válido"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Marcar token como usado"""
        self.is_used = True
        self.used_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"Token para {self.user.email} - {'Válido' if self.is_valid() else 'Inválido'}"
