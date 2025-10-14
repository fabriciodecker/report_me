from rest_framework import serializers
from .models import Project, ProjectNode, Query, Connection, Parameter
from django.contrib.auth import get_user_model

User = get_user_model()


class ProjectNodeSerializer(serializers.ModelSerializer):
    """
    Serializer para nós de projeto (estrutura hierárquica)
    """
    children = serializers.SerializerMethodField()
    query_name = serializers.CharField(source='query.name', read_only=True)
    connection_name = serializers.SerializerMethodField()
    has_query = serializers.SerializerMethodField()
    node_type = serializers.SerializerMethodField()
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)
    query_id = serializers.IntegerField(source='query.id', read_only=True, allow_null=True)
    
    class Meta:
        model = ProjectNode
        fields = [
            'id', 'name', 'parent', 'parent_id', 'query', 'query_id', 'connection',
            'children', 'query_name', 'connection_name', 'has_query',
            'node_type', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_children(self, obj):
        """Retornar filhos do nó"""
        children = obj.children.all().order_by('name')
        return ProjectNodeSerializer(children, many=True, context=self.context).data
    
    def get_connection_name(self, obj):
        """Obter nome da conexão - prioriza conexão direta, senão da query"""
        if obj.connection:
            return obj.connection.name
        elif obj.query and obj.query.connection:
            return obj.query.connection.name
        return "Sem Conexão"
    
    def get_has_query(self, obj):
        """Verificar se o nó tem consulta associada"""
        return obj.query is not None
    
    def get_node_type(self, obj):
        """Determinar tipo do nó"""
        if obj.query:
            return 'query'
        elif obj.children.exists():
            return 'folder'
        else:
            return 'empty'


class ProjectNodeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para criação de nós (sem recursão)
    """
    parent_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    query_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = ProjectNode
        fields = ['id', 'name', 'parent', 'parent_id', 'query', 'query_id', 'connection']
        read_only_fields = ['id']
        extra_kwargs = {
            'parent': {'required': False},
            'query': {'required': False}
        }
    
    def create(self, validated_data):
        """Custom create to handle parent_id and query_id"""
        parent_id = validated_data.pop('parent_id', None)
        query_id = validated_data.pop('query_id', None)
        
        if parent_id:
            try:
                parent = ProjectNode.objects.get(id=parent_id)
                validated_data['parent'] = parent
            except ProjectNode.DoesNotExist:
                raise serializers.ValidationError({"parent_id": "Nó pai não encontrado"})
        
        if query_id:
            try:
                from .models import Query
                query = Query.objects.get(id=query_id)
                validated_data['query'] = query
            except Query.DoesNotExist:
                raise serializers.ValidationError({"query_id": "Query não encontrada"})
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Custom update to handle parent_id and query_id"""
        parent_id = validated_data.pop('parent_id', None)
        query_id = validated_data.pop('query_id', None)
        
        if parent_id is not None:
            if parent_id:
                try:
                    parent = ProjectNode.objects.get(id=parent_id)
                    validated_data['parent'] = parent
                except ProjectNode.DoesNotExist:
                    raise serializers.ValidationError({"parent_id": "Nó pai não encontrado"})
            else:
                validated_data['parent'] = None
        
        if query_id is not None:
            if query_id:
                try:
                    from .models import Query
                    query = Query.objects.get(id=query_id)
                    validated_data['query'] = query
                except Query.DoesNotExist:
                    raise serializers.ValidationError({"query_id": "Query não encontrada"})
            else:
                validated_data['query'] = None
        
        return super().update(instance, validated_data)
    
    def validate(self, attrs):
        """Validações customizadas"""
        parent = attrs.get('parent')
        parent_id = attrs.get('parent_id')
        query = attrs.get('query')
        query_id = attrs.get('query_id')
        
        # Se parent_id foi fornecido, buscar o parent
        if parent_id and not parent:
            try:
                parent = ProjectNode.objects.get(id=parent_id)
                attrs['parent'] = parent
            except ProjectNode.DoesNotExist:
                raise serializers.ValidationError({"parent_id": "Nó pai não encontrado"})
        
        # Se query_id foi fornecido, buscar a query
        if query_id and not query:
            try:
                from .models import Query
                query = Query.objects.get(id=query_id)
                attrs['query'] = query
            except Query.DoesNotExist:
                raise serializers.ValidationError({"query_id": "Query não encontrada"})
        
        # Validar que nós com query não podem ter filhos
        if query and hasattr(self, 'instance') and self.instance:
            # Verificar se o nó já tem filhos
            if self.instance.children.exists():
                raise serializers.ValidationError(
                    "Nós que já possuem filhos não podem ter uma query associada"
                )
        
        return attrs


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer para projetos
    """
    root_node = ProjectNodeSerializer(source='first_node', read_only=True)
    node_count = serializers.SerializerMethodField()
    query_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='owner.full_name', read_only=True)
    first_node_id = serializers.IntegerField(source='first_node.id', read_only=True, allow_null=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'first_node', 'first_node_id', 'root_node', 'node_count',
            'query_count', 'owner', 'created_by_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at', 'first_node']
    
    def get_node_count(self, obj):
        """Contar total de nós no projeto"""
        if obj.first_node:
            return obj.first_node.get_descendants_count() + 1
        return 0
    
    def get_query_count(self, obj):
        """Contar consultas no projeto"""
        if obj.first_node:
            return ProjectNode.objects.filter(
                project=obj,
                query__isnull=False
            ).count()
        return 0
    
    def create(self, validated_data):
        """Criar projeto com nó raiz automaticamente"""
        user = self.context['request'].user
        
        # Criar projeto
        project = Project.objects.create(
            owner=user,
            **validated_data
        )
        
        # Criar nó raiz
        root_node = ProjectNode.objects.create(
            name=project.name,
            project=project,
            parent=None
        )
        
        # Atualizar referência do primeiro nó
        project.first_node = root_node
        project.save()
        
        return project


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de projetos
    """
    node_count = serializers.SerializerMethodField()
    query_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='owner.full_name', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'node_count', 'query_count',
            'created_by_name', 'created_at', 'is_active'
        ]
    
    def get_node_count(self, obj):
        """Contar nós do projeto"""
        return ProjectNode.objects.filter(project=obj).count()
    
    def get_query_count(self, obj):
        """Contar consultas do projeto"""
        return ProjectNode.objects.filter(project=obj, query__isnull=False).count()


