import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


class UserPermissionMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar informações de permissões ao usuário
    e log de ações importantes
    """
    
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Adicionar permissões calculadas ao usuário
            user = request.user
            
            # Definir permissões baseadas no tipo de usuário
            user.permissions = {
                'can_read': True,  # Todos os usuários autenticados podem ler
                'can_create': user.is_staff or user.is_admin or user.is_superuser,
                'can_update': user.is_staff or user.is_admin or user.is_superuser,
                'can_delete': user.is_admin or user.is_superuser,
                'can_execute_queries': user.is_staff or user.is_admin or user.is_superuser,
                'can_manage_connections': user.is_admin or user.is_superuser,
                'can_manage_users': user.is_admin or user.is_superuser,
                'is_read_only': not (user.is_staff or user.is_admin or user.is_superuser),
            }
            
            # Log de ações importantes
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                logger.info(
                    f"User {user.username} ({user.user_type}) accessing {request.method} {request.path}"
                )
        
        return None


class RoleBasedAccessMiddleware(MiddlewareMixin):
    """
    Middleware para controle de acesso baseado em roles
    """
    
    # URLs que requerem permissões específicas
    ADMIN_ONLY_PATHS = [
        '/api/auth/users/',
        '/api/core/connections/',
        '/api/admin/',
    ]
    
    STAFF_ONLY_PATHS = [
        '/api/core/queries/',
        '/api/core/projects/',
        '/api/core/execute-query/',
    ]
    
    def process_request(self, request):
        # Pular para usuários não autenticados (será tratado pelas views)
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        user = request.user
        path = request.path
        
        # Verificar permissões para paths específicos
        if any(path.startswith(admin_path) for admin_path in self.ADMIN_ONLY_PATHS):
            if not (user.is_admin or user.is_superuser):
                return JsonResponse({
                    'error': 'Acesso negado',
                    'message': 'Apenas administradores podem acessar este recurso',
                    'required_permission': 'admin'
                }, status=status.HTTP_403_FORBIDDEN)
        
        elif any(path.startswith(staff_path) for staff_path in self.STAFF_ONLY_PATHS):
            if not (user.is_staff or user.is_admin or user.is_superuser):
                return JsonResponse({
                    'error': 'Acesso negado',
                    'message': 'Permissão de editor ou superior necessária',
                    'required_permission': 'staff'
                }, status=status.HTTP_403_FORBIDDEN)
        
        return None
