import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  TextField,
  Typography,
  Alert,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
  AccountTree as NodesIcon,
} from '@mui/icons-material';
import { Project, ProjectForm } from '../types';
import { projectService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const ProjectsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectToDelete, setProjectToDelete] = useState<Project | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<ProjectForm>({
    name: '',
    description: '',
  });
  
  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error',
  });

  // Carregar projetos
  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await projectService.getAll();
      setProjects(response.results || response);
      setError(null);
    } catch (err) {
      console.error('Erro ao carregar projetos:', err);
      setError('Erro ao carregar projetos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // Abrir dialog para novo projeto
  const handleNewProject = () => {
    setEditingProject(null);
    setFormData({ name: '', description: '' });
    setDialogOpen(true);
  };

  // Abrir dialog para editar projeto
  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setFormData({
      name: project.name,
      description: project.description || '',
    });
    setDialogOpen(true);
  };

  // Salvar projeto (criar ou editar)
  const handleSaveProject = async () => {
    try {
      if (editingProject) {
        // Editar projeto existente
        await projectService.update(editingProject.id, formData);
        setSnackbar({
          open: true,
          message: 'Projeto atualizado com sucesso!',
          severity: 'success',
        });
      } else {
        // Criar novo projeto
        await projectService.create(formData);
        setSnackbar({
          open: true,
          message: 'Projeto criado com sucesso!',
          severity: 'success',
        });
      }
      
      setDialogOpen(false);
      loadProjects();
    } catch (err) {
      console.error('Erro ao salvar projeto:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao salvar projeto',
        severity: 'error',
      });
    }
  };

  // Confirmar exclusão
  const handleDeleteClick = (project: Project) => {
    setProjectToDelete(project);
    setDeleteDialogOpen(true);
  };

  // Deletar projeto
  const handleDeleteProject = async () => {
    if (!projectToDelete) return;

    try {
      await projectService.delete(projectToDelete.id);
      setSnackbar({
        open: true,
        message: 'Projeto excluído com sucesso!',
        severity: 'success',
      });
      setDeleteDialogOpen(false);
      setProjectToDelete(null);
      loadProjects();
    } catch (err) {
      console.error('Erro ao excluir projeto:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao excluir projeto',
        severity: 'error',
      });
    }
  };

  // Fechar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Carregando projetos...</Typography>
      </Box>
    );
  }

  return (
    <Layout>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Gestão de Projetos
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            Gerencie projetos e sua estrutura hierárquica de relatórios.
          </Typography>
        </Box>

        {/* Breadcrumbs */}
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
        <Link
          color="inherit"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate('/dashboard');
          }}
          sx={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}
        >
          <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
          Dashboard
        </Link>
        <Typography color="text.primary">Projetos</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Gerenciamento de Projetos
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleNewProject}
        >
          Novo Projeto
        </Button>
      </Box>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Projects Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nome</TableCell>
              <TableCell>Descrição</TableCell>
              <TableCell>Criado em</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center" width="150">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography color="textSecondary">
                    Nenhum projeto encontrado. Clique em "Novo Projeto" para começar.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              projects.map((project) => (
                <TableRow key={project.id} hover>
                  <TableCell>
                    <Typography variant="subtitle2" fontWeight="bold">
                      {project.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {project.description || 'Sem descrição'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {new Date(project.created_at).toLocaleDateString('pt-BR')}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={project.is_active ? 'Ativo' : 'Inativo'}
                      color={project.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/projects/${project.id}/nodes`)}
                      title="Gerenciar Nós"
                      color="primary"
                    >
                      <NodesIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleEditProject(project)}
                      title="Editar"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteClick(project)}
                      title="Excluir"
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para criar/editar projeto */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingProject ? 'Editar Projeto' : 'Novo Projeto'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nome do Projeto"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Descrição"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSaveProject}
            variant="contained"
            disabled={!formData.name.trim()}
          >
            {editingProject ? 'Atualizar' : 'Criar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de confirmação para excluir */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmar Exclusão</DialogTitle>
        <DialogContent>
          <Typography>
            Tem certeza que deseja excluir o projeto "{projectToDelete?.name}"?
            Esta ação não pode ser desfeita.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleDeleteProject}
            color="error"
            variant="contained"
          >
            Excluir
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar para feedback */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert 
          onClose={handleCloseSnackbar} 
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
      </Paper>
    </Layout>
  );
};

export default ProjectsPage;
