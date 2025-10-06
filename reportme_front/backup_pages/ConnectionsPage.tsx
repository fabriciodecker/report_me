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
  Grid,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { Connection } from '../types';
import { connectionService } from '../services/api';
import Layout from '../components/Layout';

const ConnectionsPage: React.FC = () => {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingConnection, setEditingConnection] = useState<Connection | null>(null);
  
  // Form state
  const [form, setForm] = useState({
    name: '',
    database: '',
    host: '',
    user: '',
    password: '',
    type: 'postgresql' as Connection['type'],
  });
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState<number | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [testResults, setTestResults] = useState<Record<number, { success: boolean; message: string; connectionTime?: number }>>({});

  const dbTypes = [
    { value: 'postgresql', label: 'PostgreSQL' },
    { value: 'sqlserver', label: 'SQL Server' },
    { value: 'sqlite', label: 'SQLite' },
    { value: 'oracle', label: 'Oracle' },
  ];

  // Load connections on mount
  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await connectionService.getAll();
      setConnections(response.results);
    } catch (error) {
      showSnackbar('Erro ao carregar conexões', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  const resetForm = () => {
    setForm({
      name: '',
      database: '',
      host: '',
      user: '',
      password: '',
      type: 'postgresql',
    });
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      if (editingConnection) {
        await connectionService.update(editingConnection.id, form);
        showSnackbar('Conexão atualizada com sucesso!', 'success');
      } else {
        await connectionService.create(form);
        showSnackbar('Conexão criada com sucesso!', 'success');
      }
      await loadConnections();
      setDialogOpen(false);
      setEditingConnection(null);
      resetForm();
    } catch (error) {
      showSnackbar('Erro ao salvar conexão', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedConnection) return;
    
    try {
      setLoading(true);
      await connectionService.delete(selectedConnection.id);
      showSnackbar('Conexão excluída com sucesso!', 'success');
      setDeleteDialogOpen(false);
      setSelectedConnection(null);
      await loadConnections();
    } catch (error) {
      showSnackbar('Erro ao excluir conexão', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async (connection: Connection) => {
    try {
      setTestLoading(connection.id);
      const result = await connectionService.test(connection.id);
      setTestResults(prev => ({
        ...prev,
        [connection.id]: result
      }));
      
      if (result.success) {
        showSnackbar(`Conexão testada com sucesso! Tempo: ${result.connection_time}ms`, 'success');
      } else {
        showSnackbar(`Falha no teste: ${result.message}`, 'error');
      }
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [connection.id]: { success: false, message: 'Erro ao testar conexão' }
      }));
      showSnackbar('Erro ao testar conexão', 'error');
    } finally {
      setTestLoading(null);
    }
  };

  const handleEdit = (connection: Connection) => {
    setEditingConnection(connection);
    setForm({
      name: connection.name,
      database: connection.database,
      host: connection.host,
      user: connection.user,
      password: '', // Não preencher senha por segurança
      type: connection.type,
    });
    setDialogOpen(true);
  };

  const getTypeLabel = (type: string) => {
    return dbTypes.find(t => t.value === type)?.label || type;
  };

  const getStatusColor = (connection: Connection) => {
    const result = testResults[connection.id];
    if (!result) return 'default';
    return result.success ? 'success' : 'error';
  };

  const getStatusIcon = (connection: Connection) => {
    const result = testResults[connection.id];
    if (testLoading === connection.id) return <CircularProgress size={16} />;
    if (!result) return null;
    return result.success ? <SuccessIcon /> : <ErrorIcon />;
  };

  return (
    <Layout>
      <Box sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Conexões de Banco de Dados
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetForm();
              setDialogOpen(true);
            }}
          >
            Nova Conexão
          </Button>
        </Box>

        {loading && connections.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            {connections.map((connection) => (
              <Card key={connection.id} sx={{ minWidth: 300, flex: '1 1 300px' }}>
                <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" component="h2" gutterBottom>
                          {connection.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {connection.host} / {connection.database}
                        </Typography>
                        <Chip
                          label={getTypeLabel(connection.type)}
                          size="small"
                          color="primary"
                          variant="outlined"
                          sx={{ mb: 1 }}
                        />
                        <br />
                        <Chip
                          label={testResults[connection.id] ? (testResults[connection.id].success ? 'Conectado' : 'Falha') : 'Não testado'}
                          size="small"
                          color={getStatusColor(connection)}
                          variant="outlined"
                          icon={getStatusIcon(connection) || undefined}
                        />
                      </Box>
                      <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(connection)}
                          sx={{ mb: 1 }}
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedConnection(connection);
                            setDeleteDialogOpen(true);
                          }}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Box>
                    </Box>
                    
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<TestIcon />}
                        onClick={() => handleTestConnection(connection)}
                        disabled={testLoading === connection.id}
                        fullWidth
                      >
                        {testLoading === connection.id ? 'Testando...' : 'Testar'}
                      </Button>
                    </Box>

                    {testResults[connection.id] && (
                      <Alert
                        severity={testResults[connection.id].success ? 'success' : 'error'}
                        sx={{ mt: 2 }}
                      >
                        {testResults[connection.id].message}
                        {testResults[connection.id].connectionTime && (
                          <Typography variant="caption" display="block">
                            Tempo de resposta: {testResults[connection.id].connectionTime}ms
                          </Typography>
                        )}
                      </Alert>
                    )}
                  </CardContent>
                </Card>
            ))}
          </Box>
        )}

        {connections.length === 0 && !loading && (
          <Card>
            <CardContent>
              <Typography color="text.secondary" align="center" sx={{ py: 8 }}>
                Nenhuma conexão encontrada. Clique em "Nova Conexão" para começar.
              </Typography>
            </CardContent>
          </Card>
        )}

        {/* Dialog para Conexão */}
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingConnection ? 'Editar Conexão' : 'Nova Conexão'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Nome"
                  fullWidth
                  variant="outlined"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  label="Tipo"
                  fullWidth
                  variant="outlined"
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value as Connection['type'] })}
                >
                  {dbTypes.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Host"
                  fullWidth
                  variant="outlined"
                  value={form.host}
                  onChange={(e) => setForm({ ...form, host: e.target.value })}
                  placeholder="localhost"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Banco de Dados"
                  fullWidth
                  variant="outlined"
                  value={form.database}
                  onChange={(e) => setForm({ ...form, database: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Usuário"
                  fullWidth
                  variant="outlined"
                  value={form.user}
                  onChange={(e) => setForm({ ...form, user: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Senha"
                  type="password"
                  fullWidth
                  variant="outlined"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder={editingConnection ? "Deixe em branco para manter a atual" : ""}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
            <Button 
              onClick={handleSubmit} 
              variant="contained" 
              disabled={!form.name || !form.host || !form.database || !form.user || loading}
            >
              {editingConnection ? 'Atualizar' : 'Criar'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Dialog de Confirmação de Exclusão */}
        <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
          <DialogTitle>Confirmar Exclusão</DialogTitle>
          <DialogContent>
            <Typography>
              Tem certeza que deseja excluir a conexão "{selectedConnection?.name}"?
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

export default ConnectionsPage;
