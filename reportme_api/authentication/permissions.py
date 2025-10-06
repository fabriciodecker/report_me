from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite apenas leitura para usuários normais
    e acesso completo para administradores
    """
    
    def has_permission(self, request, view):
        # Permitir leitura para usuários autenticados
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Permitir escrita apenas para administradores
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_admin
        )


class IsAdminUser(permissions.BasePermission):
    """
    Permissão que permite acesso apenas para administradores
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_admin
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permissão que permite acesso ao dono do objeto ou administradores
    """
    
    def has_object_permission(self, request, view, obj):
        # Verificar se o objeto tem um campo 'created_by' ou 'user'
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user or request.user.is_staff or request.user.is_admin
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff or request.user.is_admin
        
        # Se não tem owner, permitir apenas para admins
        return request.user.is_staff or request.user.is_admin


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permissão que permite leitura para todos e escrita apenas para o dono
    """
    
    def has_object_permission(self, request, view, obj):
        # Permitir leitura para todos
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permitir escrita apenas para o dono ou admin
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user or request.user.is_staff or request.user.is_admin
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff or request.user.is_admin
        
        return request.user.is_staff or request.user.is_admin


class CanExecuteQueries(permissions.BasePermission):
    """
    Permissão para executar consultas
    Usuários precisam ter pelo menos permissão de staff ou ser admin
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_staff or request.user.is_admin
        )
