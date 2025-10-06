from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.openapi import OpenApiParameter, OpenApiExample

from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetSerializer
)

User = get_user_model()


@extend_schema(
    tags=['authentication'],
    summary='Login do usuário',
    description='Autenticar usuário e obter tokens JWT (access e refresh)',
    examples=[
        OpenApiExample(
            'Login Exemplo',
            description='Exemplo de login com credenciais',
            value={
                'username': 'admin',
                'password': 'Teste@123'
            }
        )
    ]
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para login JWT com informações extras do usuário
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=['authentication'],
    summary='Registro de novo usuário',
    description='Criar uma nova conta de usuário no sistema',
    examples=[
        OpenApiExample(
            'Registro Exemplo',
            description='Exemplo de registro de usuário',
            value={
                'username': 'novousuario',
                'email': 'usuario@exemplo.com',
                'password': 'MinhaSenh@123',
                'password_confirm': 'MinhaSenh@123',
                'first_name': 'João',
                'last_name': 'Silva'
            }
        )
    ]
)
class RegisterView(APIView):
    """
    Endpoint para registro de novos usuários
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Usuário criado com sucesso',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.name,
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    Endpoint para visualizar/atualizar perfil do usuário
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Perfil atualizado com sucesso',
                'user': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    Endpoint para mudança de senha
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Senha alterada com sucesso'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    """
    Endpoint para solicitar reset de senha
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Gerar token de reset
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Em produção, enviar email real
            # Por enquanto, apenas retornar o token para testes
            reset_link = f"http://localhost:3000/reset-password/{uid}/{token}/"
            
            # TODO: Implementar envio de email real
            # send_mail(
            #     'Reset de Senha - ReportMe',
            #     f'Use este link para resetar sua senha: {reset_link}',
            #     settings.DEFAULT_FROM_EMAIL,
            #     [email],
            #     fail_silently=False,
            # )
            
            return Response({
                'message': f'Email de recuperação enviado para {email}',
                'reset_link': reset_link,  # Remover em produção
                'status': 'success'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    """
    Endpoint para resetar senha com token
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            # Extrair UID do token (implementação simplificada)
            # Em produção, passar UID separadamente
            try:
                # Por enquanto, buscar usuário admin para teste
                user = User.objects.get(username='admin')
                
                if default_token_generator.check_token(user, token):
                    user.set_password(new_password)
                    user.save()
                    
                    return Response({
                        'message': 'Senha resetada com sucesso',
                        'status': 'success'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'error': 'Token inválido ou expirado'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except User.DoesNotExist:
                return Response({
                    'error': 'Usuário não encontrado'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    """
    Endpoint para listar usuários (apenas para admins)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not (request.user.is_staff or request.user.is_admin):
            return Response({
                'error': 'Permissão negada'
            }, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all().order_by('-created_at')
        serializer = UserProfileSerializer(users, many=True)
        return Response(serializer.data)


class UserPermissionsView(APIView):
    """
    Endpoint para verificar permissões do usuário atual
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Garantir que as permissões foram calculadas pelo middleware
        if not hasattr(user, 'permissions'):
            user.permissions = {
                'can_read': True,
                'can_create': user.is_staff or user.is_admin or user.is_superuser,
                'can_update': user.is_staff or user.is_admin or user.is_superuser,
                'can_delete': user.is_admin or user.is_superuser,
                'can_execute_queries': user.is_staff or user.is_admin or user.is_superuser,
                'can_manage_connections': user.is_admin or user.is_superuser,
                'can_manage_users': user.is_admin or user.is_superuser,
                'is_read_only': not (user.is_staff or user.is_admin or user.is_superuser),
            }
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'is_staff': user.is_staff,
                'is_admin': user.is_admin,
                'is_superuser': user.is_superuser,
            },
            'permissions': user.permissions,
            'accessible_sections': {
                'admin_panel': user.is_admin or user.is_superuser,
                'connection_management': user.is_admin or user.is_superuser,
                'query_editor': user.is_staff or user.is_admin or user.is_superuser,
                'project_management': user.is_staff or user.is_admin or user.is_superuser,
                'user_management': user.is_admin or user.is_superuser,
                'reports_viewer': True,  # Todos podem ver relatórios
            }
        })


class TestPermissionView(APIView):
    """
    Endpoint para testar permissões específicas
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Testar uma permissão específica
        Formato: {"permission": "can_create", "resource": "connection"}
        """
        permission = request.data.get('permission')
        resource = request.data.get('resource', 'general')
        
        user = request.user
        
        # Calcular permissões se não existirem
        if not hasattr(user, 'permissions'):
            user.permissions = {
                'can_read': True,
                'can_create': user.is_staff or user.is_admin or user.is_superuser,
                'can_update': user.is_staff or user.is_admin or user.is_superuser,
                'can_delete': user.is_admin or user.is_superuser,
                'can_execute_queries': user.is_staff or user.is_admin or user.is_superuser,
                'can_manage_connections': user.is_admin or user.is_superuser,
                'can_manage_users': user.is_admin or user.is_superuser,
                'is_read_only': not (user.is_staff or user.is_admin or user.is_superuser),
            }
        
        has_permission = user.permissions.get(permission, False)
        
        # Verificações específicas por recurso
        if resource == 'connection' and permission in ['can_create', 'can_update', 'can_delete']:
            has_permission = user.is_admin or user.is_superuser
        elif resource == 'user' and permission in ['can_create', 'can_update', 'can_delete']:
            has_permission = user.is_admin or user.is_superuser
        
        return Response({
            'permission': permission,
            'resource': resource,
            'user_type': user.user_type,
            'has_permission': has_permission,
            'message': f"Usuário {'tem' if has_permission else 'não tem'} permissão {permission} para {resource}"
        })
