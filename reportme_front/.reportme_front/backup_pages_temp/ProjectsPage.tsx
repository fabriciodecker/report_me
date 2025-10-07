import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Fab,
  Grid,
  IconButton,
  TextField,
  Typography,
  Alert,
  Snackbar,
  Menu,
  MenuItem,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  FolderOpen as FolderIcon,
  InsertDriveFile as FileIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import { Project, ProjectNode, ProjectForm } from '../types';
import { projectService, projectNodeService } from '../services/api';
import Layout from '../components/Layout';

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projectTree, setProjectTree] = useState<ProjectNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<ProjectNode | null>(null);
  const [breadcrumbs, setBreadcrumbs] = useState<ProjectNode[]>([]);
  
  // Dialog states
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [nodeDialogOpen, setNodeDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [editingNode, setEditingNode] = useState<ProjectNode | null>(null);
  
  // Form states
  const [projectForm, setProjectForm] = useState<ProjectForm>({ name: '', description: '' });
  const [nodeForm, setNodeForm] = useState({ name: '', parent_id: undefined as number | undefined });
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [contextMenu, setContextMenu] = useState<{ mouseX: number; mouseY: number; node: ProjectNode } | null>(null);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load project tree when project is selected
  useEffect(() => {
    if (selectedProject) {
      loadProjectTree(selectedProject.id);
    }
  }, [selectedProject]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await projectService.getAll();
      setProjects(response.results);
    } catch (error) {
      showSnackbar('Erro ao carregar projetos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadProjectTree = async (projectId: number) => {
    try {
      const tree = await projectService.getTree(projectId);
      setProjectTree(tree);
    } catch (error) {
      showSnackbar('Erro ao carregar árvore do projeto', 'error');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleProjectSubmit = async () => {
    try {
      setLoading(true);
      if (editingProject) {
        await projectService.update(editingProject.id, projectForm);
        showSnackbar('Projeto atualizado com sucesso!', 'success');
      } else {
        const newProject = await projectService.create(projectForm);
        showSnackbar('Projeto criado com sucesso!', 'success');
        setSelectedProject(newProject);
      }
      await loadProjects();
      setProjectDialogOpen(false);
      setEditingProject(null);
      setProjectForm({ name: '', description: '' });
    } catch (error) {
      showSnackbar('Erro ao salvar projeto', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeSubmit = async () => {
    if (!selectedProject) return;
    
    try {
      setLoading(true);
      const nodeData = {
        ...nodeForm,
        project: selectedProject.id,
      };
      
      if (editingNode) {
        await projectNodeService.update(editingNode.id, nodeData);
        showSnackbar('Nó atualizado com sucesso!', 'success');
      } else {
        await projectNodeService.create(nodeData);
        showSnackbar('Nó criado com sucesso!', 'success');
      }
      
      await loadProjectTree(selectedProject.id);
      setNodeDialogOpen(false);
      setEditingNode(null);
      setNodeForm({ name: '', parent_id: undefined });
    } catch (error) {
      showSnackbar('Erro ao salvar nó', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProject = async () => {
    if (!selectedProject) return;
    
    try {
      setLoading(true);
      await projectService.delete(selectedProject.id);
      showSnackbar('Projeto excluído com sucesso!', 'success');
      setDeleteDialogOpen(false);
      setSelectedProject(null);
      setProjectTree([]);
      await loadProjects();
    } catch (error) {
      showSnackbar('Erro ao excluir projeto', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteNode = async () => {
    if (!selectedNode || !selectedProject) return;
    
    try {
      setLoading(true);
      await projectNodeService.delete(selectedNode.id);
      showSnackbar('Nó excluído com sucesso!', 'success');
      setDeleteDialogOpen(false);
      setSelectedNode(null);
      await loadProjectTree(selectedProject.id);
    } catch (error) {
      showSnackbar('Erro ao excluir nó', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleContextMenu = (event: React.MouseEvent, node: ProjectNode) => {
    event.preventDefault();
    setContextMenu({
      mouseX: event.clientX - 2,
      mouseY: event.clientY - 4,
      node,
    });
  };

  const handleContextMenuClose = () => {
    setContextMenu(null);
  };

  const handleEditNode = (node: ProjectNode) => {
    setEditingNode(node);
    setNodeForm({ name: node.name, parent_id: node.parent_id });
    setNodeDialogOpen(true);
    handleContextMenuClose();
  };

  const handleDeleteNodeClick = (node: ProjectNode) => {
    setSelectedNode(node);
    setDeleteDialogOpen(true);
    handleContextMenuClose();
  };

  const handleAddChildNode = (parentNode: ProjectNode) => {
    setNodeForm({ name: '', parent_id: parentNode.id });
    setNodeDialogOpen(true);
    handleContextMenuClose();
  };

  const renderTreeItem = (node: ProjectNode): React.ReactNode => (
    <TreeItem
      key={node.id}
      itemId={node.id.toString()}
      label={
        <Box
          sx={{ display: 'flex', alignItems: 'center', p: 0.5, pr: 0 }}
          onContextMenu={(e) => handleContextMenu(e, node)}
        >
          {node.query_id ? <FileIcon sx={{ mr: 1 }} /> : <FolderIcon sx={{ mr: 1 }} />}
          <Typography variant="body2" sx={{ fontWeight: 'inherit', flexGrow: 1 }}>
            {node.name}
          </Typography>
        </Box>
      }
    >
      {node.children?.map((child) => renderTreeItem(child))}
    </TreeItem>
  );

  const updateBreadcrumbs = (node: ProjectNode) => {
    const path: ProjectNode[] = [];
    let current: ProjectNode | undefined = node;
    
    while (current) {
      path.unshift(current);
      current = findNodeById(projectTree, current.parent_id);
    }
    
    setBreadcrumbs(path);
  };

  const findNodeById = (nodes: ProjectNode[], id?: number): ProjectNode | undefined => {
    if (!id) return undefined;
    
    for (const node of nodes) {
      if (node.id === id) return node;
      const found = findNodeById(node.children || [], id);
      if (found) return found;
    }
    return undefined;
  };

  return (
    <Layout>
      <Box sx={{ flexGrow: 1 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Gerenciamento de Projetos
        </Typography>

        <Grid container spacing={3}>
          {/* Lista de Projetos */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Projetos</Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => setProjectDialogOpen(true)}
                  >
                    Novo
                  </Button>
                </Box>
                
                <Box sx={{ maxHeight: '70vh', overflow: 'auto' }}>
                  {projects.map((project) => (
                    <Card
                      key={project.id}
                      variant={selectedProject?.id === project.id ? "outlined" : "elevation"}
                      sx={{
                        mb: 1,
                        cursor: 'pointer',
                        border: selectedProject?.id === project.id ? 2 : 1,
                        borderColor: selectedProject?.id === project.id ? 'primary.main' : 'divider',
                      }}
                      onClick={() => setSelectedProject(project)}
                    >
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Box>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {project.name}
                            </Typography>
                            {project.description && (
                              <Typography variant="body2" color="text.secondary">
                                {project.description}
                              </Typography>
                            )}
                            <Typography variant="caption" color="text.secondary">
                              {project.node_count || 0} nós • {project.query_count || 0} consultas
                            </Typography>
                          </Box>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingProject(project);
                              setProjectForm({ name: project.name, description: project.description || '' });
                              setProjectDialogOpen(true);
                            }}
                          >
                            <EditIcon />
                          </IconButton>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Árvore do Projeto */}
          <Grid size={{ xs: 12, md: 8 }}>
            {selectedProject ? (
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">{selectedProject.name}</Typography>
                    <Box>
                      <Button
                        variant="outlined"
                        startIcon={<AddIcon />}
                        onClick={() => {
                          setNodeForm({ name: '', parent_id: undefined });
                          setNodeDialogOpen(true);
                        }}
                        sx={{ mr: 1 }}
                      >
                        Novo Nó
                      </Button>
                      <Button
                        variant="outlined"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => setDeleteDialogOpen(true)}
                      >
                        Excluir Projeto
                      </Button>
                    </Box>
                  </Box>

                  {breadcrumbs.length > 0 && (
                    <Breadcrumbs sx={{ mb: 2 }}>
                      <Link
                        underline="hover"
                        color="inherit"
                        href="#"
                        onClick={() => setBreadcrumbs([])}
                      >
                        <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
                        Raiz
                      </Link>
                      {breadcrumbs.map((crumb) => (
                        <Typography key={crumb.id} color="text.primary">
                          {crumb.name}
                        </Typography>
                      ))}
                    </Breadcrumbs>
                  )}

                  <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
                    {projectTree.length > 0 ? (
                      <SimpleTreeView>
                        {projectTree.map((node) => renderTreeItem(node))}
                      </SimpleTreeView>
                    ) : (
                      <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
                        Nenhum nó encontrado. Clique em "Novo Nó" para começar.
                      </Typography>
                    )}
                  </Box>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent>
                  <Typography color="text.secondary" align="center" sx={{ py: 8 }}>
                    Selecione um projeto para visualizar sua estrutura
                  </Typography>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>

        {/* Context Menu */}
        <Menu
          open={contextMenu !== null}
          onClose={handleContextMenuClose}
          anchorReference="anchorPosition"
          anchorPosition={
            contextMenu !== null
              ? { top: contextMenu.mouseY, left: contextMenu.mouseX }
              : undefined
          }
        >
          <MenuItem onClick={() => contextMenu && handleEditNode(contextMenu.node)}>
            <EditIcon sx={{ mr: 1 }} /> Editar
          </MenuItem>
          <MenuItem onClick={() => contextMenu && handleAddChildNode(contextMenu.node)}>
            <AddIcon sx={{ mr: 1 }} /> Adicionar Filho
          </MenuItem>
          <MenuItem onClick={() => contextMenu && handleDeleteNodeClick(contextMenu.node)}>
            <DeleteIcon sx={{ mr: 1 }} /> Excluir
          </MenuItem>
        </Menu>

        {/* Dialog para Projeto */}
        <Dialog open={projectDialogOpen} onClose={() => setProjectDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {editingProject ? 'Editar Projeto' : 'Novo Projeto'}
          </DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Nome"
              fullWidth
              variant="outlined"
              value={projectForm.name}
              onChange={(e) => setProjectForm({ ...projectForm, name: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Descrição"
              fullWidth
              multiline
              rows={3}
              variant="outlined"
              value={projectForm.description}
              onChange={(e) => setProjectForm({ ...projectForm, description: e.target.value })}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setProjectDialogOpen(false)}>Cancelar</Button>
            <Button onClick={handleProjectSubmit} variant="contained" disabled={!projectForm.name || loading}>
              {editingProject ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog para Nó */}
        <Dialog open={nodeDialogOpen} onClose={() => setNodeDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {editingNode ? 'Editar Nó' : 'Novo Nó'}
          </DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Nome"
              fullWidth
              variant="outlined"
              value={nodeForm.name}
              onChange={(e) => setNodeForm({ ...nodeForm, name: e.target.value })}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNodeDialogOpen(false)}>Cancelar</Button>
            <Button onClick={handleNodeSubmit} variant="contained" disabled={!nodeForm.name || loading}>
              {editingNode ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog de Confirmação de Exclusão */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Confirmar Exclusão</DialogTitle>
          <DialogContent>
            <Typography>
              {selectedNode 
                ? `Tem certeza que deseja excluir o nó "${selectedNode.name}"?`
                : `Tem certeza que deseja excluir o projeto "${selectedProject?.name}"?`
              }
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
            <Button
              onClick={selectedNode ? handleDeleteNode : handleDeleteProject}
              color="error"
              variant="contained"
              disabled={loading}
            >
              Excluir
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Layout>
  );
};

export default ProjectsPage;
