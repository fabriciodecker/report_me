from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AuditLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin para o modelo User customizado"""
    
    list_display = ['username', 'email', 'name', 'is_admin', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_admin', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Extras', {
            'fields': ('name', 'is_admin', 'preferences')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informações Extras', {
            'fields': ('email', 'name', 'is_admin')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin para visualizar logs de auditoria"""
    
    list_display = ['timestamp', 'user', 'action', 'object_repr', 'ip_address']
    list_filter = ['action', 'timestamp', 'user']
    search_fields = ['user__username', 'object_repr', 'ip_address']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp', 'user', 'action', 'content_type', 'object_id', 'object_repr', 'changes', 'ip_address', 'user_agent']
    
    def has_add_permission(self, request):
        return False  # Não permitir adicionar logs manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Não permitir editar logs
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Só superuser pode deletar logs
