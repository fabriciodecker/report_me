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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Home as HomeIcon,
  Cable as ConnectionIcon,
  PlayArrow as TestIcon,
} from '@mui/icons-material';
import { Connection } from '../types';
import { connectionService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface ConnectionForm {
  name: string;
  database: string;
  host: string;
  user: string;
  password: string;
  sgbd: 'sqlite' | 'postgresql' | 'sqlserver' | 'oracle' | 'mysql';
  port?: number;
}

const ConnectionsPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingConnection, setEditingConnection] = useState<Connection | null>(null);
  const [connectionToDelete, setConnectionToDelete] = useState<Connection | null>(null);
  
  // Form state
  const [formData, setFormData] = useState<ConnectionForm>({
    name: '',
    database: '',
    host: '',
    user: '',
    password: '',
    sgbd: 'postgresql',
    port: undefined,
  });
  
  // Test connection state
  const [testingConnections, setTestingConnections] = useState<Set<number>>(new Set());
  
  // Snackbar state
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success' as 'success' | 'error' | 'info',
  });

  // Carregar conexões
  const loadConnections = async () => {
    try {
      setLoading(true);
      const response = await connectionService.getAll();
      console.log('Dados recebidos do backend:', response);
      const connections = response.results || (Array.isArray(response) ? response : []);
      console.log('Primeira conexão:', connections[0]);
      setConnections(connections);
      setError(null);
    } catch (err) {
      console.error('Erro ao carregar conexões:', err);
      setError('Erro ao carregar conexões');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConnections();
  }, []);

  // Abrir dialog para nova conexão
  const handleNewConnection = () => {
    setEditingConnection(null);
    setFormData({
      name: '',
      database: '',
      host: '',
      user: '',
      password: '',
      sgbd: 'postgresql',
      port: undefined,
    });
    setDialogOpen(true);
  };

  // Abrir dialog para editar conexão
  const handleEditConnection = (connection: Connection) => {
    setEditingConnection(connection);
    const dbType = connection.sgbd || connection.type || 'postgresql';
    setFormData({
      name: connection.name,
      database: connection.database,
      host: connection.host,
      user: connection.user,
      password: '', // Não carregar senha por segurança
      sgbd: dbType as ConnectionForm['sgbd'],
      port: undefined, // Assumindo que port não está no tipo atual
    });
    setDialogOpen(true);
  };

  // Salvar conexão (criar ou editar)
  const handleSaveConnection = async () => {
    try {
      const dataToSave = { ...formData };
      
      // Remover campos vazios/undefined
      if (!dataToSave.port) delete (dataToSave as any).port;
      if (!dataToSave.password && editingConnection) delete (dataToSave as any).password;

      if (editingConnection) {
        // Editar conexão existente
        await connectionService.update(editingConnection.id, dataToSave);
        setSnackbar({
          open: true,
          message: 'Conexão atualizada com sucesso!',
          severity: 'success',
        });
      } else {
        // Criar nova conexão
        await connectionService.create(dataToSave);
        setSnackbar({
          open: true,
          message: 'Conexão criada com sucesso!',
          severity: 'success',
        });
      }
      
      setDialogOpen(false);
      loadConnections();
    } catch (err) {
      console.error('Erro ao salvar conexão:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao salvar conexão',
        severity: 'error',
      });
    }
  };

  // Testar conexão
  const handleTestConnection = async (connection: Connection) => {
    setTestingConnections(prev => new Set(prev).add(connection.id));
    
    try {
      const result = await connectionService.test(connection.id);
      setSnackbar({
        open: true,
        message: result.success ? 'Conexão testada com sucesso!' : `Erro na conexão: ${result.message}`,
        severity: result.success ? 'success' : 'error',
      });
    } catch (err) {
      console.error('Erro ao testar conexão:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao testar conexão',
        severity: 'error',
      });
    } finally {
      setTestingConnections(prev => {
        const newSet = new Set(prev);
        newSet.delete(connection.id);
        return newSet;
      });
    }
  };

  // Confirmar exclusão
  const handleDeleteClick = (connection: Connection) => {
    setConnectionToDelete(connection);
    setDeleteDialogOpen(true);
  };

  // Deletar conexão
  const handleDeleteConnection = async () => {
    if (!connectionToDelete) return;

    try {
      await connectionService.delete(connectionToDelete.id);
      setSnackbar({
        open: true,
        message: 'Conexão excluída com sucesso!',
        severity: 'success',
      });
      setDeleteDialogOpen(false);
      setConnectionToDelete(null);
      loadConnections();
    } catch (err) {
      console.error('Erro ao excluir conexão:', err);
      setSnackbar({
        open: true,
        message: 'Erro ao excluir conexão',
        severity: 'error',
      });
    }
  };

  // Fechar snackbar
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Função para obter cor do chip do tipo de banco
  const getDbTypeColor = (type: string) => {
    const colors: Record<string, 'default' | 'primary' | 'secondary' | 'success' | 'warning'> = {
      postgresql: 'primary',
      postgres: 'primary', // Alias
      sqlserver: 'secondary',
      oracle: 'success',
      sqlite: 'default',
      mysql: 'warning',
    };
    return colors[type.toLowerCase()] || 'default';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Carregando conexões...</Typography>
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
        <Typography color="text.primary">Conexões</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Gerenciamento de Conexões
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleNewConnection}
        >
          Nova Conexão
        </Button>
      </Box>

      {/* Error display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Connections Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nome</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Host</TableCell>
              <TableCell>Banco</TableCell>
              <TableCell>Usuário</TableCell>
              <TableCell align="center">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {connections.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="textSecondary">
                    Nenhuma conexão encontrada. Clique em "Nova Conexão" para começar.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              connections.map((connection) => (
                <TableRow key={connection.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <ConnectionIcon sx={{ mr: 1, color: 'text.secondary' }} />
                      <Typography variant="subtitle2" fontWeight="bold">
                        {connection.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={(connection.sgbd || connection.type || 'unknown').toUpperCase()}
                      color={getDbTypeColor(connection.sgbd || connection.type || '')}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {connection.host}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {connection.database}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {connection.user}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => handleTestConnection(connection)}
                      title="Testar Conexão"
                      disabled={testingConnections.has(connection.id)}
                      color="info"
                    >
                      <TestIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleEditConnection(connection)}
                      title="Editar"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteClick(connection)}
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

      {/* Dialog para criar/editar conexão */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        key={editingConnection ? `edit-${editingConnection.id}` : 'new'}
      >
        <DialogTitle>
          {editingConnection ? 'Editar Conexão' : 'Nova Conexão'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nome da Conexão"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          
          <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
            <InputLabel>Tipo de Banco</InputLabel>
            <Select
              value={formData.sgbd || 'postgresql'}
              onChange={(e) => {
                const newType = e.target.value as ConnectionForm['sgbd'];
                console.log('Mudando tipo para:', newType);
                setFormData({ ...formData, sgbd: newType });
              }}
              label="Tipo de Banco"
            >
              <MenuItem value="postgresql">PostgreSQL</MenuItem>
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="sqlserver">SQL Server</MenuItem>
              <MenuItem value="oracle">Oracle</MenuItem>
              <MenuItem value="sqlite">SQLite</MenuItem>
            </Select>
          </FormControl>

          <TextField
            margin="dense"
            label="Host"
            fullWidth
            variant="outlined"
            value={formData.host}
            onChange={(e) => setFormData({ ...formData, host: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label="Porta (opcional)"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.port || ''}
            onChange={(e) => setFormData({ ...formData, port: e.target.value ? parseInt(e.target.value) : undefined })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label="Nome do Banco"
            fullWidth
            variant="outlined"
            value={formData.database}
            onChange={(e) => setFormData({ ...formData, database: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label="Usuário"
            fullWidth
            variant="outlined"
            value={formData.user}
            onChange={(e) => setFormData({ ...formData, user: e.target.value })}
            sx={{ mb: 2 }}
          />

          <TextField
            margin="dense"
            label={editingConnection ? "Nova Senha (deixe vazio para manter)" : "Senha"}
            type="password"
            fullWidth
            variant="outlined"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleSaveConnection}
            variant="contained"
            disabled={!formData.name.trim() || !formData.database.trim() || !formData.host.trim()}
          >
            {editingConnection ? 'Atualizar' : 'Criar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog de confirmação para excluir */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmar Exclusão</DialogTitle>
        <DialogContent>
          <Typography>
            Tem certeza que deseja excluir a conexão "{connectionToDelete?.name}"?
            Esta ação não pode ser desfeita.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleDeleteConnection}
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
    </Box>
  );
};

export default ConnectionsPage;
