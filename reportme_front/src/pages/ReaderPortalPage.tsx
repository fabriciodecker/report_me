import React, { useEffect, useState } from 'react';
import { projectService } from '../services/api';
import { Project } from '../types';
import Layout from '../components/Layout';
import { 
  List, 
  ListItemButton, 
  ListItemText, 
  Typography, 
  Paper, 
  CircularProgress, 
  Alert,
  Box,
  Chip
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ReaderPortalPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        console.log('Carregando projetos...');
        console.log('Usuário:', user);
        console.log('Token:', localStorage.getItem('access_token'));
        
        const resp = await projectService.getAll();
        console.log('Resposta da API:', resp);
        console.log('Projects array:', resp.results);
        setProjects(resp.results || []);
        setError(null);
      } catch (err: any) {
        console.error('Erro ao carregar projetos:', err);
        console.error('Detalhes do erro:', err.response?.data);
        console.error('Status:', err.response?.status);
        console.error('Headers:', err.response?.headers);
        setError(err.response?.data?.detail || err.message || 'Erro ao carregar projetos');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  const handleProjectSelect = (project: Project) => {
    navigate(`/reader/projects/${project.id}`);
  };

  return (
    <Layout>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Portal de Relatórios
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            Bem-vindo, {user?.username}! Selecione um projeto para navegar pelos relatórios disponíveis.
          </Typography>
          {user?.is_staff && (
            <Chip 
              label="Administrador" 
              color="primary" 
              size="small" 
              sx={{ mt: 1 }}
            />
          )}
        </Box>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && projects.length === 0 && (
          <Alert severity="info">
            Nenhum projeto encontrado. {user?.is_staff ? 'Acesse o painel de administração para criar projetos.' : 'Entre em contato com o administrador.'}
          </Alert>
        )}

        {!loading && !error && projects.length > 0 && (
          <>
            <Typography variant="h6" gutterBottom>
              Projetos Disponíveis ({projects.length})
            </Typography>
            <List>
              {projects.map((project) => (
                <ListItemButton 
                  key={project.id} 
                  onClick={() => handleProjectSelect(project)}
                  sx={{ 
                    mb: 1, 
                    border: 1, 
                    borderColor: 'divider', 
                    borderRadius: 1,
                    '&:hover': {
                      backgroundColor: 'action.hover',
                    }
                  }}
                >
                  <ListItemText 
                    primary={project.name} 
                    secondary={project.description || 'Sem descrição'} 
                    primaryTypographyProps={{ variant: 'h6' }}
                    secondaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItemButton>
              ))}
            </List>
          </>
        )}
      </Paper>
    </Layout>
  );
};

export default ReaderPortalPage;
