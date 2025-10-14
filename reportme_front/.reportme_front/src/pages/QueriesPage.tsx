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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
  Storage as QueryIcon,
  PlayArrow as PlayIcon,
  Code as CodeIcon,
  Timer as TimerIcon,
  Memory as CacheIcon,
  Link as ConnectionIcon,
} from '@mui/icons-material';
import { Query, Connection } from '../types';
import { queryService, connectionService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface QueryForm {
  name: string;
  query: string;
  connection_id: number | '';
  timeout: number;
  cache_duration: number;
}

const QueriesPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [queries, setQueries] = useState<Query[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [resultsDialogOpen, setResultsDialogOpen] = useState(false);
  const [editingQuery, setEditingQuery] = useState<Query | null>(null);
  const [queryToDelete, setQueryToDelete] = useState<Query | null>(null);
  const [queryResults, setQueryResults] = useState<any>(null);
  
  // Form state
  const [formData, setFormData] = useState<QueryForm>({
    name: '',
    query: '',
    connection_id: '',
    timeout: 30,
    cache_duration: 0,
  });
  
  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info' | 'warning',
  });

  // Carregar dados
  const loadData = async () => {
    try {
      setLoading(true);
      
      const [queriesResponse, connectionsResponse] = await Promise.all([
        queryService.getAll(),
        connectionService.getAll()
      ]);
      
      const queriesList = queriesResponse.results || queriesResponse;
      const connectionsList = connectionsResponse.results || connectionsResponse;
      
      setQueries(Array.isArray(queriesList) ? queriesList : []);
      setConnections(Array.isArray(connectionsList) ? connectionsList : []);
      
      setError(null);
    } catch (err) {
      console.error('Erro ao carregar dados:', err);
      setError('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Abrir dialog para nova query
  const handleNewQuery = () => {
    setEditingQuery(null);
    setFormData({
      name: '',
      query: '',
      connection_id: '',
      timeout: 30,
      cache_duration: 0,
    });
    setDialogOpen(true);
  };

  // Abrir dialog para editar query
  const handleEditQuery = (query: Query) => {
    console.log('Editando query:', query);
    setEditingQuery(query);
    setFormData({
      name: query.name || '',
      query: query.query || '',
      connection_id: query.connection_id || '',
      timeout: query.timeout || 30,
      cache_duration: query.cache_duration || 0,
    });
    setDialogOpen(true);
  };

  // Salvar query (criar ou editar)
  const handleSaveQuery = async () => {
    try {
      if (!formData.name?.trim()) {
        setSnackbar({
          open: true,
          message: 'Nome da query é obrigatório',
          severity: 'error',
        });
        return;
      }

      if (!formData.query?.trim()) {
        setSnackbar({
          open: true,
          message: 'SQL da query é obrigatório',
          severity: 'error',
        });
        return;
      }

      if (!formData.connection_id || String(formData.connection_id).trim() === '' || Number(formData.connection_id) === 0) {
        setSnackbar({
          open: true,
          message: 'Conexão é obrigatória',
          severity: 'error',
        });
        return;
      }

      const dataToSave = {
        name: formData.name.trim(),
        query: formData.query.trim(),
        connection_id: Number(formData.connection_id),
        timeout: Number(formData.timeout) || 30,
        cache_duration: Number(formData.cache_duration) || 0,
      };

      console.log('Dados sendo enviados para o backend:', dataToSave);

      if (editingQuery) {
        await queryService.update(editingQuery.id, dataToSave);
        setSnackbar({
          open: true,
          message: 'Query atualizada com sucesso!',
          severity: 'success',
        });
      } else {
        await queryService.create(dataToSave);
        setSnackbar({
          open: true,
          message: 'Query criada com sucesso!',
          severity: 'success',
        });
      }
      
      setDialogOpen(false);
      await loadData();
    } catch (err) {
      console.error('Erro ao salvar query:', err);
      
      let errorMessage = 'Erro ao salvar query';
      if ((err as any)?.response?.data) {
        console.log('Detalhes do erro do backend:', (err as any).response.data);
        
        // Processar diferentes tipos de erro
        const errorData = (err as any).response.data;
        
        if (errorData.non_field_errors) {
          errorMessage = errorData.non_field_errors.join(', ');
        } else if (errorData.connection) {
          errorMessage = `Conexão: ${errorData.connection.join(', ')}`;
        } else if (errorData.connection_id) {
          errorMessage = `Connection ID: ${errorData.connection_id.join(', ')}`;
        } else if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else {
          errorMessage = JSON.stringify(errorData);
        }
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
  const handleDeleteClick = (query: Query) => {
    setQueryToDelete(query);
    setDeleteDialogOpen(true);
  };

  // Deletar query
  const handleDeleteQuery = async () => {
    if (!queryToDelete) return;

    try {
      await queryService.delete(queryToDelete.id);
      
      setSnackbar({
        open: true,
        message: 'Query excluída com sucesso!',
        severity: 'success',
      });
      setDeleteDialogOpen(false);
      setQueryToDelete(null);
      
      await loadData();
    } catch (err) {
      console.error('Erro ao excluir query:', err);
      
      let errorMessage = 'Erro ao excluir query';
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

  // Executar query
  const handleExecuteQuery = async (query: Query) => {
    try {
      setSnackbar({
        open: true,
        message: `Executando query "${query.name}"...`,
        severity: 'info',
      });

      const result = await queryService.execute(query.id);
      
      setQueryResults({
        query: query,
        ...result
      });
      setResultsDialogOpen(true);
      
      setSnackbar({
        open: true,
        message: `Query executada com sucesso! ${result.total_records || 0} registros retornados.`,
        severity: 'success',
      });
      
    } catch (err) {
      console.error('Erro ao executar query:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao executar query. Verifique os logs.',
        severity: 'error',
      });
    }
  };

  // Fechar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Obter nome da conexão
  const getConnectionName = (connectionId: number): string => {
    const connection = connections.find(c => c.id === connectionId);
    return connection ? connection.name : 'Conexão não encontrada';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Carregando queries...</Typography>
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
        <Typography color="text.primary">Queries</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" sx={{ display: 'flex', alignItems: 'center' }}>
            <QueryIcon sx={{ mr: 1 }} />
            Gerenciamento de Queries
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {queries.length} {queries.length === 1 ? 'query' : 'queries'} disponíveis
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleNewQuery}
        >
          Nova Query
        </Button>
      </Box>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Queries Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Nome</strong></TableCell>
              <TableCell><strong>Conexão</strong></TableCell>
              <TableCell><strong>Timeout</strong></TableCell>
              <TableCell><strong>Cache</strong></TableCell>
              <TableCell><strong>Criado por</strong></TableCell>
              <TableCell align="center"><strong>Ações</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {queries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Box sx={{ py: 4 }}>
                    <QueryIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      Nenhuma query encontrada
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      Comece criando sua primeira query SQL.
                    </Typography>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleNewQuery}
                    >
                      Criar Primeira Query
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              queries.map((query) => (
                <TableRow key={query.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {query.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {query.id}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={<ConnectionIcon />}
                      label={getConnectionName(query.connection_id)}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={<TimerIcon />}
                      label={`${query.timeout || 30}s`}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={<CacheIcon />}
                      label={query.cache_duration ? `${query.cache_duration}s` : 'Sem cache'}
                      size="small"
                      variant="outlined"
                      color={query.cache_duration ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {query.created_by_name || `ID: ${query.created_by}`}
                    </Typography>
                    {query.created_at && (
                      <Typography variant="caption" color="text.secondary">
                        {new Date(query.created_at).toLocaleDateString('pt-BR')}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => handleExecuteQuery(query)}
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
                      <IconButton
                        size="small"
                        onClick={() => handleEditQuery(query)}
                        title="Editar Query"
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
                        onClick={() => handleDeleteClick(query)}
                        title="Excluir Query"
                        color="error"
                        sx={{ 
                          '&:hover': { 
                            backgroundColor: 'error.main',
                            color: 'error.contrastText',
                          }
                        }}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog para criar/editar query */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CodeIcon sx={{ mr: 1 }} />
            {editingQuery ? 'Editar Query' : 'Nova Query'}
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 1 }}>
            {/* Nome da Query */}
            <Box sx={{ mb: 2 }}>
              <TextField
                autoFocus
                label="Nome da Query"
                fullWidth
                variant="outlined"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ex: Relatório de vendas mensais"
              />
            </Box>
            
            {/* Conexão e configurações */}
            <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: '1 1 300px', minWidth: '300px' }}>
                <FormControl fullWidth>
                  <InputLabel id="connection-select-label">Conexão</InputLabel>
                  <Select
                    labelId="connection-select-label"
                    value={formData.connection_id}
                    label="Conexão"
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      connection_id: e.target.value as number
                    })}
                  >
                    {connections.map((connection) => (
                      <MenuItem key={connection.id} value={connection.id}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <ConnectionIcon sx={{ mr: 1, fontSize: 16 }} />
                          {connection.name} - {connection.sgbd || connection.type}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
              
              <Box sx={{ flex: '0 0 150px' }}>
                <TextField
                  label="Timeout (segundos)"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={formData.timeout}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    timeout: parseInt(e.target.value) || 30 
                  })}
                  inputProps={{ min: 1, max: 300 }}
                />
              </Box>
              
              <Box sx={{ flex: '0 0 150px' }}>
                <TextField
                  label="Cache (segundos)"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={formData.cache_duration}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    cache_duration: parseInt(e.target.value) || 0 
                  })}
                  inputProps={{ min: 0, max: 3600 }}
                  helperText="0 = sem cache"
                />
              </Box>
            </Box>
            
            {/* SQL Query */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Consulta SQL
              </Typography>
              <TextField
                multiline
                rows={12}
                fullWidth
                variant="outlined"
                value={formData.query}
                onChange={(e) => setFormData({ ...formData, query: e.target.value })}
                placeholder="SELECT * FROM tabela WHERE condicao = 'valor'"
                sx={{
                  '& .MuiInputBase-input': {
                    fontFamily: 'monospace',
                    fontSize: '14px',
                  }
                }}
              />
            </Box>
          </Box>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>💡 Dicas:</strong>
              <br />
              • Use parâmetros com <code>:nome_parametro</code> para queries dinâmicas
              <br />
              • Timeout padrão é 30 segundos
              <br />
              • Cache de 0 segundos significa sem cache
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSaveQuery}
            variant="contained"
            disabled={
              !formData.name?.trim() || 
              !formData.query?.trim() || 
              !formData.connection_id || 
              String(formData.connection_id).trim() === '' || 
              Number(formData.connection_id) === 0
            }
          >
            {editingQuery ? 'Atualizar' : 'Criar'}
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
            Tem certeza que deseja excluir a query "<strong>{queryToDelete?.name}</strong>"?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              Esta ação não pode ser desfeita. Todos os nós de projeto que usam esta query 
              ficarão sem query associada.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleDeleteQuery}
            color="error"
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            Excluir
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para exibir resultados da query */}
      <Dialog open={resultsDialogOpen} onClose={() => setResultsDialogOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <PlayIcon sx={{ mr: 1, color: 'success.main' }} />
              Resultados da Query: {queryResults?.query?.name}
            </Box>
            <Button
              onClick={() => setResultsDialogOpen(false)}
              color="inherit"
              size="small"
            >
              ✕
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          {queryResults && (
            <Box>
              {/* Informações da execução */}
              <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: 1, borderColor: 'divider' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Informações da Execução
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Chip
                    icon={<TimerIcon />}
                    label={`${queryResults.execution_time_ms || 0}ms`}
                    size="small"
                    color="primary"
                  />
                  <Chip
                    icon={<CodeIcon />}
                    label={`${queryResults.total_records || 0} registros`}
                    size="small"
                    color="success"
                  />
                  <Chip
                    icon={<ConnectionIcon />}
                    label={getConnectionName(queryResults.query.connection_id)}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>

              {/* Tabela de resultados */}
              {queryResults.columns && queryResults.rows ? (
                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                  <Table stickyHeader>
                    <TableHead>
                      <TableRow>
                        {queryResults.columns.map((column: string, index: number) => (
                          <TableCell key={index}>
                            <Typography variant="subtitle2" fontWeight="bold">
                              {column}
                            </Typography>
                          </TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {queryResults.rows.map((row: any[], rowIndex: number) => (
                        <TableRow key={rowIndex} hover>
                          {row.map((cell: any, cellIndex: number) => (
                            <TableCell key={cellIndex}>
                              {cell === null ? (
                                <Typography variant="body2" color="text.secondary" fontStyle="italic">
                                  NULL
                                </Typography>
                              ) : (
                                <Typography variant="body2">
                                  {String(cell)}
                                </Typography>
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  Nenhum resultado retornado pela query.
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResultsDialogOpen(false)}>
            Fechar
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

export default QueriesPage;
