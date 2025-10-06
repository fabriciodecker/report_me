from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction, connection
from django.db import models
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
import json

from .models import Project, ProjectNode, Query, Connection, QueryParameter, Parameter, QueryExecution
from .serializers import (
    ProjectSerializer, ProjectListSerializer, ProjectTreeSerializer,
    ProjectNodeSerializer, ProjectNodeCreateSerializer,
    ConnectionSerializer, ConnectionListSerializer, ConnectionTestSerializer,
    QuerySerializer, QueryListSerializer, QueryCreateSerializer,
    QueryExecutionSerializer, QueryValidationSerializer
)
from authentication.decorators import require_permission
from authentication.audit import log_user_action


@extend_schema(
    tags=['system'],
    summary='Health Check',
    description='Verificar se a API está funcionando corretamente'
)
class HealthCheckView(APIView):
    """
    Endpoint de health check para verificar se a API está funcionando
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'message': 'ReportMe API is running',
            'version': '1.0.0',
            'timestamp': '2024-09-28'
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=['projects'],
        summary='Listar projetos',
        description='Listar todos os projetos do usuário com paginação e filtros'
    ),
    create=extend_schema(
        tags=['projects'],
        summary='Criar projeto',
        description='Criar um novo projeto',
        examples=[
            OpenApiExample(
                'Projeto Exemplo',
                value={
                    'name': 'Meu Projeto de Relatórios',
                    'description': 'Projeto para relatórios financeiros'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['projects'],
        summary='Obter projeto',
        description='Obter detalhes de um projeto específico'
    ),
    update=extend_schema(
        tags=['projects'],
        summary='Atualizar projeto',
        description='Atualizar informações de um projeto'
    ),
    partial_update=extend_schema(
        tags=['projects'],
        summary='Atualizar projeto parcialmente',
        description='Atualizar campos específicos de um projeto'
    ),
    destroy=extend_schema(
        tags=['projects'],
        summary='Excluir projeto',
        description='Excluir um projeto e toda sua estrutura'
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de projetos
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar projetos baseado nas permissões do usuário"""
        user = self.request.user
        
        if user.is_superuser or user.is_admin:
            return Project.objects.all()
        elif user.is_staff:
            # Managers podem ver todos os projetos
            return Project.objects.all()
        else:
            # Users podem ver apenas seus próprios projetos
            return Project.objects.filter(owner=user)
    
    def get_serializer_class(self):
        """Escolher serializer baseado na action"""
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'tree':
            return ProjectTreeSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        """Criar projeto e logar ação"""
        if not self.request.user.can_create_project():
            self.permission_denied(
                self.request,
                message="Você não tem permissão para criar projetos"
            )
        
        project = serializer.save()
        log_user_action(
            user=self.request.user,
            action='create_project',
            details=f"Criado projeto: {project.name}"
        )
    
    def perform_update(self, serializer):
        """Atualizar projeto e logar ação"""
        project = self.get_object()
        if not self.request.user.can_edit_project(project):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para editar este projeto"
            )
        
        old_name = project.name
        project = serializer.save()
        log_user_action(
            user=self.request.user,
            action='update_project',
            details=f"Atualizado projeto: {old_name} -> {project.name}"
        )
    
    def perform_destroy(self, instance):
        """Excluir projeto e logar ação"""
        if not self.request.user.can_edit_project(instance):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para excluir este projeto"
            )
        
        project_name = instance.name
        instance.delete()
        log_user_action(
            user=self.request.user,
            action='delete_project',
            details=f"Excluído projeto: {project_name}"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Verificar permissão de visualização"""
        instance = self.get_object()
        if not request.user.can_view_project(instance):
            self.permission_denied(
                request,
                message="Você não tem permissão para visualizar este projeto"
            )
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Endpoint para obter árvore completa do projeto"""
        project = self.get_object()
        
        if not request.user.can_view_project(project):
            return Response(
                {"error": "Você não tem permissão para visualizar este projeto"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ProjectTreeSerializer(project, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicar projeto"""
        original_project = self.get_object()
        
        if not request.user.can_view_project(original_project):
            return Response(
                {"error": "Você não tem permissão para duplicar este projeto"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not request.user.can_create_project():
            return Response(
                {"error": "Você não tem permissão para criar projetos"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_name = request.data.get('name', f"{original_project.name} (Cópia)")
        
        with transaction.atomic():
            # Duplicar projeto
            new_project = Project.objects.create(
                name=new_name,
                owner=request.user,
                is_active=True
            )
            
            # Duplicar estrutura de nós
            if original_project.first_node:
                self._duplicate_node_tree(original_project.first_node, new_project, None)
            
            log_user_action(
                user=request.user,
                action='duplicate_project',
                details=f"Duplicado projeto: {original_project.name} -> {new_name}"
            )
        
        serializer = ProjectSerializer(new_project, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _duplicate_node_tree(self, original_node, new_project, new_parent):
        """Duplicar recursivamente a árvore de nós"""
        new_node = ProjectNode.objects.create(
            name=original_node.name,
            project=new_project,
            parent=new_parent,
            query=original_node.query,
            connection=original_node.connection
        )
        
        # Se é o primeiro nó, atualizar referência no projeto
        if new_parent is None:
            new_project.first_node = new_node
            new_project.save()
        
        # Duplicar filhos recursivamente
        for child in original_node.children.all():
            self._duplicate_node_tree(child, new_project, new_node)
        
        return new_node


class ProjectNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de nós de projeto
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filtrar nós baseado nas permissões do usuário"""
        user = self.request.user
        
        if user.is_superuser or user.is_admin:
            return ProjectNode.objects.all()
        elif user.is_staff:
            return ProjectNode.objects.all()
        else:
            # Users podem ver apenas nós de seus próprios projetos
            return ProjectNode.objects.filter(project__owner=user)
    
    def get_serializer_class(self):
        """Escolher serializer baseado na action"""
        if self.action in ['create', 'update', 'partial_update']:
            return ProjectNodeCreateSerializer
        return ProjectNodeSerializer
    
    def perform_create(self, serializer):
        """Criar nó e validar permissões"""
        # Validar permissões baseado no projeto
        parent = serializer.validated_data.get('parent')
        project = None
        
        if parent:
            project = parent.project
        else:
            # Se não tem parent, precisa especificar o projeto
            project_id = self.request.data.get('project_id')
            if not project_id:
                return Response(
                    {"error": "Projeto deve ser especificado"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            project = get_object_or_404(Project, id=project_id)
        
        if not self.request.user.can_edit_project(project):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para editar este projeto"
            )
        
        node = serializer.save(project=project)
        log_user_action(
            user=self.request.user,
            action='create_node',
            details=f"Criado nó: {node.name} no projeto {project.name}"
        )
    
    def perform_update(self, serializer):
        """Atualizar nó e validar permissões"""
        node = self.get_object()
        
        if not self.request.user.can_edit_project(node.project):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para editar este projeto"
            )
        
        old_name = node.name
        node = serializer.save()
        log_user_action(
            user=self.request.user,
            action='update_node',
            details=f"Atualizado nó: {old_name} -> {node.name}"
        )
    
    def perform_destroy(self, instance):
        """Excluir nó e validar permissões"""
        if not self.request.user.can_edit_project(instance.project):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para editar este projeto"
            )
        
        # Verificar se não é o nó raiz
        if instance.parent is None and instance.project.first_node == instance:
            return Response(
                {"error": "Não é possível excluir o nó raiz do projeto"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mover filhos para o pai
        if instance.children.exists():
            for child in instance.children.all():
                child.parent = instance.parent
                child.save()
        
        node_name = instance.name
        project_name = instance.project.name
        instance.delete()
        
        log_user_action(
            user=self.request.user,
            action='delete_node',
            details=f"Excluído nó: {node_name} do projeto {project_name}"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Verificar permissão de visualização"""
        instance = self.get_object()
        if not request.user.can_view_project(instance.project):
            self.permission_denied(
                request,
                message="Você não tem permissão para visualizar este projeto"
            )
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Mover nó para outro local na árvore"""
        node = self.get_object()
        
        if not request.user.can_edit_project(node.project):
            return Response(
                {"error": "Você não tem permissão para editar este projeto"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_parent_id = request.data.get('new_parent_id')
        
        # Validações
        if new_parent_id:
            new_parent = get_object_or_404(ProjectNode, id=new_parent_id)
            
            # Não pode mover para si mesmo ou seus descendentes
            if new_parent == node or new_parent.is_descendant_of(node):
                return Response(
                    {"error": "Não é possível mover nó para si mesmo ou seus descendentes"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Deve ser do mesmo projeto
            if new_parent.project != node.project:
                return Response(
                    {"error": "Nó deve permanecer no mesmo projeto"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Se o novo pai tem query, não pode ter filhos
            if new_parent.query:
                return Response(
                    {"error": "Nós com consulta não podem ter filhos"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            new_parent = None
            
            # Não pode mover nó raiz
            if node.project.first_node == node:
                return Response(
                    {"error": "Não é possível mover o nó raiz"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        old_parent = node.parent
        node.parent = new_parent
        node.save()
        
        log_user_action(
            user=request.user,
            action='move_node',
            details=f"Movido nó: {node.name} de {old_parent.name if old_parent else 'raiz'} para {new_parent.name if new_parent else 'raiz'}"
        )
        
        serializer = ProjectNodeSerializer(node, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicar nó e sua subárvore"""
        original_node = self.get_object()
        
        if not request.user.can_edit_project(original_node.project):
            return Response(
                {"error": "Você não tem permissão para editar este projeto"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_name = request.data.get('name', f"{original_node.name} (Cópia)")
        parent_id = request.data.get('parent_id', original_node.parent.id if original_node.parent else None)
        
        parent = None
        if parent_id:
            parent = get_object_or_404(ProjectNode, id=parent_id)
            if parent.project != original_node.project:
                return Response(
                    {"error": "Parent deve ser do mesmo projeto"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        with transaction.atomic():
            new_node = self._duplicate_node_subtree(original_node, new_name, parent)
            
            log_user_action(
                user=request.user,
                action='duplicate_node',
                details=f"Duplicado nó: {original_node.name} -> {new_name}"
            )
        
        serializer = ProjectNodeSerializer(new_node, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _duplicate_node_subtree(self, original_node, new_name, new_parent):
        """Duplicar recursivamente subárvore do nó"""
        new_node = ProjectNode.objects.create(
            name=new_name,
            project=original_node.project,
            parent=new_parent,
            query=original_node.query,
            connection=original_node.connection
        )
        
        # Duplicar filhos recursivamente
        for child in original_node.children.all():
            self._duplicate_node_subtree(child, child.name, new_node)
        
        return new_node


class TestConnectionView(APIView):
    """
    Endpoint para testar conexão com banco de dados
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # TODO: Implementar teste de conexão com diferentes SGBDs
        connection_data = request.data
        
        return Response({
            'message': 'Teste de conexão - a ser implementado',
            'connection_data': connection_data,
            'status': 'success'
        }, status=status.HTTP_200_OK)


class ExecuteQueryView(APIView):
    """
    Endpoint para executar consultas SQL
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # TODO: Implementar execução de consultas
        query_data = request.data
        
        return Response({
            'message': 'Execução de consulta - a ser implementado',
            'query': query_data.get('query', ''),
            'parameters': query_data.get('parameters', {}),
            'results': [],
            'total_records': 0
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=['connections'],
        summary='Listar conexões',
        description='Listar todas as conexões de banco de dados do usuário'
    ),
    create=extend_schema(
        tags=['connections'],
        summary='Criar conexão',
        description='Criar uma nova conexão com banco de dados',
        examples=[
            OpenApiExample(
                'Conexão PostgreSQL',
                value={
                    'name': 'BD Produção',
                    'sgbd': 'postgresql',
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'reportme_prod',
                    'user': 'user_db',
                    'password': 'senha123'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['connections'],
        summary='Obter conexão',
        description='Obter detalhes de uma conexão específica'
    ),
    update=extend_schema(
        tags=['connections'],
        summary='Atualizar conexão',
        description='Atualizar informações de uma conexão'
    ),
    destroy=extend_schema(
        tags=['connections'],
        summary='Excluir conexão',
        description='Excluir uma conexão de banco de dados'
    ),
)
class ConnectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de conexões de banco de dados
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'host', 'database']
    ordering_fields = ['name', 'sgbd', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar conexões baseado nas permissões do usuário"""
        user = self.request.user
        
        if user.is_superuser or user.is_admin:
            return Connection.objects.all()
        elif user.is_staff:
            # Managers podem ver todas as conexões
            return Connection.objects.all()
        else:
            # Users podem ver apenas suas próprias conexões
            return Connection.objects.filter(created_by=user)
    
    def get_serializer_class(self):
        """Escolher serializer baseado na action"""
        if self.action == 'list':
            return ConnectionListSerializer
        elif self.action == 'test_connection':
            return ConnectionTestSerializer
        return ConnectionSerializer
    
    def perform_create(self, serializer):
        """Criar conexão e logar ação"""
        if not self.request.user.can_create_connection():
            self.permission_denied(
                self.request,
                message="Você não tem permissão para criar conexões"
            )
        
        connection = serializer.save()
        log_user_action(
            user=self.request.user,
            action='create_connection',
            details=f"Criada conexão: {connection.name}"
        )
    
    def perform_update(self, serializer):
        """Atualizar conexão e logar ação"""
        connection = self.get_object()
        if not self.request.user.can_edit_connection(connection):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para editar esta conexão"
            )
        
        old_name = connection.name
        connection = serializer.save()
        log_user_action(
            user=self.request.user,
            action='update_connection',
            details=f"Atualizada conexão: {old_name} -> {connection.name}"
        )
    
    def perform_destroy(self, instance):
        """Excluir conexão e logar ação"""
        if not self.request.user.can_edit_connection(instance):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para excluir esta conexão"
            )
        
        # Verificar se a conexão está sendo usada por alguma consulta
        if instance.queries.exists():
            return Response(
                {"error": "Não é possível excluir conexão que está sendo usada por consultas"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        connection_name = instance.name
        instance.delete()
        
        log_user_action(
            user=self.request.user,
            action='delete_connection',
            details=f"Excluída conexão: {connection_name}"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Verificar permissão de visualização"""
        instance = self.get_object()
        if not request.user.can_view_connection(instance):
            self.permission_denied(
                request,
                message="Você não tem permissão para visualizar esta conexão"
            )
        
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        tags=['connections'],
        summary='Testar conexão',
        description='Testar conectividade com banco de dados (conexão existente ou temporária)',
        examples=[
            OpenApiExample(
                'Teste conexão existente',
                description='Testar uma conexão já cadastrada',
                value={'connection_id': 1}
            ),
            OpenApiExample(
                'Teste conexão temporária',
                description='Testar uma nova conexão sem salvar',
                value={
                    'database_type': 'postgresql',
                    'host': 'localhost',
                    'port': 5432,
                    'database_name': 'test_db',
                    'username': 'user',
                    'password': 'password'
                }
            )
        ]
    )
    @action(detail=False, methods=['post'], url_path='test-connection')
    def test_connection(self, request):
        """Endpoint para testar conexão de banco de dados"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        connection_id = validated_data.get('connection_id')
        
        try:
            if connection_id:
                # Testar conexão existente
                connection = get_object_or_404(Connection, id=connection_id)
                test_result = self._test_database_connection(connection)
            else:
                # Testar conexão temporária
                test_result = self._test_temporary_connection(validated_data)
            
            # Log da ação
            details = f"Teste de conexão - Sucesso: {test_result['success']}"
            if connection_id:
                details += f" - Conexão: {connection.name}"
            
            log_user_action(
                user=request.user,
                action='test_connection',
                details=details
            )
            
            return Response(test_result)
            
        except Exception as e:
            error_result = {
                'success': False,
                'message': f'Erro ao testar conexão: {str(e)}',
                'error_type': type(e).__name__,
                'timestamp': timezone.now().isoformat()
            }
            
            log_user_action(
                user=request.user,
                action='test_connection_failed',
                details=f"Teste de conexão falhou: {str(e)}"
            )
            
            return Response(error_result, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicar conexão"""
        original_connection = self.get_object()
        
        if not request.user.can_view_connection(original_connection):
            return Response(
                {"error": "Você não tem permissão para duplicar esta conexão"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not request.user.can_create_connection():
            return Response(
                {"error": "Você não tem permissão para criar conexões"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_name = request.data.get('name', f"{original_connection.name} (Cópia)")
        
        # Duplicar conexão
        new_connection = Connection.objects.create(
            name=new_name,
            sgbd=original_connection.sgbd,
            host=original_connection.host,
            port=original_connection.port,
            database=original_connection.database,
            user=original_connection.user,
            password=original_connection.password,
            extra_config=original_connection.extra_config,
            created_by=request.user,
            is_active=True
        )
        
        log_user_action(
            user=request.user,
            action='duplicate_connection',
            details=f"Duplicada conexão: {original_connection.name} -> {new_name}"
        )
        
        serializer = ConnectionSerializer(new_connection, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _test_database_connection(self, connection):
        """Testar conexão com banco de dados existente"""
        return self._test_connection_params(
            sgbd=connection.sgbd,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            user=connection.user,
            password=connection.password,
            extra_config=connection.extra_config or {}
        )
    
    def _test_temporary_connection(self, params):
        """Testar conexão temporária"""
        return self._test_connection_params(
            sgbd=params['sgbd'],
            host=params['host'],
            port=params.get('port'),
            database=params['database'],
            user=params['user'],
            password=params['password'],
            extra_config=params.get('extra_config', {})
        )
    
    def _test_connection_params(self, sgbd, host, port, database, user, password, extra_config):
        """Testar conexão com parâmetros específicos"""
        import time
        
        start_time = time.time()
        
        try:
            if sgbd == 'postgresql':
                result = self._test_postgresql(host, port, database, user, password, extra_config)
            elif sgbd == 'mysql':
                result = self._test_mysql(host, port, database, user, password, extra_config)
            elif sgbd == 'sqlserver':
                result = self._test_sqlserver(host, port, database, user, password, extra_config)
            elif sgbd == 'oracle':
                result = self._test_oracle(host, port, database, user, password, extra_config)
            elif sgbd == 'sqlite':
                result = self._test_sqlite(database)
            else:
                raise ValueError(f"Tipo de banco de dados não suportado: {sgbd}")
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # em ms
            
            return {
                'success': True,
                'message': 'Conexão estabelecida com sucesso',
                'sgbd': sgbd,
                'response_time_ms': response_time,
                'server_info': result.get('server_info', ''),
                'timestamp': timezone.now().isoformat()
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            return {
                'success': False,
                'message': str(e),
                'sgbd': sgbd,
                'response_time_ms': response_time,
                'timestamp': timezone.now().isoformat()
            }
    
    def _test_postgresql(self, host, port, database, user, password, extra_config):
        """Testar conexão PostgreSQL"""
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=host,
                port=port or 5432,
                database=database,
                user=user,
                password=password,
                connect_timeout=10,
                **extra_config
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {'server_info': version}
            
        except ImportError:
            raise Exception("Driver PostgreSQL (psycopg2) não está instalado")
        except Exception as e:
            raise Exception(f"Erro PostgreSQL: {str(e)}")
    
    def _test_mysql(self, host, port, database, user, password, extra_config):
        """Testar conexão MySQL"""
        try:
            # Tentar pymysql primeiro
            try:
                import pymysql
                conn = pymysql.connect(
                    host=host,
                    port=int(port or 3306),
                    database=database,
                    user=user,
                    password=password,
                    connect_timeout=10,
                    **extra_config
                )
                
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                
                return {'server_info': version}
                
            except ImportError:
                # Fallback para MySQLdb
                import MySQLdb
                conn = MySQLdb.connect(
                    host=host,
                    port=int(port or 3306),
                    db=database,
                    user=user,
                    passwd=password,
                    connect_timeout=10,
                    **extra_config
                )
                
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION();")
                version = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                
                return {'server_info': version}
            
        except ImportError:
            raise Exception("Nenhum driver MySQL encontrado. Execute: pip install pymysql ou pip install mysqlclient")
        except Exception as e:
            raise Exception(f"Erro MySQL: {str(e)}")
    
    def _test_sqlserver(self, host, port, database, user, password, extra_config):
        """Testar conexão SQL Server"""
        try:
            import pyodbc
            
            # Construir connection string
            conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={host},{port or 1433};DATABASE={database};UID={user};PWD={password}"
            
            conn = pyodbc.connect(conn_str, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION;")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {'server_info': version}
            
        except ImportError:
            raise Exception("Driver SQL Server (pyodbc) não está instalado")
        except Exception as e:
            raise Exception(f"Erro SQL Server: {str(e)}")
    
    def _test_oracle(self, host, port, database, user, password, extra_config):
        """Testar conexão Oracle"""
        try:
            import cx_Oracle
            
            dsn = cx_Oracle.makedsn(host, port or 1521, service_name=database)
            conn = cx_Oracle.connect(user, password, dsn)
            
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {'server_info': version}
            
        except ImportError:
            raise Exception("Driver Oracle (cx_Oracle) não está instalado")
        except Exception as e:
            raise Exception(f"Erro Oracle: {str(e)}")
    
    def _test_sqlite(self, database_path):
        """Testar conexão SQLite"""
        try:
            import sqlite3
            import os
            
            if not os.path.exists(database_path):
                raise Exception(f"Arquivo SQLite não encontrado: {database_path}")
            
            conn = sqlite3.connect(database_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {'server_info': f"SQLite {version}"}
            
        except Exception as e:
            raise Exception(f"Erro SQLite: {str(e)}")


# ===== QUERY VIEWSET =====

@extend_schema_view(
    list=extend_schema(
        tags=['queries'],
        summary='Listar consultas',
        description='Listar todas as consultas SQL do usuário com filtros e paginação'
    ),
    create=extend_schema(
        tags=['queries'],
        summary='Criar consulta',
        description='Criar uma nova consulta SQL',
        examples=[
            OpenApiExample(
                'Consulta Simples',
                value={
                    'name': 'Lista de Usuários',
                    'query': 'SELECT id, name, email FROM users WHERE active = 1',
                    'connection': 1,
                    'timeout': 30,
                    'cache_duration': 300
                }
            ),
            OpenApiExample(
                'Consulta com Parâmetros',
                value={
                    'name': 'Usuários por Departamento',
                    'query': 'SELECT * FROM users WHERE department = {{dept}} AND created_at >= {{start_date}}',
                    'connection': 1,
                    'parameters': [
                        {
                            'name': 'dept',
                            'type': 'text',
                            'description': 'Departamento',
                            'is_required': True
                        },
                        {
                            'name': 'start_date',
                            'type': 'date',
                            'description': 'Data inicial',
                            'is_required': False,
                            'default_value': '2024-01-01'
                        }
                    ]
                }
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['queries'],
        summary='Obter consulta',
        description='Obter detalhes de uma consulta específica'
    ),
    update=extend_schema(
        tags=['queries'],
        summary='Atualizar consulta',
        description='Atualizar informações de uma consulta'
    ),
    destroy=extend_schema(
        tags=['queries'],
        summary='Excluir consulta',
        description='Excluir uma consulta SQL'
    ),
)
class QueryViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de consultas SQL
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'query']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filtrar consultas baseado nas permissões do usuário"""
        user = self.request.user
        
        if user.is_superuser or user.is_admin:
            return Query.objects.all()
        elif user.is_staff:
            # Managers podem ver todas as consultas
            return Query.objects.all()
        else:
            # Users podem ver apenas suas próprias consultas
            return Query.objects.filter(created_by=user)
    
    def get_serializer_class(self):
        """Escolher serializer baseado na action"""
        if self.action == 'list':
            return QueryListSerializer
        elif self.action == 'execute':
            return QueryExecutionSerializer
        elif self.action == 'validate':
            return QueryValidationSerializer
        return QuerySerializer
    
    def perform_create(self, serializer):
        """Criar consulta e logar ação"""
        if not self.request.user.can_create_connection():
            self.permission_denied(
                self.request,
                message="Você não tem permissão para criar consultas"
            )
        
        query = serializer.save()
        log_user_action(
            user=self.request.user,
            action='create_query',
            details=f"Criada consulta: {query.name}"
        )
    
    def perform_update(self, serializer):
        """Atualizar consulta e logar ação"""
        query = self.get_object()
        if not self.request.user.can_edit_connection(query.connection):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para editar esta consulta"
            )
        
        old_name = query.name
        query = serializer.save()
        log_user_action(
            user=self.request.user,
            action='update_query',
            details=f"Atualizada consulta: {old_name} -> {query.name}"
        )
    
    def perform_destroy(self, instance):
        """Excluir consulta e logar ação"""
        if not self.request.user.can_edit_connection(instance.connection):
            self.permission_denied(
                self.request,
                message="Você não tem permissão para excluir esta consulta"
            )
        
        query_name = instance.name
        instance.delete()
        log_user_action(
            user=self.request.user,
            action='delete_query',
            details=f"Excluída consulta: {query_name}"
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Verificar permissão de visualização"""
        instance = self.get_object()
        if not request.user.can_view_connection(instance.connection):
            self.permission_denied(
                request,
                message="Você não tem permissão para visualizar esta consulta"
            )
        
        return super().retrieve(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], url_path='execute')
    def execute(self, request):
        """Executar consulta SQL"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query_id = serializer.validated_data['query_id']
        parameters = serializer.validated_data.get('parameters', {})
        limit = serializer.validated_data.get('limit', 100)
        
        try:
            query = Query.objects.get(id=query_id)
            
            # Executar consulta
            result = self._execute_query(query, parameters, limit, request.user)
            
            # Log da execução
            log_user_action(
                user=request.user,
                action='execute_query',
                details=f"Executada consulta: {query.name} - {result['records_count']} registros"
            )
            
            return Response(result)
            
        except Exception as e:
            log_user_action(
                user=request.user,
                action='execute_query',
                details=f"Erro ao executar consulta ID {query_id}: {str(e)}"
            )
            
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='validate')
    def validate_query(self, request):
        """Validar consulta SQL"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query_sql = serializer.validated_data['query']
        connection_id = serializer.validated_data['connection_id']
        
        try:
            connection = Connection.objects.get(id=connection_id)
            
            # Validar sintaxe SQL básica
            validation_result = self._validate_sql_syntax(query_sql, connection)
            
            return Response(validation_result)
            
        except Exception as e:
            return Response({
                'valid': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicar consulta"""
        original_query = self.get_object()
        
        if not request.user.can_view_connection(original_query.connection):
            return Response(
                {"error": "Você não tem permissão para duplicar esta consulta"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not request.user.can_create_connection():
            return Response(
                {"error": "Você não tem permissão para criar consultas"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_name = request.data.get('name', f"{original_query.name} (Cópia)")
        
        # Duplicar consulta
        new_query = Query.objects.create(
            name=new_name,
            query=original_query.query,
            connection=original_query.connection,
            timeout=original_query.timeout,
            cache_duration=original_query.cache_duration,
            created_by=request.user,
            is_active=True
        )
        
        # Duplicar parâmetros
        for query_param in original_query.queryparameter_set.all():
            QueryParameter.objects.create(
                query=new_query,
                parameter=query_param.parameter,
                default_value=query_param.default_value,
                is_required=query_param.is_required
            )
        
        log_user_action(
            user=request.user,
            action='duplicate_query',
            details=f"Duplicada consulta: {original_query.name} -> {new_name}"
        )
        
        serializer = QuerySerializer(new_query, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], url_path='execution-history')
    def execution_history(self, request, pk=None):
        """Obter histórico de execuções de uma consulta"""
        query = self.get_object()
        
        if not request.user.can_view_connection(query.connection):
            return Response(
                {"error": "Você não tem permissão para visualizar esta consulta"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Paginação
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        offset = (page - 1) * page_size
        
        # Filtros
        status_filter = request.query_params.get('status')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        # Query base
        executions = query.executions.all()
        
        # Aplicar filtros
        if status_filter:
            executions = executions.filter(status=status_filter)
        if date_from:
            executions = executions.filter(executed_at__gte=date_from)
        if date_to:
            executions = executions.filter(executed_at__lte=date_to)
        
        # Ordenar e paginar
        executions = executions.order_by('-executed_at')[offset:offset + page_size]
        
        # Serializar dados
        history_data = []
        for execution in executions:
            history_data.append({
                'id': execution.id,
                'executed_at': execution.executed_at,
                'user': execution.user.get_full_name(),
                'status': execution.status,
                'execution_time': execution.execution_time,
                'rows_returned': execution.rows_returned,
                'error_message': execution.error_message,
                'parameters': execution.parameters
            })
        
        # Estatísticas
        stats = query.executions.aggregate(
            total_executions=models.Count('id'),
            successful_executions=models.Count('id', filter=models.Q(status='success')),
            avg_execution_time=models.Avg('execution_time'),
            total_rows_returned=models.Sum('rows_returned')
        )
        
        return Response({
            'query_id': query.id,
            'query_name': query.name,
            'history': history_data,
            'statistics': {
                'total_executions': stats['total_executions'] or 0,
                'successful_executions': stats['successful_executions'] or 0,
                'success_rate': round((stats['successful_executions'] or 0) / max(stats['total_executions'] or 1, 1) * 100, 2),
                'avg_execution_time': round(stats['avg_execution_time'] or 0, 3),
                'total_rows_returned': stats['total_rows_returned'] or 0
            },
            'pagination': {
                'page': page,
                'page_size': page_size,
                'has_more': len(history_data) == page_size
            }
        })
    
    @action(detail=False, methods=['post'], url_path='export')
    def export_query_results(self, request):
        """Exportar resultados de consulta para Excel/CSV"""
        serializer = QueryExecutionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query_id = serializer.validated_data['query_id']
        parameters = serializer.validated_data.get('parameters', {})
        limit = serializer.validated_data.get('limit', 1000)
        format_type = request.data.get('format', 'excel')  # excel, csv
        
        try:
            query = Query.objects.get(id=query_id)
            
            if not request.user.can_view_connection(query.connection):
                return Response(
                    {"error": "Você não tem permissão para exportar esta consulta"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Executar consulta
            result = self._execute_query(query, parameters, limit, request.user)
            
            if not result['success']:
                return Response({
                    'error': 'Erro ao executar consulta para exportação'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Preparar dados para exportação
            import pandas as pd
            from django.http import HttpResponse
            import io
            
            # Criar DataFrame
            df = pd.DataFrame(result['rows'], columns=result['columns'])
            
            # Gerar arquivo
            if format_type.lower() == 'csv':
                # Exportar CSV
                output = io.StringIO()
                df.to_csv(output, index=False, encoding='utf-8')
                output.seek(0)
                
                response = HttpResponse(
                    output.getvalue(), 
                    content_type='text/csv; charset=utf-8'
                )
                response['Content-Disposition'] = f'attachment; filename="{query.name}_export.csv"'
                
            else:
                # Exportar Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Dados', index=False)
                    
                    # Adicionar metadados
                    metadata_df = pd.DataFrame([
                        ['Consulta', query.name],
                        ['Executado em', timezone.now().strftime('%d/%m/%Y %H:%M:%S')],
                        ['Usuário', request.user.get_full_name()],
                        ['Registros', len(result['rows'])],
                        ['Tempo de execução', f"{result['execution_time_ms']}ms"]
                    ], columns=['Campo', 'Valor'])
                    
                    metadata_df.to_excel(writer, sheet_name='Metadados', index=False)
                
                output.seek(0)
                
                response = HttpResponse(
                    output.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="{query.name}_export.xlsx"'
            
            # Log da exportação
            log_user_action(
                user=request.user,
                action='export_query',
                details=f"Exportada consulta: {query.name} ({format_type}) - {len(result['rows'])} registros"
            )
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Erro na exportação: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='execute-paginated')
    def execute_paginated(self, request):
        """Executar consulta SQL com paginação"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query_id = serializer.validated_data['query_id']
        parameters = serializer.validated_data.get('parameters', {})
        page = request.data.get('page', 1)
        page_size = request.data.get('page_size', 50)
        
        # Validar page_size
        if page_size not in [10, 50, 100]:
            page_size = 50
            
        try:
            query = Query.objects.get(id=query_id)
            
            if not request.user.can_view_connection(query.connection):
                return Response(
                    {"error": "Você não tem permissão para executar esta consulta"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Executar consulta com paginação
            result = self._execute_query_paginated(query, parameters, page, page_size, request.user)
            
            return Response(result)
            
        except Exception as e:
            log_user_action(
                user=request.user,
                action='execute_query_paginated',
                details=f"Erro ao executar consulta paginada ID {query_id}: {str(e)}"
            )
            
            return Response({
                'success': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _execute_query_paginated(self, query, parameters, page, page_size, user):
        """Executar consulta SQL com paginação"""
        import time
        from django.core.cache import cache
        
        start_time = time.time()
        
        try:
            # Substituir parâmetros na consulta
            sql_query = self._replace_query_parameters(query.query, parameters)
            
            # Adicionar OFFSET e LIMIT para paginação
            offset = (page - 1) * page_size
            
            # Adaptar paginação por tipo de banco
            if query.connection.sgbd == 'sqlserver':
                # SQL Server usa OFFSET/FETCH
                sql_query += f" OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY"
            elif query.connection.sgbd == 'oracle':
                # Oracle usa ROWNUM (mais complexo)
                sql_query = f"SELECT * FROM (SELECT a.*, ROWNUM rnum FROM ({sql_query}) a WHERE ROWNUM <= {offset + page_size}) WHERE rnum > {offset}"
            else:
                # PostgreSQL, MySQL, SQLite usam LIMIT/OFFSET
                sql_query += f" LIMIT {page_size} OFFSET {offset}"
            
            # Obter conexão de banco
            db_connection = self._get_database_connection(query.connection)
            
            # Executar consulta principal
            cursor = db_connection.cursor()
            cursor.execute(sql_query)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            # Contar total de registros (sem paginação)
            count_query = self._replace_query_parameters(query.query, parameters)
            count_sql = f"SELECT COUNT(*) as total FROM ({count_query}) as count_table"
            
            cursor.execute(count_sql)
            total_records = cursor.fetchone()[0]
            
            cursor.close()
            db_connection.close()
            
            end_time = time.time()
            execution_time = round((end_time - start_time) * 1000, 2)
            
            # Calcular informações de paginação
            total_pages = (total_records + page_size - 1) // page_size
            has_next = page < total_pages
            has_previous = page > 1
            
            result = {
                'success': True,
                'columns': columns,
                'rows': [list(row) for row in rows],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_records': total_records,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_previous': has_previous,
                    'records_in_page': len(rows)
                },
                'execution_time_ms': execution_time,
                'timestamp': timezone.now().isoformat()
            }
            
            # Salvar execução no histórico
            QueryExecution.objects.create(
                query=query,
                user=user,
                status='success',
                execution_time=execution_time / 1000,
                rows_returned=len(rows),
                parameters=parameters
            )
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = round((end_time - start_time) * 1000, 2)
            
            # Salvar execução com erro
            QueryExecution.objects.create(
                query=query,
                user=user,
                status='error',
                execution_time=execution_time / 1000,
                error_message=str(e),
                parameters=parameters
            )
            
            raise e
