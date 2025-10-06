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
  IconButton,
  TextField,
  Typography,
  Alert,
  Snackbar,
  MenuItem,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as ExecuteIcon,
  CheckCircle as ValidateIcon,
  FileCopy as DuplicateIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { Query, Connection, Parameter } from '../types';
import { queryService, connectionService } from '../services/api';
import Layout from '../components/Layout';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const QueriesPage: React.FC = () => {
  const [queries, setQueries] = useState<Query[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedQuery, setSelectedQuery] = useState<Query | null>(null);
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false);
  const [editingQuery, setEditingQuery] = useState<Query | null>(null);
  
  // Form state
  const [form, setForm] = useState({
    name: '',
    query: '',
    connection_id: '',
  });
  
  // Execution states
  const [executionParameters, setExecutionParameters] = useState<Record<string, any>>({});
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executionLoading, setExecutionLoading] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [tabValue, setTabValue] = useState(0);

  // Load data on mount
  useEffect(() => {
    loadQueries();
    loadConnections();
  }, []);

  const loadQueries = async () => {
    try {
      setLoading(true);
      const response = await queryService.getAll();
      setQueries(response.results);
    } catch (error) {
      showSnackbar('Erro ao carregar consultas', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadConnections = async () => {
    try {
      const response = await connectionService.getAll();
      setConnections(response.results);
    } catch (error) {
      showSnackbar('Erro ao carregar conexões', 'error');
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const resetForm = () => {
    setForm({
      name: '',
      query: '',
      connection_id: '',
    });
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      const queryData = {
        ...form,
        connection_id: parseInt(form.connection_id),
      };
      
      if (editingQuery) {
        await queryService.update(editingQuery.id, queryData);
        showSnackbar('Consulta atualizada com sucesso!', 'success');
      } else {
        await queryService.create(queryData);
        showSnackbar('Consulta criada com sucesso!', 'success');
      }
      await loadQueries();
      setDialogOpen(false);
      setEditingQuery(null);
      resetForm();
    } catch (error) {
      showSnackbar('Erro ao salvar consulta', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedQuery) return;
    
    try {
      setLoading(true);
      await queryService.delete(selectedQuery.id);
      showSnackbar('Consulta excluída com sucesso!', 'success');
      setDeleteDialogOpen(false);
      setSelectedQuery(null);
      await loadQueries();
    } catch (error) {
      showSnackbar('Erro ao excluir consulta', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!selectedQuery) return;
    
    try {
      setExecutionLoading(true);
      const result = await queryService.execute(selectedQuery.id, executionParameters);
      setExecutionResult(result);
      setTabValue(1); // Switch to results tab
      showSnackbar('Consulta executada com sucesso!', 'success');
    } catch (error) {
      showSnackbar('Erro ao executar consulta', 'error');
      setExecutionResult({ error: 'Erro ao executar consulta' });
    } finally {
      setExecutionLoading(false);
    }
  };

  const handleValidate = async (query: Query) => {
    try {
      const result = await queryService.validate(query.id);
      setValidationResult(result);
      showSnackbar(result.valid ? 'Consulta válida!' : 'Consulta inválida', result.valid ? 'success' : 'error');
    } catch (error) {
      showSnackbar('Erro ao validar consulta', 'error');
    }
  };

  const handleDuplicate = async (query: Query) => {
    try {
      await queryService.duplicate(query.id);
      showSnackbar('Consulta duplicada com sucesso!', 'success');
      await loadQueries();
    } catch (error) {
      showSnackbar('Erro ao duplicar consulta', 'error');
    }
  };

  const handleEdit = (query: Query) => {
    setEditingQuery(query);
    setForm({
      name: query.name,
      query: query.query,
      connection_id: query.connection_id.toString(),
    });
    setDialogOpen(true);
  };

  const handleExecuteDialog = (query: Query) => {
    setSelectedQuery(query);
    // Reset execution parameters based on query parameters
    const params: Record<string, any> = {};
    query.parameters?.forEach(param => {
      params[param.name] = param.default_value || '';
    });
    setExecutionParameters(params);
    setExecutionResult(null);
    setExecuteDialogOpen(true);
  };

  const getConnectionName = (connectionId: number) => {
    const connection = connections.find(c => c.id === connectionId);
    return connection?.name || 'Conexão não encontrada';
  };

  const renderParameterInput = (parameter: Parameter) => {
    const value = executionParameters[parameter.name] || '';
    
    switch (parameter.type) {
      case 'boolean':
        return (
          <TextField
            select
            label={parameter.name}
            fullWidth
            value={value}
            onChange={(e) => setExecutionParameters(prev => ({
              ...prev,
              [parameter.name]: e.target.value === 'true'
            }))}
          >
            <MenuItem value="true">Sim</MenuItem>
            <MenuItem value="false">Não</MenuItem>
          </TextField>
        );
      
      case 'date':
        return (
          <TextField
            type="date"
            label={parameter.name}
            fullWidth
            value={value}
            onChange={(e) => setExecutionParameters(prev => ({
              ...prev,
              [parameter.name]: e.target.value
            }))}
            InputLabelProps={{ shrink: true }}
          />
        );
      
      case 'number':
        return (
          <TextField
            type="number"
            label={parameter.name}
            fullWidth
            value={value}
            onChange={(e) => setExecutionParameters(prev => ({
              ...prev,
              [parameter.name]: parseFloat(e.target.value) || 0
            }))}
          />
        );
      
      default:
        return (
          <TextField
            label={parameter.name}
            fullWidth
            value={value}
            onChange={(e) => setExecutionParameters(prev => ({
              ...prev,
              [parameter.name]: e.target.value
            }))}
            placeholder={parameter.default_value}
          />
        );
    }
  };

  return (
    <Layout>
      <Box sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Consultas SQL
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetForm();
              setDialogOpen(true);
            }}
          >
            Nova Consulta
          </Button>
        </Box>

        {loading && queries.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
            {queries.map((query) => (
              <Box key={query.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" component="h2" gutterBottom>
                          {query.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {getConnectionName(query.connection_id)}
                        </Typography>
                        <Chip
                          label={`${query.parameters?.length || 0} parâmetros`}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ mb: 1 }}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(query)}
                          sx={{ mb: 1 }}
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedQuery(query);
                            setDeleteDialogOpen(true);
                          }}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </Box>
                    
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Button
                        variant="contained"
                        size="small"
                        startIcon={<ExecuteIcon />}
                        onClick={() => handleExecuteDialog(query)}
                        fullWidth
                      >
                        Executar
                      </Button>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<ValidateIcon />}
                          onClick={() => handleValidate(query)}
                          sx={{ flex: 1 }}
                        >
                          Validar
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          startIcon={<DuplicateIcon />}
                          onClick={() => handleDuplicate(query)}
                          sx={{ flex: 1 }}
                        >
                          Duplicar
                        </Button>
                      </Box>
                    </Box>

                    {/* Query preview */}
                    <Accordion sx={{ mt: 2 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="caption">Ver SQL</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography
                          variant="body2"
                          component="pre"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            backgroundColor: 'grey.100',
                            p: 1,
                            borderRadius: 1,
                            overflow: 'auto',
                            maxHeight: 200,
                          }}
                        >
                          {query.query}
                        </Typography>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Box>
            ))}
          </Box>
        )}

        {queries.length === 0 && !loading && (
          <Card>
            <CardContent>
              <Typography color="text.secondary" align="center" sx={{ py: 8 }}>
                Nenhuma consulta encontrada. Clique em "Nova Consulta" para começar.
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* Dialog para Consulta */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="lg" fullWidth>
          <DialogTitle>
            {editingQuery ? 'Editar Consulta' : 'Nova Consulta'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' }, gap: 2, mt: 1 }}>
              <Box>
                <TextField
                  label="Nome"
                  fullWidth
                  variant="outlined"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </Box>
              <Box>
                <TextField
                  select
                  label="Conexão"
                  fullWidth
                  variant="outlined"
                  value={form.connection_id}
                  onChange={(e) => setForm({ ...form, connection_id: e.target.value })}
                >
                  {connections.map((connection) => (
                    <MenuItem key={connection.id} value={connection.id}>
                      {connection.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Box>
              <Box sx={{ gridColumn: '1 / -1' }}>
                <TextField
                  label="SQL"
                  fullWidth
                  multiline
                  rows={12}
                  variant="outlined"
                  value={form.query}
                  onChange={(e) => setForm({ ...form, query: e.target.value })}
                  sx={{ fontFamily: 'monospace' }}
                />
              </Box>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button 
              onClick={handleSubmit} 
              variant="contained" 
              disabled={!form.name || !form.query || !form.connection_id || loading}
            >
              {editingQuery ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog de Execução */}
        <Dialog open={executeDialogOpen} onClose={() => setExecuteDialogOpen(false)} maxWidth="xl" fullWidth>
          <DialogTitle>
            Executar Consulta: {selectedQuery?.name}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
                <Tab label="Parâmetros" />
                <Tab label="Resultados" />
              </Tabs>
            </Box>
            
            <TabPanel value={tabValue} index={0}>
              {selectedQuery?.parameters && selectedQuery.parameters.length > 0 ? (
                <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 2 }}>
                  {selectedQuery.parameters.map((parameter) => (
                    <Box key={parameter.id}>
                      {renderParameterInput(parameter)}
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography color="text.secondary">
                  Esta consulta não possui parâmetros.
                </Typography>
              )}
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              {executionResult ? (
                executionResult.error ? (
                  <Alert severity="error">{executionResult.error}</Alert>
                ) : (
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">
                        Resultados ({executionResult.total_records} registros)
                      </Typography>
                      <Box>
                        <Button startIcon={<DownloadIcon />} sx={{ mr: 1 }}>
                          Excel
                        </Button>
                        <Button startIcon={<DownloadIcon />}>
                          CSV
                        </Button>
                      </Box>
                    </Box>
                    
                    <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                      <Table stickyHeader>
                        <TableHead>
                          <TableRow>
                            {executionResult.columns?.map((column: string) => (
                              <TableCell key={column}>{column}</TableCell>
                            ))}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {executionResult.rows?.map((row: any[], index: number) => (
                            <TableRow key={index}>
                              {row.map((cell, cellIndex) => (
                                <TableCell key={cellIndex}>
                                  {cell !== null ? String(cell) : 'NULL'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    
                    <Typography variant="caption" sx={{ mt: 2, display: 'block' }}>
                      Tempo de execução: {executionResult.execution_time}ms
                    </Typography>
                  </Box>
                )
              ) : (
                <Typography color="text.secondary">
                  Execute a consulta para ver os resultados.
                </Typography>
              )}
            </TabPanel>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setExecuteDialogOpen(false)}>Fechar</Button>
            <Button
              onClick={handleExecute}
              variant="contained"
              disabled={executionLoading}
              startIcon={executionLoading ? <CircularProgress size={16} /> : <ExecuteIcon />}
            >
              {executionLoading ? 'Executando...' : 'Executar'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog de Confirmação de Exclusão */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Confirmar Exclusão</DialogTitle>
          <DialogContent>
            <Typography>
              Tem certeza que deseja excluir a consulta "{selectedQuery?.name}"?
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
            <Button
              onClick={handleDelete}
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

export default QueriesPage;
