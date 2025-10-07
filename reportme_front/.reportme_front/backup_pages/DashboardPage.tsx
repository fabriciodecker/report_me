import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  AccountTree as ProjectIcon,
  Storage as ConnectionIcon,
  Code as QueryIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { Project, Connection, Query } from '../types';
import { projectService, connectionService, queryService, authService } from '../services/api';
import Layout from '../components/Layout';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    projectsCount: 0,
    connectionsCount: 0,
    queriesCount: 0,
  });
  const [recentProjects, setRecentProjects] = useState<Project[]>([]);
  const [recentQueries, setRecentQueries] = useState<Query[]>([]);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load user profile
      const userProfile = await authService.getProfile();
      setUser(userProfile);

      // Load statistics
      const [projectsRes, connectionsRes, queriesRes] = await Promise.all([
        projectService.getAll(),
        connectionService.getAll(),
        queryService.getAll(),
      ]);

      setStats({
        projectsCount: projectsRes.count || projectsRes.results.length,
        connectionsCount: connectionsRes.count || connectionsRes.results.length,
        queriesCount: queriesRes.count || queriesRes.results.length,
      });

      // Set recent items (first 5)
      setRecentProjects(projectsRes.results.slice(0, 5));
      setRecentQueries(queriesRes.results.slice(0, 5));
      
    } catch (error) {
      console.error('Erro ao carregar dados do dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const StatCard: React.FC<{
    title: string;
    value: number;
    icon: React.ReactNode;
    color: string;
    onClick: () => void;
  }> = ({ title, value, icon, color, onClick }) => (
    <Card 
      sx={{ 
        cursor: 'pointer',
        transition: 'transform 0.2s',
        '&:hover': { transform: 'translateY(-2px)' },
        minWidth: 250,
        mb: 2
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="h2">
              {value}
            </Typography>
          </Box>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout>
      <Box sx={{ flexGrow: 1 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Bem-vindo ao ReportMe, {user?.username}!
          </Typography>
        </Box>

        {/* Statistics Cards */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
          <StatCard
            title="Projetos"
            value={stats.projectsCount}
            icon={<ProjectIcon />}
            color="#1976d2"
            onClick={() => navigate('/projects')}
          />
          <StatCard
            title="Conexões"
            value={stats.connectionsCount}
            icon={<ConnectionIcon />}
            color="#388e3c"
            onClick={() => navigate('/connections')}
          />
          <StatCard
            title="Consultas"
            value={stats.queriesCount}
            icon={<QueryIcon />}
            color="#f57c00"
            onClick={() => navigate('/queries')}
          />
        </Box>

        {/* Quick Actions */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Ações Rápidas
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<ProjectIcon />}
                onClick={() => navigate('/projects')}
              >
                Novo Projeto
              </Button>
              <Button
                variant="outlined"
                startIcon={<ConnectionIcon />}
                onClick={() => navigate('/connections')}
              >
                Nova Conexão
              </Button>
              <Button
                variant="outlined"
                startIcon={<QueryIcon />}
                onClick={() => navigate('/queries')}
              >
                Nova Consulta
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Recent Items */}
        <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 4 }}>
          {/* Recent Projects */}
          <Card sx={{ flex: 1, minWidth: 300 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Projetos Recentes</Typography>
                <Button size="small" onClick={() => navigate('/projects')}>
                  Ver Todos
                </Button>
              </Box>
              
              {recentProjects.length > 0 ? (
                <List>
                  {recentProjects.map((project, index) => (
                    <React.Fragment key={project.id}>
                      <ListItem 
                        sx={{ cursor: 'pointer', px: 0 }}
                        onClick={() => navigate('/projects')}
                      >
                        <ListItemIcon>
                          <ProjectIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary={project.name}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {project.description || 'Sem descrição'}
                              </Typography>
                              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                                <Chip
                                  label={`${project.node_count || 0} nós`}
                                  size="small"
                                  variant="outlined"
                                />
                                <Chip
                                  label={`${project.query_count || 0} consultas`}
                                  size="small"
                                  variant="outlined"
                                />
                              </Box>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < recentProjects.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Typography color="text.secondary" align="center" sx={{ py: 2 }}>
                  Nenhum projeto encontrado
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Recent Queries */}
          <Card sx={{ flex: 1, minWidth: 300 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Consultas Recentes</Typography>
                <Button size="small" onClick={() => navigate('/queries')}>
                  Ver Todas
                </Button>
              </Box>
              
              {recentQueries.length > 0 ? (
                <List>
                  {recentQueries.map((query, index) => (
                    <React.Fragment key={query.id}>
                      <ListItem 
                        sx={{ cursor: 'pointer', px: 0 }}
                        onClick={() => navigate('/queries')}
                      >
                        <ListItemIcon>
                          <QueryIcon />
                        </ListItemIcon>
                        <ListItemText
                          primary={query.name}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {query.connection?.name || 'Conexão não encontrada'}
                              </Typography>
                              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                                <Chip
                                  label={`${query.parameters?.length || 0} parâmetros`}
                                  size="small"
                                  variant="outlined"
                                />
                              </Box>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < recentQueries.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Typography color="text.secondary" align="center" sx={{ py: 2 }}>
                  Nenhuma consulta encontrada
                </Typography>
              )}
            </CardContent>
          </Card>
        </Box>

        {/* User Info */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Informações do Usuário
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <PersonIcon />
              </Avatar>
              <Box>
                <Typography variant="subtitle1">
                  {user?.username}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {user?.email}
                </Typography>
                <Chip
                  label={user?.is_staff ? 'Administrador' : 'Usuário'}
                  size="small"
                  color={user?.is_staff ? 'primary' : 'default'}
                  sx={{ mt: 1 }}
                />
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Layout>
  );
};

export default DashboardPage;
