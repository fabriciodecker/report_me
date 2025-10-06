from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import json

User = get_user_model()


class Connection(models.Model):
    """
    Modelo para conexões com bancos de dados
    Baseado nos requisitos: core_connection
    """
    SGBD_CHOICES = [
        ('sqlite', 'SQLite'),
        ('postgresql', 'PostgreSQL'),
        ('sqlserver', 'SQL Server'),
        ('oracle', 'Oracle'),
        ('mysql', 'MySQL'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nome da Conexão")
    database = models.CharField(max_length=255, verbose_name="Nome do Banco")
    host = models.CharField(max_length=255, verbose_name="Host", blank=True)
    port = models.IntegerField(verbose_name="Porta", null=True, blank=True)
    user = models.CharField(max_length=255, verbose_name="Usuário", blank=True)
    password = models.CharField(max_length=255, verbose_name="Senha", blank=True)
    sgbd = models.CharField(max_length=20, choices=SGBD_CHOICES, default='sqlite', verbose_name="SGBD")
    
    # Campos de auditoria
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_connections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Configurações extras (JSON)
    extra_config = models.JSONField(default=dict, blank=True, verbose_name="Configurações Extras")

    class Meta:
        db_table = 'core_connection'
        verbose_name = 'Conexão'
        verbose_name_plural = 'Conexões'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sgbd})"

    def get_connection_string(self):
        """Retorna string de conexão baseada no SGBD"""
        if self.sgbd == 'sqlite':
            return f"sqlite:///{self.database}"
        elif self.sgbd == 'postgresql':
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port or 5432}/{self.database}"
        elif self.sgbd == 'mysql':
            return f"mysql://{self.user}:{self.password}@{self.host}:{self.port or 3306}/{self.database}"
        # Adicionar outros SGBDs conforme necessário
        return ""


class Parameter(models.Model):
    """
    Modelo para parâmetros de consultas
    Baseado nos requisitos: core_parameter
    """
    TYPE_CHOICES = [
        ('string', 'Texto'),
        ('number', 'Número'),
        ('date', 'Data'),
        ('datetime', 'Data e Hora'),
        ('boolean', 'Verdadeiro/Falso'),
        ('list', 'Lista'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nome do Parâmetro")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='string', verbose_name="Tipo")
    allow_null = models.BooleanField(default=False, verbose_name="Permite Vazio")
    default_value = models.CharField(max_length=255, blank=True, verbose_name="Valor Padrão")
    allow_multiple_values = models.BooleanField(default=False, verbose_name="Permite Múltiplos Valores")
    
    # Validações
    min_value = models.FloatField(null=True, blank=True, verbose_name="Valor Mínimo")
    max_value = models.FloatField(null=True, blank=True, verbose_name="Valor Máximo")
    regex_pattern = models.CharField(max_length=500, blank=True, verbose_name="Padrão Regex")
    
    # Opções para listas
    options = models.JSONField(default=list, blank=True, verbose_name="Opções (para tipo lista)")
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'core_parameter'
        verbose_name = 'Parâmetro'
        verbose_name_plural = 'Parâmetros'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.type})"


class Query(models.Model):
    """
    Modelo para consultas SQL
    Baseado nos requisitos: core_query
    """
    name = models.CharField(max_length=255, verbose_name="Nome da Consulta")
    query = models.TextField(verbose_name="Consulta SQL")
    connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name='queries', verbose_name="Conexão")
    parameters = models.ManyToManyField(Parameter, through='QueryParameter', blank=True, verbose_name="Parâmetros")
    
    # Configurações da consulta
    timeout = models.IntegerField(default=30, verbose_name="Timeout (segundos)")
    cache_duration = models.IntegerField(default=0, verbose_name="Cache (segundos, 0 = sem cache)")
    
    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_queries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_query'
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.connection.name}"

    def get_parameters_dict(self):
        """Retorna dicionário com os parâmetros da consulta"""
        return {qp.parameter.name: qp.parameter for qp in self.queryparameter_set.all()}


