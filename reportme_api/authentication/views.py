from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
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


@extend_schema(
    tags=['authentication'],
    summary='Solicitar recuperação de senha',
    description='Enviar email com token para recuperação de senha',
    examples=[
        OpenApiExample(
            'Solicitação de recuperação',
            description='Exemplo de solicitação de recuperação de senha',
            value={
                'email': 'usuario@exemplo.com'
            }
        )
    ]
)
class PasswordResetRequestView(APIView):
    """
    Solicitar recuperação de senha via email
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Invalidar tokens anteriores não utilizados
                from .models import PasswordResetToken
                PasswordResetToken.objects.filter(
                    user=user, 
                    is_used=False
                ).update(is_used=True)
                
                # Criar novo token
                reset_token = PasswordResetToken.objects.create(user=user)
                
                # Preparar dados para o email
                reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
                
                # Template de email melhorado
                subject = 'Recuperação de Senha - ReportMe'
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                        <h1 style="color: #1976d2; margin: 0;">ReportMe</h1>
                    </div>
                    
                    <div style="padding: 30px; background-color: white;">
                        <h2 style="color: #333;">Recuperação de Senha</h2>
                        
                        <p>Olá <strong>{user.full_name}</strong>,</p>
                        
                        <p>Você solicitou a recuperação de senha para sua conta no ReportMe.</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" 
                               style="background-color: #1976d2; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Redefinir Senha
                            </a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px;">
                            Este link é válido por <strong>1 hora</strong>.
                        </p>
                        
                        <p style="color: #666; font-size: 14px;">
                            Se você não solicitou esta recuperação, ignore este email.
                            Sua senha permanecerá inalterada.
                        </p>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Se o botão não funcionar, copie e cole este link no seu navegador:<br>
                            <span style="word-break: break-all;">{reset_url}</span>
                        </p>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                        <p style="color: #666; font-size: 12px; margin: 0;">
                            Atenciosamente,<br>
                            Equipe ReportMe
                        </p>
                    </div>
                </body>
                </html>
                """
                
                # Versão texto simples como fallback
                text_message = f"""
Olá {user.full_name},

Você solicitou a recuperação de senha para sua conta no ReportMe.

Para redefinir sua senha, acesse o link abaixo:
{reset_url}

Este link é válido por 1 hora.

Se você não solicitou esta recuperação, ignore este email.

Atenciosamente,
Equipe ReportMe
                """
                
                try:
                    from django.core.mail import EmailMultiAlternatives
                    
                    # Criar email com versão HTML e texto
                    email_msg = EmailMultiAlternatives(
                        subject=subject,
                        body=text_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[user.email]
                    )
                    email_msg.attach_alternative(html_message, "text/html")
                    email_msg.send(fail_silently=False)
                    
                    return Response({
                        'message': 'Email de recuperação enviado com sucesso',
                        'email': email
                    }, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    # Log do erro para debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Erro ao enviar email de recuperação: {e}")
                    
                    return Response({
                        'error': 'Erro interno do servidor ao enviar email'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except User.DoesNotExist:
                # Por segurança, retornar sucesso mesmo se o usuário não existir
                pass
        
        # Sempre retornar sucesso por segurança (não revelar se email existe)
        return Response({
            'message': 'Se o email existir no sistema, uma mensagem de recuperação será enviada',
            'email': serializer.validated_data.get('email', '') if serializer.is_valid() else ''
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['authentication'],
    summary='Redefinir senha',
    description='Redefinir senha usando token de recuperação',
    examples=[
        OpenApiExample(
            'Redefinição de senha',
            description='Exemplo de redefinição de senha',
            value={
                'token': 'abcd1234efgh5678ijkl9012mnop3456',
                'new_password': 'MinhaNovaSenh@123'
            }
        )
    ]
)
class PasswordResetView(APIView):
    """
    Redefinir senha usando token de recuperação
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            try:
                from .models import PasswordResetToken
                reset_token = PasswordResetToken.objects.get(token=token)
                
                if not reset_token.is_valid():
                    return Response({
                        'error': 'Token inválido ou expirado'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Redefinir senha
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                
                # Marcar token como usado
                reset_token.mark_as_used()
                
                return Response({
                    'message': 'Senha redefinida com sucesso'
                }, status=status.HTTP_200_OK)
                
            except PasswordResetToken.DoesNotExist:
                return Response({
                    'error': 'Token inválido'
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erro ao redefinir senha: {str(e)}")
                
                return Response({
                    'error': 'Erro interno do servidor'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
