"""
Testes para o sistema de projetos do ReportMe
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Project, ProjectNode
from tests import (
    BaseAPITestCase, 
    TestConstants, 
    TestDataFactory,
    PermissionTestMixin,
    ValidationTestMixin
)
import json

User = get_user_model()


class ProjectViewSetTestCase(BaseAPITestCase, PermissionTestMixin, ValidationTestMixin):
    """
    Testes para ProjectViewSet (CRUD de projetos)
    """
    
    def test_list_projects_authenticated_admin(self):
        """Testa listagem de projetos como admin"""
        self.authenticate_admin()
        
        response = self.client.get(TestConstants.PROJECTS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertTrue(len(response.data['results']) >= 1)  # Pelo menos o projeto de teste
    
    def test_list_projects_authenticated_editor(self):
        """Testa listagem de projetos como editor"""
        self.authenticate_editor()
        
        response = self.client.get(TestConstants.PROJECTS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Editor pode ver todos os projetos
        self.assertIn('results', response.data)
    
    def test_list_projects_authenticated_readonly(self):
        """Testa listagem de projetos como readonly"""
        self.authenticate_readonly()
        
        response = self.client.get(TestConstants.PROJECTS_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Readonly só vê projetos próprios ou compartilhados
        self.assertIn('results', response.data)
    
    def test_list_projects_unauthenticated(self):
        """Testa listagem sem autenticação"""
        response = self.client.get(TestConstants.PROJECTS_URL)
        self.assert_permission_denied(response)
    
    def test_create_project_success(self):
        """Testa criação de projeto com dados válidos"""
        self.authenticate_admin()
        
        data = {
            'name': 'Novo Projeto',
            'description': 'Descrição do novo projeto'
        }
        
        response = self.client.post(TestConstants.PROJECTS_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Novo Projeto')
        self.assertEqual(response.data['description'], 'Descrição do novo projeto')
        self.assertEqual(response.data['owner'], self.admin_user.id)
        
        # Verificar se projeto foi criado no banco
        project = Project.objects.get(id=response.data['id'])
        self.assertEqual(project.name, 'Novo Projeto')
        self.assertEqual(project.owner, self.admin_user)
    
    def test_create_project_readonly_permission_denied(self):
        """Testa criação de projeto como readonly (deve falhar)"""
        self.authenticate_readonly()
        
        data = {
            'name': 'Projeto Readonly',
            'description': 'Não deveria conseguir criar'
        }
        
        response = self.client.post(TestConstants.PROJECTS_URL, data)
        self.assert_permission_denied(response)
    
    def test_create_project_invalid_data(self):
        """Testa criação com dados inválidos"""
        self.authenticate_admin()
        
        # Nome vazio
        data = {
            'name': '',
            'description': 'Descrição válida'
        }
        
        response = self.client.post(TestConstants.PROJECTS_URL, data)
        self.assert_validation_error(response, 'name')
    
    def test_retrieve_project_success(self):
        """Testa recuperação de projeto específico"""
        self.authenticate_admin()
        
        url = f"{TestConstants.PROJECTS_URL}{self.test_project.id}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.test_project.id)
        self.assertEqual(response.data['name'], self.test_project.name)
    
    def test_retrieve_project_not_found(self):
        """Testa recuperação de projeto inexistente"""
        self.authenticate_admin()
        
        url = f"{TestConstants.PROJECTS_URL}99999/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_project_success(self):
        """Testa atualização de projeto"""
        self.authenticate_admin()
        
        data = {
            'name': 'Projeto Atualizado',
            'description': 'Descrição atualizada'
        }
        
        url = f"{TestConstants.PROJECTS_URL}{self.test_project.id}/"
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Projeto Atualizado')
        
        # Verificar se foi atualizado no banco
        self.test_project.refresh_from_db()
        self.assertEqual(self.test_project.name, 'Projeto Atualizado')
    
    def test_update_project_partial(self):
        """Testa atualização parcial de projeto"""
        self.authenticate_admin()
        
        data = {'name': 'Apenas Nome Novo'}
        
        url = f"{TestConstants.PROJECTS_URL}{self.test_project.id}/"
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Apenas Nome Novo')
        # Descrição deve permanecer a mesma
        self.assertEqual(response.data['description'], self.test_project.description)
    
    def test_update_project_permission_denied(self):
        """Testa atualização por usuário sem permissão"""
        # Criar projeto de outro usuário
        other_user = TestDataFactory.create_user('other')
        other_project = TestDataFactory.create_project(other_user, name='Projeto de Outro')
        
        self.authenticate_readonly()
        
        data = {'name': 'Tentativa de Hack'}
        url = f"{TestConstants.PROJECTS_URL}{other_project.id}/"
        response = self.client.put(url, data)
        
        self.assert_permission_denied(response)
    
    def test_delete_project_success(self):
        """Testa exclusão de projeto"""
        # Criar projeto para deletar
        project_to_delete = TestDataFactory.create_project(
            self.admin_user, 
            name='Projeto para Deletar'
        )
        
        self.authenticate_admin()
        
        url = f"{TestConstants.PROJECTS_URL}{project_to_delete.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar se foi deletado
        with self.assertRaises(Project.DoesNotExist):
            Project.objects.get(id=project_to_delete.id)
    
    def test_delete_project_permission_denied(self):
        """Testa exclusão por usuário sem permissão"""
        self.authenticate_readonly()
        
        url = f"{TestConstants.PROJECTS_URL}{self.test_project.id}/"
        response = self.client.delete(url)
        
        self.assert_permission_denied(response)
    
    def test_project_tree_action(self):
        """Testa action tree do projeto"""
        self.authenticate_admin()
        
        url = f"{TestConstants.PROJECTS_URL}{self.test_project.id}/tree/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tree', response.data)
        self.assertIsInstance(response.data['tree'], list)
    
    def test_duplicate_project_action(self):
        """Testa duplicação de projeto"""
        self.authenticate_admin()
        
        data = {'name': 'Projeto Duplicado'}
        
        url = f"{TestConstants.PROJECTS_URL}{self.test_project.id}/duplicate/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Projeto Duplicado')
        
        # Verificar se foi criado novo projeto
        duplicated_project = Project.objects.get(id=response.data['id'])
        self.assertEqual(duplicated_project.name, 'Projeto Duplicado')
        self.assertEqual(duplicated_project.owner, self.admin_user)
        self.assertNotEqual(duplicated_project.id, self.test_project.id)


class ProjectNodeViewSetTestCase(BaseAPITestCase, PermissionTestMixin, ValidationTestMixin):
    """
    Testes para ProjectNodeViewSet (CRUD de nós de projeto)
    """
    
    def test_list_project_nodes(self):
        """Testa listagem de nós de projeto"""
        self.authenticate_admin()
        
        response = self.client.get(TestConstants.PROJECT_NODES_URL)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_create_project_node_success(self):
        """Testa criação de nó de projeto"""
        self.authenticate_admin()
        
        data = {
            'project': self.test_project.id,
            'name': 'Novo Nó',
            'description': 'Descrição do novo nó',
            'parent': self.root_node.id
        }
        
        response = self.client.post(TestConstants.PROJECT_NODES_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Novo Nó')
        self.assertEqual(response.data['parent'], self.root_node.id)
        
        # Verificar hierarquia
        new_node = ProjectNode.objects.get(id=response.data['id'])
        self.assertEqual(new_node.parent, self.root_node)
    
    def test_create_root_node(self):
        """Testa criação de nó raiz (sem parent)"""
        self.authenticate_admin()
        
        data = {
            'project': self.test_project.id,
            'name': 'Novo Nó Raiz',
            'description': 'Nó raiz do projeto'
        }
        
        response = self.client.post(TestConstants.PROJECT_NODES_URL, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['parent'])
    
    def test_create_node_invalid_parent(self):
        """Testa criação com parent inválido (de outro projeto)"""
        # Criar outro projeto com nó
        other_project = TestDataFactory.create_project(self.admin_user, name='Outro Projeto')
        other_node = ProjectNode.objects.create(
            project=other_project,
            name='Nó de Outro Projeto'
        )
        
        self.authenticate_admin()
        
        data = {
            'project': self.test_project.id,
            'name': 'Nó Inválido',
            'parent': other_node.id  # Parent de outro projeto
        }
        
        response = self.client.post(TestConstants.PROJECT_NODES_URL, data)
        self.assert_validation_error(response)
    
    def test_update_project_node(self):
        """Testa atualização de nó de projeto"""
        self.authenticate_admin()
        
        data = {
            'name': 'Nó Atualizado',
            'description': 'Descrição atualizada'
        }
        
        url = f"{TestConstants.PROJECT_NODES_URL}{self.child_node.id}/"
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Nó Atualizado')
    
    def test_delete_project_node_with_children(self):
        """Testa exclusão de nó que tem filhos"""
        self.authenticate_admin()
        
        url = f"{TestConstants.PROJECT_NODES_URL}{self.root_node.id}/"
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar se filhos também foram deletados (ou órfãos)
        # Depende da implementação do modelo
        with self.assertRaises(ProjectNode.DoesNotExist):
            ProjectNode.objects.get(id=self.root_node.id)
    
    def test_move_node_action(self):
        """Testa action de mover nó"""
        # Criar outro nó para mover
        another_root = ProjectNode.objects.create(
            project=self.test_project,
            name='Outra Raiz'
        )
        
        self.authenticate_admin()
        
        data = {'new_parent': another_root.id}
        
        url = f"{TestConstants.PROJECT_NODES_URL}{self.child_node.id}/move/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar se foi movido
        self.child_node.refresh_from_db()
        self.assertEqual(self.child_node.parent, another_root)
    
    def test_duplicate_node_action(self):
        """Testa duplicação de nó"""
        self.authenticate_admin()
        
        data = {'name': 'Nó Duplicado'}
        
        url = f"{TestConstants.PROJECT_NODES_URL}{self.child_node.id}/duplicate/"
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Nó Duplicado')
        self.assertEqual(response.data['parent'], self.child_node.parent.id)


class ProjectModelTestCase(TestCase):
    """
    Testes para o modelo Project
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_project_creation(self):
        """Testa criação de projeto"""
        project = Project.objects.create(
            name='Projeto Teste',
            description='Descrição do projeto',
            owner=self.user
        )
        
        self.assertEqual(project.name, 'Projeto Teste')
        self.assertEqual(project.description, 'Descrição do projeto')
        self.assertEqual(project.owner, self.user)
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)
    
    def test_project_string_representation(self):
        """Testa representação string do projeto"""
        project = Project.objects.create(
            name='Projeto Teste',
            owner=self.user
        )
        
        expected = 'Projeto Teste'
        self.assertEqual(str(project), expected)
    
    def test_project_get_root_nodes(self):
        """Testa método get_root_nodes"""
        project = Project.objects.create(
            name='Projeto com Nós',
            owner=self.user
        )
        
        # Criar nós raiz
        root1 = ProjectNode.objects.create(
            project=project,
            name='Raiz 1'
        )
        root2 = ProjectNode.objects.create(
            project=project,
            name='Raiz 2'
        )
        
        # Criar nó filho
        child = ProjectNode.objects.create(
            project=project,
            name='Filho',
            parent=root1
        )
        
        root_nodes = project.get_root_nodes()
        
        self.assertEqual(root_nodes.count(), 2)
        self.assertIn(root1, root_nodes)
        self.assertIn(root2, root_nodes)
        self.assertNotIn(child, root_nodes)