class QueryParameter(models.Model):
    """
    Modelo intermediário para relacionamento Query-Parameter
    Baseado nos requisitos: core_query_parameter
    """
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, verbose_name="Ordem")
    is_required = models.BooleanField(default=True, verbose_name="Obrigatório")

    class Meta:
        db_table = 'core_query_parameter'
        unique_together = ['query', 'parameter']
        ordering = ['order', 'parameter__name']

    def __str__(self):
        return f"{self.query.name} - {self.parameter.name}"


class Project(models.Model):
    """
    Modelo para projetos
    Baseado nos requisitos: core_project
    """
    name = models.CharField(max_length=255, verbose_name="Nome do Projeto")
    description = models.TextField(blank=True, verbose_name="Descrição")
    
    # Referência ao nó raiz da árvore
    first_node = models.OneToOneField('ProjectNode', on_delete=models.CASCADE, null=True, blank=True, related_name='project_root')
    
    # Permissões
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_projects')
    is_public = models.BooleanField(default=False, verbose_name="Público")
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_project'
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Criar nó raiz se for um projeto novo
        if is_new and not self.first_node:
            root_node = ProjectNode.objects.create(
                name=self.name,
                project=self,
                parent=None
            )
            self.first_node = root_node
            self.save(update_fields=['first_node'])


class ProjectNode(models.Model):
    """
    Modelo para nós da árvore hierárquica de projetos
    Baseado nos requisitos: core_project_node
    """
    name = models.CharField(max_length=255, verbose_name="Nome do Nó")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='nodes')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Associações opcionais
    query = models.ForeignKey(Query, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Consulta")
    connection = models.ForeignKey(Connection, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Conexão")
    
    # Ordem na árvore
    order = models.IntegerField(default=0, verbose_name="Ordem")
    
    # Metadados
    icon = models.CharField(max_length=50, blank=True, verbose_name="Ícone")
    description = models.TextField(blank=True, verbose_name="Descrição")
    
    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_project_node'
        verbose_name = 'Nó do Projeto'
        verbose_name_plural = 'Nós do Projeto'
        ordering = ['order', 'name']
        unique_together = ['project', 'parent', 'name']

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    @property
    def level(self):
        """Retorna o nível do nó na árvore"""
        if not self.parent:
            return 0
        return self.parent.level + 1

    @property
    def path(self):
        """Retorna o caminho completo do nó"""
        if not self.parent:
            return [self.name]
        return self.parent.path + [self.name]

    @property
    def has_query(self):
        """Verifica se o nó tem uma consulta associada"""
        return self.query is not None

    @property
    def is_leaf(self):
        """Verifica se é um nó folha (sem filhos)"""
        return not self.children.exists()

    def clean(self):
        """Validações customizadas"""
        # Somente nós folha podem ter consulta associada
        if self.query and not self.is_leaf:
            raise ValidationError("Somente nós folha podem ter consulta associada.")
        
        # Evitar referência circular
        if self.parent:
            current = self.parent
            while current:
                if current == self:
                    raise ValidationError("Referência circular detectada.")
                current = current.parent

    def get_descendants(self):
        """Retorna todos os descendentes do nó"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_descendants_count(self):
        """Retorna o número total de descendentes"""
        return len(self.get_descendants())
    
    def is_descendant_of(self, node):
        """Verifica se este nó é descendente do nó especificado"""
        current = self.parent
        while current:
            if current == node:
                return True
            current = current.parent
        return False


class QueryExecution(models.Model):
    """
    Modelo para histórico de execuções de consultas
    """
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='executions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='query_executions')
    parameters = models.JSONField(default=dict, verbose_name="Parâmetros Utilizados")
    
    # Resultado da execução
    status = models.CharField(max_length=20, choices=[
        ('success', 'Sucesso'),
        ('error', 'Erro'),
        ('timeout', 'Timeout'),
    ], default='success')
    
    execution_time = models.FloatField(null=True, blank=True, verbose_name="Tempo de Execução (segundos)")
    rows_returned = models.IntegerField(null=True, blank=True, verbose_name="Linhas Retornadas")
    error_message = models.TextField(blank=True, verbose_name="Mensagem de Erro")
    
    # Auditoria
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_query_execution'
        verbose_name = 'Execução de Consulta'
        verbose_name_plural = 'Execuções de Consultas'
        ordering = ['-executed_at']

    def __str__(self):
        return f"{self.query.name} - {self.executed_at} ({self.status})"
