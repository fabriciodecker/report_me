from functools import wraps
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response


def require_permission(permission_name):
    """
    Decorator para verificar permissões específicas
    
    Usage:
    @require_permission('can_create')
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Autenticação necessária'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user_permissions = getattr(request.user, 'permissions', {})
            
            if not user_permissions.get(permission_name, False):
                return JsonResponse({
                    'error': 'Permissão insuficiente',
                    'required_permission': permission_name,
                    'user_type': request.user.user_type
                }, status=status.HTTP_403_FORBIDDEN)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func):
    """
    Decorator para views que requerem permissão de administrador
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Autenticação necessária'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (request.user.is_admin or request.user.is_superuser):
            return JsonResponse({
                'error': 'Acesso negado',
                'message': 'Apenas administradores podem acessar este recurso',
                'user_type': request.user.user_type
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(view_func):
    """
    Decorator para views que requerem permissão de staff (editor) ou superior
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Autenticação necessária'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not (request.user.is_staff or request.user.is_admin or request.user.is_superuser):
            return JsonResponse({
                'error': 'Acesso negado',
                'message': 'Permissão de editor ou superior necessária',
                'user_type': request.user.user_type
            }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    return wrapper


def read_only_check(view_func):
    """
    Decorator para verificar se o usuário não é somente leitura em operações de escrita
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Autenticação necessária'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            user_permissions = getattr(request.user, 'permissions', {})
            
            if user_permissions.get('is_read_only', True):
                return JsonResponse({
                    'error': 'Acesso negado',
                    'message': 'Usuários com permissão somente leitura não podem modificar dados',
                    'user_type': request.user.user_type
                }, status=status.HTTP_403_FORBIDDEN)
        
        return view_func(request, *args, **kwargs)
    return wrapper


class PermissionMixin:
    """
    Mixin para adicionar verificações de permissão em ViewSets
    """
    
    def check_permissions(self, request):
        """
        Verificar permissões baseadas no método HTTP
        """
        super().check_permissions(request)
        
        if not hasattr(request.user, 'permissions'):
            return
        
        permissions = request.user.permissions
        
        # Verificar permissões baseadas no método
        if request.method in ['POST'] and not permissions.get('can_create'):
            self.permission_denied(
                request, 
                message="Permissão de criação necessária",
                code='create_permission_required'
            )
        elif request.method in ['PUT', 'PATCH'] and not permissions.get('can_update'):
            self.permission_denied(
                request, 
                message="Permissão de edição necessária",
                code='update_permission_required'
            )
        elif request.method in ['DELETE'] and not permissions.get('can_delete'):
            self.permission_denied(
                request, 
                message="Permissão de exclusão necessária",
                code='delete_permission_required'
            )
    
    def check_object_permissions(self, request, obj):
        """
        Verificar permissões no nível do objeto
        """
        super().check_object_permissions(request, obj)
        
        # Verificar se o usuário é dono do objeto ou admin
        if hasattr(obj, 'created_by'):
            if obj.created_by != request.user and not (
                request.user.is_admin or request.user.is_superuser
            ):
                self.permission_denied(
                    request,
                    message="Você só pode acessar seus próprios objetos",
                    code='object_ownership_required'
                )
