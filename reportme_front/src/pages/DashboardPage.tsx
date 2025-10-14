import React from 'react';
import { Container, Typography, Paper, Box, Button } from '@mui/material';
import { FolderOpen, Dashboard, Settings, Storage as QueryIcon } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <Container maxWidth="lg">
      <Box sx={{ marginTop: 4 }}>
        <Paper elevation={3} sx={{ padding: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h4" component="h1">
              Dashboard - ReportMe
            </Typography>
            <Button variant="outlined" onClick={logout}>
              Sair
            </Button>
          </Box>
          
          <Typography variant="h6" gutterBottom>
            Bem-vindo, {user?.username}!
          </Typography>
          
          <Typography variant="body1" color="textSecondary">
            Sistema de relatórios funcionando! 🎉
          </Typography>
          
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
      </Box>
    </Container>
  );
};

export default DashboardPage;
