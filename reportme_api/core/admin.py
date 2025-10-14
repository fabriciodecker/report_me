from django.contrib import admin
from .models import Connection, Parameter, Query, Project, ProjectNode, QueryExecution


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'sgbd', 'host', 'database', 'created_by', 'is_active', 'created_at']
    list_filter = ['sgbd', 'is_active', 'created_at']
    search_fields = ['name', 'host', 'database']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'sgbd', 'database')
        }),
        ('Configuração de Conexão', {
            'fields': ('host', 'port', 'user', 'password')
        }),
        ('Configurações Extras', {
            'fields': ('extra_config', 'is_active')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ParameterInline(admin.TabularInline):
    model = Parameter
    extra = 1
    fields = ['name', 'type', 'allow_null', 'allow_multiple_values', 'default_value']


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'query', 'allow_null', 'allow_multiple_values', 'created_at']
    list_filter = ['type', 'allow_null', 'allow_multiple_values']
    search_fields = ['name', 'query__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('query')


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ['name', 'connection', 'created_by', 'is_active', 'created_at']
    list_filter = ['connection', 'is_active', 'created_at']
    search_fields = ['name', 'query']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ParameterInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'connection')
        }),
        ('Consulta SQL', {
            'fields': ('query',)
        }),
        ('Configurações', {
            'fields': ('timeout', 'cache_duration', 'is_active')
        }),
        ('Auditoria', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class ProjectNodeInline(admin.TabularInline):
    model = ProjectNode
    fk_name = 'parent'
    extra = 1
    fields = ['name', 'query', 'connection', 'order', 'is_active']


@admin.register(ProjectNode)
class ProjectNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'parent', 'query', 'level', 'is_active']
    list_filter = ['project', 'is_active', 'created_at']
    search_fields = ['name', 'project__name']
    readonly_fields = ['created_at', 'updated_at', 'level', 'path']
    inlines = [ProjectNodeInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'project', 'parent', 'order')
        }),
        ('Associações', {
            'fields': ('query', 'connection')
        }),
        ('Metadados', {
            'fields': ('icon', 'description', 'is_active')
        }),
        ('Informações da Árvore', {
            'fields': ('level', 'path'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QueryExecution)
class QueryExecutionAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'status', 'execution_time', 'rows_returned', 'executed_at']
    list_filter = ['status', 'executed_at']
    search_fields = ['query__name', 'user__username']
    readonly_fields = ['executed_at']
    
    fieldsets = (
        ('Execução', {
            'fields': ('query', 'user', 'parameters')
        }),
        ('Resultado', {
            'fields': ('status', 'execution_time', 'rows_returned', 'error_message')
        }),
        ('Data', {
            'fields': ('executed_at',)
        }),
    )
