import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService } from '../services/api';
import { Project, ProjectNode } from '../types';
import Layout from '../components/Layout';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Breadcrumbs,
  Link,
  Card,
  CardContent,
  IconButton,
  Chip
} from '@mui/material';
import {
  ArrowBack,
  Folder,
  Description,
  QueryStats,
  PlayArrow
} from '@mui/icons-material';

const ReaderProjectTreePage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [nodes, setNodes] = useState<ProjectNode[]>([]);
  const [currentNode, setCurrentNode] = useState<ProjectNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const loadProject = async () => {
      try {
        setLoading(true);
        console.log('Carregando projeto:', projectId);
        
        // Carregar dados do projeto
        const projectData = await projectService.getById(Number(projectId));
        setProject(projectData);
        
        // Carregar árvore do projeto
        const treeData = await projectService.getTree(Number(projectId));
        setNodes(treeData);
        
        // Definir nó raiz como atual se existir
        const rootNode = treeData.find(node => !node.parent && !node.parent_id);
        if (rootNode) {
          setCurrentNode(rootNode);
        }
        
        setError(null);
      } catch (err: any) {
        console.error('Erro ao carregar projeto:', err);
        setError(err.response?.data?.detail || err.message || 'Erro ao carregar projeto');
      } finally {
        setLoading(false);
      }
    };

    loadProject();
  }, [projectId]);

  const getNodeChildren = (parentId?: number) => {
    return nodes.filter(node => (node.parent || node.parent_id) === parentId);
  };

  const getBreadcrumbs = (node: ProjectNode | null): ProjectNode[] => {
    if (!node) return [];
    
    const breadcrumbs: ProjectNode[] = [];
    let current: ProjectNode | null = node;
    
    while (current) {
      breadcrumbs.unshift(current);
      const parentId: number | undefined = current.parent || current.parent_id;
      current = parentId ? nodes.find(n => n.id === parentId) || null : null;
    }
    
    return breadcrumbs;
  };

  const handleNodeClick = (node: ProjectNode) => {
    setCurrentNode(node);
  };

  const handleExecuteQuery = (node: ProjectNode) => {
    if (node.query) {
      navigate(`/reader/execute-query/${node.query}`);
    }
  };

  const handleBackToProjects = () => {
    navigate('/reader');
  };

  if (loading) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout>
        <Alert severity="warning" sx={{ m: 2 }}>
          Projeto não encontrado
        </Alert>
      </Layout>
    );
  }

  const breadcrumbs = getBreadcrumbs(currentNode);
  const children = getNodeChildren(currentNode?.id);

  return (
    <Layout>
      <Paper sx={{ p: 3 }}>
        {/* Header com navegação */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <IconButton onClick={handleBackToProjects} sx={{ mr: 2 }}>
            <ArrowBack />
          </IconButton>
          <Box>
            <Typography variant="h4">
              {project.name}
            </Typography>
            {project.description && (
              <Typography variant="body2" color="text.secondary">
                {project.description}
              </Typography>
            )}
          </Box>
        </Box>

        {/* Breadcrumbs */}
        {breadcrumbs.length > 0 && (
          <Breadcrumbs sx={{ mb: 3 }}>
            <Link 
              color="inherit" 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                setCurrentNode(null);
              }}
            >
              {project.name}
            </Link>
            {breadcrumbs.map((node, index) => (
              <Link
                key={node.id}
                color={index === breadcrumbs.length - 1 ? "text.primary" : "inherit"}
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  if (index < breadcrumbs.length - 1) {
                    setCurrentNode(node);
                  }
                }}
              >
                {node.name}
              </Link>
            ))}
          </Breadcrumbs>
        )}

        {/* Título da seção atual */}
        <Typography variant="h5" gutterBottom>
          {currentNode ? `Conteúdo de: ${currentNode.name}` : 'Conteúdo do Projeto'}
        </Typography>

        {/* Lista de nós filhos */}
        {children.length === 0 ? (
          <Alert severity="info">
            {currentNode ? 'Este nó não possui subitens.' : 'Este projeto não possui nós configurados.'}
          </Alert>
        ) : (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            {children.map((node) => (
              <Box key={node.id} sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <Card 
                  sx={{ 
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 4,
                    }
                  }}
                  onClick={() => {
                    if (node.query) {
                      handleExecuteQuery(node);
                    } else {
                      handleNodeClick(node);
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {node.query ? (
                        <QueryStats color="primary" sx={{ mr: 1 }} />
                      ) : (
                        <Folder color="action" sx={{ mr: 1 }} />
                      )}
                      <Typography 
                        variant="h6" 
                        component="div"
                        sx={{
                          color: node.query ? 'primary.main' : 'inherit',
                          '&:hover': {
                            textDecoration: node.query ? 'underline' : 'none'
                          }
                        }}
                      >
                        {node.name}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Box>
                        {node.query ? (
                          <Chip 
                            label="Clique para executar" 
                            color="primary" 
                            size="small"
                            icon={<Description />}
                          />
                        ) : (
                          <Chip 
                            label="Pasta" 
                            color="default" 
                            size="small"
                            icon={<Folder />}
                          />
                        )}
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </Box>
        )}
      </Paper>
    </Layout>
  );
};

export default ReaderProjectTreePage;