from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


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
