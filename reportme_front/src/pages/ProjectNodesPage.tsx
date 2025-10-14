import React, { useState, useEffect } from 'react';
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
  Paper,
  Breadcrumbs,
  Link,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Collapse,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
  FolderOpen as FolderIcon,
  InsertDriveFile as FileIcon,
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Folder as FolderClosedIcon,
  AccountTree as TreeIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material';
import { ProjectNode, Project, Query } from '../types';
import { projectNodeService, projectService, queryService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useParams } from 'react-router-dom';

interface NodeForm {
  name: string;
  parent_id?: number;
  query_id?: number;
}

const ProjectNodesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  
  const [project, setProject] = useState<Project | null>(null);
  const [nodes, setNodes] = useState<ProjectNode[]>([]);
  const [queries, setQueries] = useState<Query[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set());
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<ProjectNode | null>(null);
  const [nodeToDelete, setNodeToDelete] = useState<ProjectNode | null>(null);
  const [selectedParentNode, setSelectedParentNode] = useState<ProjectNode | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<NodeForm>({
    name: '',
    parent_id: undefined,
    query_id: undefined,
  });
  
  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info' | 'warning',
  });

  // Carregar dados
  const loadData = async () => {
    if (!projectId) {
      console.error('ProjectId não encontrado');
      return;
    }
    
    try {
      setLoading(true);
      const projectIdNum = parseInt(projectId);
      console.log('Carregando dados para projeto ID:', projectIdNum);
      
      // Carregar projeto e queries em paralelo
      const [projectData, queriesResponse] = await Promise.all([
        projectService.getById(projectIdNum),
        queryService.getAll()
      ]);
      
      console.log('Projeto carregado:', projectData);
      setProject(projectData);
      
      console.log('Queries carregadas:', queriesResponse);
      const queriesList = queriesResponse.results || queriesResponse;
      setQueries(Array.isArray(queriesList) ? queriesList : []);
      
      // Carregar nós do projeto
      const nodesResponse = await projectNodeService.getAll(projectIdNum);
      console.log('Resposta da API de nós:', nodesResponse);
      
      const nodesList = nodesResponse.results || nodesResponse;
      console.log('Lista de nós processada:', nodesList);
      
      // Filtrar nós apenas deste projeto (garantia adicional)
      const filteredNodes = Array.isArray(nodesList) 
        ? nodesList.filter(node => {
            const nodeProjectId = (node as any).project_id || (node as any).project;
            console.log(`Nó ${node.name} - project_id: ${nodeProjectId}, target: ${projectIdNum}`);
            return !nodeProjectId || nodeProjectId === projectIdNum;
          })
        : [];
      
      console.log('Nós filtrados para o projeto:', filteredNodes);
      setNodes(filteredNodes);
      
      // Expandir automaticamente os nós raiz
      const rootNodeIds = filteredNodes
        .filter(node => !node.parent_id)
        .map(node => node.id);
      setExpandedNodes(new Set(rootNodeIds));
      
      setError(null);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
      setError('Erro ao carregar dados do projeto');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [projectId]);

  // Abrir dialog para novo nó
  const handleNewNode = (parentNode?: ProjectNode) => {
    setEditingNode(null);
    setSelectedParentNode(parentNode || null);
    setFormData({
      name: '',
      parent_id: parentNode?.id,
      query_id: undefined,
    });
    setDialogOpen(true);
  };

  // Abrir dialog para editar nó
  const handleEditNode = (node: ProjectNode) => {
    setEditingNode(node);
    setSelectedParentNode(null);
    setFormData({
      name: node.name,
      parent_id: node.parent_id,
      query_id: node.query_id,
    });
    setDialogOpen(true);
  };

  // Salvar nó (criar ou editar)
  const handleSaveNode = async () => {
    try {
      const projectIdNum = parseInt(projectId!);
      const dataToSave = { 
        ...formData,
        project: projectIdNum, // Usando 'project' como chave
        project_id: projectIdNum // Usando 'project_id' como backup
      };

      console.log('Dados a serem salvos:', dataToSave);

      if (editingNode) {
        // Editar nó existente
        console.log('Editando nó ID:', editingNode.id);
        const response = await projectNodeService.update(editingNode.id, dataToSave);
        console.log('Resposta da edição:', response);
        setSnackbar({
          open: true,
          message: 'Nó atualizado com sucesso!',
          severity: 'success',
        });
      } else {
        // Criar novo nó
        console.log('Criando novo nó');
        const response = await projectNodeService.create(dataToSave);
        console.log('Resposta da criação:', response);
        setSnackbar({
          open: true,
          message: 'Nó criado com sucesso!',
          severity: 'success',
        });
      }
      
      setDialogOpen(false);
      await loadData();
    } catch (err) {
      console.error('Erro ao salvar nó:', err);
      console.error('Response:', (err as any)?.response);
      
      let errorMessage = 'Erro ao salvar nó';
      if ((err as any)?.response?.data?.detail) {
        errorMessage = (err as any).response.data.detail;
      } else if ((err as any)?.response?.data) {
        errorMessage = JSON.stringify((err as any).response.data);
      } else if ((err as any)?.message) {
        errorMessage = (err as any).message;
      }
      
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    }
  };

  // Confirmar exclusão
  const handleDeleteClick = (node: ProjectNode) => {
    setNodeToDelete(node);
    setDeleteDialogOpen(true);
  };

  // Deletar nó
  const handleDeleteNode = async () => {
    if (!nodeToDelete) return;

    try {
      console.log('Tentando excluir nó ID:', nodeToDelete.id);
      console.log('Nó a ser excluído:', nodeToDelete);
      
      const response = await projectNodeService.delete(nodeToDelete.id);
      console.log('Resposta da exclusão:', response);
      
      setSnackbar({
        open: true,
        message: 'Nó excluído com sucesso!',
        severity: 'success',
      });
      setDeleteDialogOpen(false);
      setNodeToDelete(null);
      
      // Recarregar dados após exclusão
      await loadData();
    } catch (err) {
      console.error('Erro detalhado ao excluir nó:', err);
      console.error('Stack trace:', (err as any)?.stack);
      console.error('Response:', (err as any)?.response);
      
      let errorMessage = 'Erro ao excluir nó';
      if ((err as any)?.response?.data?.detail) {
        errorMessage = (err as any).response.data.detail;
      } else if ((err as any)?.message) {
        errorMessage = (err as any).message;
      }
      
      setSnackbar({
        open: true,
        message: errorMessage,
        severity: 'error',
      });
    }
  };

  // Fechar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Alternar expansão de nó
  const toggleNodeExpansion = (nodeId: number) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  // Verificar se nó tem filhos
  const hasChildren = (nodeId: number): boolean => {
    return nodes.some(node => node.parent_id === nodeId);
  };

  // Verificar se nó pode ter query (apenas nós folha)
  const canHaveQuery = (nodeId?: number): boolean => {
    if (!nodeId) return true; // Novo nó pode ter query
    return !hasChildren(nodeId);
  };

  // Verificar se é nó raiz (não pode ser excluído)
  const isRootNode = (node: ProjectNode): boolean => {
    return !node.parent_id && project?.first_node_id === node.id;
  };

  // Renderizar nó individual
  const renderNode = (node: ProjectNode, level: number = 0): React.ReactNode => {
    const children = nodes.filter(n => n.parent_id === node.id);
    const isExpanded = expandedNodes.has(node.id);
    const nodeHasChildren = children.length > 0;

    return (
      <Box key={node.id}>
        {/* Nó principal */}
        <Card 
          sx={{ 
            mb: 1, 
            ml: level * 3,
            border: '1px solid',
            borderColor: 'divider',
            '&:hover': {
              borderColor: 'primary.main',
              boxShadow: 1,
            }
          }}
        >
          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              {/* Lado esquerdo - Ícone de expansão, ícone do tipo e nome */}
              <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                {/* Indicador de nível com linhas */}
                {level > 0 && (
                  <Box sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    mr: 1,
                    color: 'text.disabled',
                  }}>
                    {Array.from({ length: level }, (_, i) => (
                      <Box 
                        key={i}
                        sx={{
                          width: 20,
                          height: 1,
                          borderTop: '1px dashed',
                          borderColor: 'text.disabled',
                          mr: 0.5,
                        }}
                      />
                    ))}
                  </Box>
                )}

                {/* Botão de expansão/contração */}
                {nodeHasChildren ? (
                  <IconButton
                    size="small"
                    onClick={() => toggleNodeExpansion(node.id)}
                    sx={{ mr: 1, p: 0.5 }}
                  >
                    {isExpanded ? <ExpandMoreIcon /> : <ChevronRightIcon />}
                  </IconButton>
                ) : (
                  <Box sx={{ width: 32, mr: 1 }} /> // Espaço para alinhamento
                )}

                {/* Ícone do tipo de nó */}
                {node.query_id ? (
                  <FileIcon sx={{ mr: 1, color: 'success.main' }} />
                ) : nodeHasChildren ? (
                  isExpanded ? (
                    <FolderIcon sx={{ mr: 1, color: 'warning.main' }} />
                  ) : (
                    <FolderClosedIcon sx={{ mr: 1, color: 'warning.main' }} />
                  )
                ) : (
                  <FolderClosedIcon sx={{ mr: 1, color: 'primary.main' }} />
                )}

                {/* Informações do nó */}
                <Box sx={{ flex: 1 }}>
                  <Typography 
                    variant="subtitle2" 
                    fontWeight="bold"
                    sx={{ 
                      color: node.query_id ? 'success.main' : 'text.primary',
                    }}
                  >
                    {node.name}
                    {/* Nome da query ao lado do nome do nó */}
                    {node.query_id && (() => {
                      const query = queries.find(q => q.id === node.query_id);
                      return query ? (
                        <Typography 
                          component="span" 
                          variant="body2" 
                          sx={{ 
                            ml: 1, 
                            color: 'success.main', 
                            fontWeight: 'normal',
                            fontSize: '0.875rem'
                          }}
                        >
                          → {query.name}
                        </Typography>
                      ) : null;
                    })()}
                  </Typography>
                  
                  {/* Informações secundárias */}
                  <Typography variant="caption" color="text.secondary">
                    {node.query_id ? (() => {
                      const query = queries.find(q => q.id === node.query_id);
                      return query?.connection?.name ? `� Conexão: ${query.connection.name}` : '📄 Query associada';
                    })() : nodeHasChildren ? (
                      `📁 Pasta (${children.length} ${children.length === 1 ? 'item' : 'itens'})`
                    ) : (
                      '📂 Nó de organização'
                    )}
                  </Typography>
                </Box>
              </Box>

              {/* Lado direito - Botões de ação */}
              <Box sx={{ display: 'flex', gap: 0.5 }}>
                {/* Botão executar query - apenas para nós com query */}
                {node.query_id && (
                  <IconButton
                    size="small"
                    onClick={() => handleExecuteQuery(node)}
                    title="Executar Query"
                    sx={{ 
                      color: 'success.main',
                      '&:hover': { 
                        backgroundColor: 'success.main',
                        color: 'success.contrastText',
                      }
                    }}
                  >
                    <PlayIcon fontSize="small" />
                  </IconButton>
                )}
                
                <IconButton
                  size="small"
                  onClick={() => handleNewNode(node)}
                  title="Adicionar nó filho"
                  color="primary"
                  disabled={!!node.query_id} // Nós com query não podem ter filhos
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                    }
                  }}
                >
                  <AddIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => handleEditNode(node)}
                  title="Editar nó"
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: 'info.main',
                      color: 'info.contrastText',
                    }
                  }}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => handleDeleteClick(node)}
                  title={isRootNode(node) ? "Nó raiz não pode ser excluído" : "Excluir nó"}
                  color="error"
                  disabled={isRootNode(node)}
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: 'error.main',
                      color: 'error.contrastText',
                    },
                    '&.Mui-disabled': {
                      color: 'text.disabled',
                    }
                  }}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Nós filhos (renderizados condicionalmente se expandido) */}
        <Collapse in={isExpanded && nodeHasChildren}>
          <Box>
            {children.map(child => renderNode(child, level + 1))}
          </Box>
        </Collapse>
      </Box>
    );
  };

  // Renderizar árvore de nós raiz
  const renderNodeTree = (): React.ReactNode => {
    const rootNodes = nodes.filter(node => !node.parent_id);
    
    if (rootNodes.length === 0) return null;

    return (
      <Box>
        {rootNodes.map(node => renderNode(node, 0))}
      </Box>
    );
  };

  // Expandir/colapsar todos os nós
  const handleExpandAll = () => {
    const allNodeIds = new Set(nodes.map(node => node.id));
    setExpandedNodes(allNodeIds);
  };

  const handleCollapseAll = () => {
    setExpandedNodes(new Set());
  };

  // Executar query de um nó
  const handleExecuteQuery = async (node: ProjectNode) => {
    if (!node.query_id) return;

    try {
      setSnackbar({
        open: true,
        message: `Executando query "${node.name}"...`,
        severity: 'info',
      });

      const result = await queryService.execute(node.query_id);
      
      setSnackbar({
        open: true,
        message: `Query executada com sucesso! ${result.total_records || 0} registros retornados.`,
        severity: 'success',
      });

      // Aqui você pode implementar uma modal para mostrar os resultados
      console.log('Resultado da query:', result);
      
    } catch (err) {
      console.error('Erro ao executar query:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao executar query. Verifique os logs.',
        severity: 'error',
      });
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Carregando nós do projeto...</Typography>
      </Box>
    );
  }

  if (!project) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Projeto não encontrado</Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
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
        <Link
          color="inherit"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            navigate('/projects');
          }}
          sx={{ textDecoration: 'none' }}
        >
          Projetos
        </Link>
        <Typography color="text.primary">Nós - {project.name}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
            <TreeIcon sx={{ mr: 1 }} />
            Estrutura do Projeto
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {project.name} • {nodes.length} {nodes.length === 1 ? 'nó' : 'nós'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {nodes.length > 0 && (
            <>
              <Button
                variant="outlined"
                size="small"
                onClick={handleExpandAll}
                startIcon={<ExpandMoreIcon />}
              >
                Expandir Todos
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={handleCollapseAll}
                startIcon={<ChevronRightIcon />}
              >
                Colapsar Todos
              </Button>
            </>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleNewNode()}
          >
            Novo Nó Raiz
          </Button>
        </Box>
      </Box>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Nodes Tree */}
      <Box>
        {nodes.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <TreeIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              Nenhum nó encontrado
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Comece criando o primeiro nó deste projeto para organizar sua estrutura hierárquica.
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleNewNode()}
            >
              Criar Primeiro Nó
            </Button>
          </Paper>
        ) : (
          <Box>
            {/* Indicador de estrutura hierárquica */}
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>📁 Pastas:</strong> Nós de organização que podem conter outros nós
                <br />
                <strong>📄 Arquivos:</strong> Nós com queries associadas
                <br />
                <strong>💡 Dica:</strong> Use os botões ▶/▼ para expandir/colapsar pastas
              </Typography>
            </Alert>
            {renderNodeTree()}
          </Box>
        )}
      </Box>

      {/* Dialog para criar/editar nó */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingNode ? 'Editar Nó' : `Novo Nó${selectedParentNode ? ` (filho de "${selectedParentNode.name}")` : ' Raiz'}`}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nome do Nó"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          {/* Seletor de Query - apenas para nós folha */}
          {canHaveQuery(editingNode?.id) && (
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="query-select-label">Query (Opcional)</InputLabel>
              <Select
                labelId="query-select-label"
                value={formData.query_id || ''}
                label="Query (Opcional)"
                onChange={(e) => setFormData({ 
                  ...formData, 
                  query_id: e.target.value ? Number(e.target.value) : undefined 
                })}
              >
                <MenuItem value="">
                  <em>Nenhuma query (nó de organização)</em>
                </MenuItem>
                {queries.map((query) => (
                  <MenuItem key={query.id} value={query.id}>
                    {query.name} - {query.connection?.name || 'Sem conexão'}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          
          {/* Alertas informativos */}
          {canHaveQuery(editingNode?.id) ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>📁 Nó de organização:</strong> Não selecione query para criar uma pasta que pode conter outros nós.
                <br />
                <strong>📄 Nó com query:</strong> Selecione uma query para criar um nó executável (nó folha).
              </Typography>
            </Alert>
          ) : (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>⚠️ Nó com filhos:</strong> Este nó possui filhos e não pode ter uma query associada.
                <br />
                Apenas nós folha (sem filhos) podem executar queries.
              </Typography>
            </Alert>
          )}
          
          {selectedParentNode && (
            <Alert severity="info" sx={{ mt: 2 }}>
              Este nó será criado como filho de: <strong>{selectedParentNode.name}</strong>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSaveNode}
            variant="contained"
            disabled={!formData.name.trim()}
          >
            {editingNode ? 'Atualizar' : 'Criar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de confirmação para excluir */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <DeleteIcon sx={{ mr: 1, color: 'error.main' }} />
          Confirmar Exclusão
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Tem certeza que deseja excluir o nó "<strong>{nodeToDelete?.name}</strong>"?
          </Typography>
          {nodeToDelete && (
            <>
              {/* Verificar se tem filhos */}
              {(() => {
                const children = nodes.filter(n => n.parent_id === nodeToDelete.id);
                const allDescendants: ProjectNode[] = [];
                
                // Função recursiva para coletar todos os descendentes
                const collectDescendants = (nodeId: number) => {
                  const directChildren = nodes.filter(n => n.parent_id === nodeId);
                  for (const child of directChildren) {
                    allDescendants.push(child);
                    collectDescendants(child.id);
                  }
                };
                
                collectDescendants(nodeToDelete.id);
                
                if (allDescendants.length > 0) {
                  return (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      <Typography variant="body2" gutterBottom>
                        <strong>⚠️ Atenção:</strong> Este nó possui {allDescendants.length} {allDescendants.length === 1 ? 'descendente' : 'descendentes'} que também {allDescendants.length === 1 ? 'será excluído' : 'serão excluídos'}:
                      </Typography>
                      <Box sx={{ ml: 2, mt: 1, maxHeight: 120, overflow: 'auto' }}>
                        {allDescendants.slice(0, 10).map((child) => (
                          <Typography key={child.id} variant="caption" display="block">
                            • {child.name}
                            {child.query_id && (
                              <Box component="span" sx={{ color: 'warning.main', ml: 1 }}>
                                (com query)
                              </Box>
                            )}
                          </Typography>
                        ))}
                        {allDescendants.length > 10 && (
                          <Typography variant="caption" color="text.secondary">
                            ... e mais {allDescendants.length - 10} {allDescendants.length - 10 === 1 ? 'nó' : 'nós'}
                          </Typography>
                        )}
                      </Box>
                      <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                        Esta ação não pode ser desfeita!
                      </Typography>
                    </Alert>
                  );
                } else {
                  return (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        Este é um nó folha (sem filhos). Apenas este nó será excluído.
                      </Typography>
                    </Alert>
                  );
                }
              })()}
              
              {/* Informação sobre nó raiz */}
              {!nodeToDelete.parent_id && (
                <Alert severity="info" sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    <strong>📁 Nó Raiz:</strong> Este é um nó raiz do projeto. Você pode ter múltiplos nós raiz.
                  </Typography>
                </Alert>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleDeleteNode}
            color="error"
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            {nodeToDelete && (() => {
              const children = nodes.filter(n => n.parent_id === nodeToDelete.id);
              const allDescendants: ProjectNode[] = [];
              
              const collectDescendants = (nodeId: number) => {
                const directChildren = nodes.filter(n => n.parent_id === nodeId);
                for (const child of directChildren) {
                  allDescendants.push(child);
                  collectDescendants(child.id);
                }
              };
              
              collectDescendants(nodeToDelete.id);
              
              if (allDescendants.length > 0) {
                return `Excluir Tudo (${allDescendants.length + 1} nós)`;
              } else {
                return 'Excluir';
              }
            })()}
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
    </Box>
  );
};

export default ProjectNodesPage;
