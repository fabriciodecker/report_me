import React from 'react';
import { Typography, Paper, Box, Chip } from '@mui/material';
import Layout from '../components/Layout';
import { FolderOpen, Dashboard, Settings, Storage as QueryIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <Layout>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Portal de Administração
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            Bem-vindo, {user?.username}! Gerencie projetos, conexões e consultas do sistema.
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
          
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Acesso Rápido
            </Typography>
            <Box sx={{ 
              display: 'grid', 
              gap: 2, 
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              mt: 2 
            }}>
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { elevation: 4 }
                }}
                onClick={() => navigate('/projects')}
              >
                <FolderOpen sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
                <Typography variant="h6">Projetos</Typography>
                <Typography variant="body2" color="text.secondary">
                  Gerenciar projetos e consultas
                </Typography>
              </Paper>
              
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { elevation: 4 }
                }}
                onClick={() => navigate('/connections')}
              >
                <Dashboard sx={{ fontSize: 48, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h6">Conexões</Typography>
                <Typography variant="body2" color="text.secondary">
                  Configurar conexões de banco
                </Typography>
              </Paper>
              
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { elevation: 4 }
                }}
                onClick={() => navigate('/queries')}
              >
                <QueryIcon sx={{ fontSize: 48, color: 'warning.main', mb: 1 }} />
                <Typography variant="h6">Queries</Typography>
                <Typography variant="body2" color="text.secondary">
                  Gerenciar consultas SQL
                </Typography>
              </Paper>
              
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 3, 
                  textAlign: 'center', 
                  cursor: 'pointer',
                  '&:hover': { elevation: 4 }
                }}
                onClick={() => console.log('Configurações em breve')}
              >
                <Settings sx={{ fontSize: 48, color: 'success.main', mb: 1 }} />
                <Typography variant="h6">Configurações</Typography>
                <Typography variant="body2" color="text.secondary">
                  Configurações do sistema
                </Typography>
              </Paper>
            </Box>
          </Box>
      </Paper>
    </Layout>
  );
};

export default DashboardPage;