class ProjectTreeSerializer(serializers.ModelSerializer):
    """
    Serializer para árvore completa do projeto
    """
    tree = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'tree', 'created_at', 'updated_at']
    
    def get_tree(self, obj):
        """Retornar árvore completa do projeto"""
        if obj.first_node:
            return ProjectNodeSerializer(obj.first_node, context=self.context).data
        return None


class ConnectionSerializer(serializers.ModelSerializer):
    """
    Serializer para conexões de banco de dados
    """
    owner_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    sgbd_display = serializers.CharField(source='get_sgbd_display', read_only=True)
    is_testable = serializers.SerializerMethodField()
    last_test_status = serializers.SerializerMethodField()
    
    class Meta:
        model = Connection
        fields = [
            'id', 'name', 'sgbd', 'sgbd_display', 'host', 'port', 
            'database', 'user', 'password', 'extra_config',
            'created_by', 'owner_name', 'is_active', 'is_testable', 'last_test_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}  # Não expor senha na resposta
        }
    
    def get_is_testable(self, obj):
        """Verificar se a conexão pode ser testada"""
        return obj.host and obj.database and obj.user
    
    def get_last_test_status(self, obj):
        """Status do último teste de conexão"""
        # TODO: Implementar cache do último teste
        return None
    
    def create(self, validated_data):
        """Criar conexão com created_by automaticamente"""
        user = self.context['request'].user
        connection = Connection.objects.create(
            created_by=user,
            **validated_data
        )
        return connection
    
    def validate(self, attrs):
        """Validações customizadas"""
        sgbd = attrs.get('sgbd')
        port = attrs.get('port')
        
        # Validar porta padrão por tipo de banco
        default_ports = {
            'postgresql': 5432,
            'mysql': 3306,
            'sqlserver': 1433,
            'oracle': 1521,
            'sqlite': None
        }
        
        if sgbd in default_ports and not port:
            attrs['port'] = default_ports[sgbd]
        
        return attrs


class ConnectionListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de conexões
    """
    owner_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    sgbd_display = serializers.CharField(source='get_sgbd_display', read_only=True)
    connection_string = serializers.SerializerMethodField()
    
    class Meta:
        model = Connection
        fields = [
            'id', 'name', 'sgbd', 'sgbd_display', 'host', 'port',
            'database', 'user', 'owner_name', 'is_active', 'connection_string',
            'created_at'
        ]
    
    def get_connection_string(self, obj):
        """String de conexão mascarada para exibição"""
        if obj.sgbd == 'sqlite':
            return f"SQLite: {obj.database}"
        else:
            return f"{obj.user}@{obj.host}:{obj.port}/{obj.database}"


class ConnectionTestSerializer(serializers.Serializer):
    """
    Serializer para testar conexão
    """
    connection_id = serializers.IntegerField(required=False)
    
    # Campos para teste de conexão temporária
    sgbd = serializers.ChoiceField(
        choices=Connection.SGBD_CHOICES,
        required=False
    )
    host = serializers.CharField(max_length=255, required=False)
    port = serializers.IntegerField(required=False)
    database = serializers.CharField(max_length=255, required=False)
    user = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(max_length=255, required=False)
    extra_config = serializers.JSONField(required=False, default=dict)
    
    def validate(self, attrs):
        """Validar que temos conexão ID ou dados completos"""
        connection_id = attrs.get('connection_id')
        
        if connection_id:
            # Testar conexão existente
            try:
                connection = Connection.objects.get(id=connection_id)
                # Verificar permissão
                user = self.context['request'].user
                if not user.can_view_connection(connection):
                    raise serializers.ValidationError("Você não tem permissão para testar esta conexão")
            except Connection.DoesNotExist:
                raise serializers.ValidationError("Conexão não encontrada")
        else:
            # Testar conexão temporária - todos os campos obrigatórios
            required_fields = ['sgbd', 'host', 'database', 'user', 'password']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError(f"Campo '{field}' é obrigatório para teste de conexão")
        
        return attrs


# ===== QUERY SERIALIZERS =====

class ParameterSerializer(serializers.ModelSerializer):
    """
    Serializer para parâmetros de consulta
    """
    
    class Meta:
        model = Parameter
        fields = [
            'id', 'name', 'type', 'allow_null', 'default_value', 'allow_multiple_values',
            'min_value', 'max_value', 'regex_pattern', 'options', 'query'
        ]


class QueryListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem de consultas
    """
    connection_name = serializers.CharField(source='connection.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    parameters_count = serializers.SerializerMethodField()
    last_execution = serializers.SerializerMethodField()
    
    class Meta:
        model = Query
        fields = [
            'id', 'name', 'query', 'connection', 'connection_id', 'connection_name', 'created_by_name',
            'parameters_count', 'last_execution', 'timeout', 'cache_duration',
            'created_at', 'updated_at', 'is_active'
        ]
    
    def to_representation(self, instance):
        """Customizar representação para garantir connection_id"""
        data = super().to_representation(instance)
        # Garantir que connection_id esteja presente
        if instance.connection_id:
            data['connection_id'] = instance.connection_id
        return data
    
    def get_parameters_count(self, obj):
        """Contar parâmetros da consulta"""
        return obj.query_parameters.count()
    
    def get_last_execution(self, obj):
        """Última execução da consulta"""
        last_exec = obj.executions.order_by('-executed_at').first()
        if last_exec:
            return {
                'executed_at': last_exec.executed_at,
                'status': last_exec.status,
                'execution_time': last_exec.execution_time
            }
        return None


class QuerySerializer(serializers.ModelSerializer):
    """
    Serializer para consultas
    """
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    connection_name = serializers.CharField(source='connection.name', read_only=True)
    parameters = ParameterSerializer(source='query_parameters', many=True, read_only=True)
    
    class Meta:
        model = Query
        fields = [
            'id', 'name', 'query', 'connection', 'connection_name',
            'created_by', 'created_by_name', 'parameters', 'timeout', 'cache_duration',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']


class QueryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de consulta
    """
    connection_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Query
        fields = [
            'name', 'query', 'connection', 'connection_id', 'timeout', 'cache_duration',
            'is_active'
        ]
        extra_kwargs = {
            'connection': {'required': False},
        }
    
    def create(self, validated_data):
        """Criar consulta, lidando com connection_id"""
        connection_id = validated_data.pop('connection_id', None)
        
        # Se connection_id foi fornecido, buscar a conexão
        if connection_id:
            try:
                connection = Connection.objects.get(id=connection_id)
                validated_data['connection'] = connection
            except Connection.DoesNotExist:
                raise serializers.ValidationError({'connection_id': 'Conexão não encontrada'})
        
        user = self.context['request'].user
        return Query.objects.create(created_by=user, **validated_data)
    
    def update(self, instance, validated_data):
        """Atualizar consulta, lidando com connection_id"""
        print(f"=== DEBUG QueryCreateSerializer.update ===")
        print(f"validated_data: {validated_data}")
        
        connection_id = validated_data.pop('connection_id', None)
        print(f"connection_id extraído: {connection_id}")
        
        # Se connection_id foi fornecido, buscar a conexão
        if connection_id:
            try:
                connection = Connection.objects.get(id=connection_id)
                validated_data['connection'] = connection
                print(f"Conexão encontrada e adicionada: {connection}")
            except Connection.DoesNotExist:
                print(f"ERRO: Conexão {connection_id} não encontrada")
                raise serializers.ValidationError({'connection_id': 'Conexão não encontrada'})
        
        # Atualizar os campos um por um
        for attr, value in validated_data.items():
            print(f"Atualizando {attr} = {value}")
            setattr(instance, attr, value)
        
        instance.save()
        print("=== FIM DEBUG update ===")
        return instance
    
    def validate_query(self, value):
        """Validar consulta SQL básica"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Consulta SQL deve ter pelo menos 10 caracteres")
        
        # Verificações básicas de segurança
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        query_upper = value.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise serializers.ValidationError(
                    f"Consulta contém palavra-chave não permitida: {keyword}. "
                    "Apenas consultas SELECT são permitidas."
                )
        
        if not query_upper.strip().startswith('SELECT'):
            raise serializers.ValidationError("Apenas consultas SELECT são permitidas")
        
        return value
    
    def validate_connection(self, value):
        """Validar se o usuário tem acesso à conexão"""
        user = self.context['request'].user
        if not user.can_view_connection(value):
            raise serializers.ValidationError("Você não tem permissão para usar esta conexão")
        return value
    
    def validate(self, data):
        """Validação geral simplificada"""
        print(f"=== DEBUG QueryCreateSerializer.validate ===")
        print(f"Dados recebidos: {data}")
        
        # Verificar se connection ou connection_id foi fornecido
        connection_id = data.get('connection_id')
        connection = data.get('connection')
        
        print(f"connection_id: {connection_id}, connection: {connection}")
        
        if not connection and not connection_id:
            print("ERRO: Nenhum connection nem connection_id fornecido")
            raise serializers.ValidationError({
                'non_field_errors': ['Campo connection ou connection_id é obrigatório']
            })
        
        # Se connection_id foi fornecido, validar que existe
        if connection_id:
            try:
                connection_obj = Connection.objects.get(id=connection_id)
                print(f"Conexão encontrada: {connection_obj.name}")
                
                # Verificar permissão do usuário
                user = self.context['request'].user
                if not user.can_view_connection(connection_obj):
                    print("ERRO: Usuário não tem permissão para usar esta conexão")
                    raise serializers.ValidationError({
                        'connection_id': ['Você não tem permissão para usar esta conexão']
                    })
                    
            except Connection.DoesNotExist:
                print(f"ERRO: Conexão com ID {connection_id} não encontrada")
                raise serializers.ValidationError({
                    'connection_id': ['Conexão não encontrada']
                })
        
        print("=== FIM DEBUG ===")
        return data


class QueryExecutionSerializer(serializers.Serializer):
    """
    Serializer para execução de consulta
    """
    query_id = serializers.IntegerField()
    parameters = serializers.DictField(required=False, default=dict)
    limit = serializers.IntegerField(required=False, default=100, min_value=1, max_value=10000)
    
    def validate_query_id(self, value):
        """Validar se a consulta existe e o usuário tem acesso"""
        try:
            query = Query.objects.get(id=value)
            user = self.context['request'].user
            if not user.can_view_connection(query.connection):
                raise serializers.ValidationError("Você não tem permissão para executar esta consulta")
            return value
        except Query.DoesNotExist:
            raise serializers.ValidationError("Consulta não encontrada")


class QueryValidationSerializer(serializers.Serializer):
    """
    Serializer para validação de consulta SQL
    """
    query = serializers.CharField()
    connection_id = serializers.IntegerField()
    
    def validate_connection_id(self, value):
        """Validar se a conexão existe e o usuário tem acesso"""
        try:
            connection = Connection.objects.get(id=value)
            user = self.context['request'].user
            if not user.can_view_connection(connection):
                raise serializers.ValidationError("Você não tem permissão para usar esta conexão")
            return value
        except Connection.DoesNotExist:
            raise serializers.ValidationError("Conexão não encontrada")
    
    def validate_query(self, value):
        """Validar consulta SQL"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Consulta SQL deve ter pelo menos 5 caracteres")
        
        # Apenas consultas SELECT
        if not value.strip().upper().startswith('SELECT'):
            raise serializers.ValidationError("Apenas consultas SELECT são permitidas")
        
        return value