class ProjectNodeModelTestCase(TestCase):
    """
    Testes para o modelo ProjectNode
    """
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.project = Project.objects.create(
            name='Projeto Teste',
            owner=self.user
        )
    
    def test_project_node_creation(self):
        """Testa criação de nó de projeto"""
        node = ProjectNode.objects.create(
            project=self.project,
            name='Nó Teste',
            description='Descrição do nó'
        )
        
        self.assertEqual(node.project, self.project)
        self.assertEqual(node.name, 'Nó Teste')
        self.assertEqual(node.description, 'Descrição do nó')
        self.assertIsNone(node.parent)
        self.assertIsNotNone(node.created_at)
    
    def test_hierarchical_relationship(self):
        """Testa relacionamento hierárquico"""
        parent = ProjectNode.objects.create(
            project=self.project,
            name='Parent'
        )
        
        child = ProjectNode.objects.create(
            project=self.project,
            name='Child',
            parent=parent
        )
        
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())
    
    def test_node_string_representation(self):
        """Testa representação string do nó"""
        node = ProjectNode.objects.create(
            project=self.project,
            name='Nó Teste'
        )
        
        expected = 'Projeto Teste / Nó Teste'
        self.assertEqual(str(node), expected)
    
    def test_get_level_method(self):
        """Testa método get_level"""
        # Nó raiz
        root = ProjectNode.objects.create(
            project=self.project,
            name='Raiz'
        )
        
        # Nó nível 1
        level1 = ProjectNode.objects.create(
            project=self.project,
            name='Nível 1',
            parent=root
        )
        
        # Nó nível 2
        level2 = ProjectNode.objects.create(
            project=self.project,
            name='Nível 2',
            parent=level1
        )
        
        self.assertEqual(root.get_level(), 0)
        self.assertEqual(level1.get_level(), 1)
        self.assertEqual(level2.get_level(), 2)
    
    def test_get_descendants_method(self):
        """Testa método get_descendants"""
        root = ProjectNode.objects.create(
            project=self.project,
            name='Raiz'
        )
        
        child1 = ProjectNode.objects.create(
            project=self.project,
            name='Filho 1',
            parent=root
        )
        
        child2 = ProjectNode.objects.create(
            project=self.project,
            name='Filho 2',
            parent=root
        )
        
        grandchild = ProjectNode.objects.create(
            project=self.project,
            name='Neto',
            parent=child1
        )
        
        descendants = root.get_descendants()
        
        self.assertEqual(descendants.count(), 3)
        self.assertIn(child1, descendants)
        self.assertIn(child2, descendants)
        self.assertIn(grandchild, descendants)