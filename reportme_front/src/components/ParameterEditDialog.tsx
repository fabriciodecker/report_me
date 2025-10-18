import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Edit as EditIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { Parameter } from '../types';
import { queryService } from '../services/api';

interface ParameterEditDialogProps {
  open: boolean;
  onClose: () => void;
  queryId?: number;
  sqlText: string;
  parameters: Parameter[];
  onSave: (parameters: Parameter[]) => void;
  onValidate?: () => void;
}

interface ParameterForm {
  id?: number;
  name: string;
  type: 'string' | 'number' | 'date' | 'datetime' | 'boolean' | 'list';
  allow_null: boolean;
  default_value: string;
  allow_multiple_values: boolean;
  min_value?: number;
  max_value?: number;
  regex_pattern?: string;
  options: string[];
}

interface ValidationResult {
  isValid: boolean;
  missingParameters: string[];
  extraParameters: string[];
  message: string;
}

const ParameterEditDialog: React.FC<ParameterEditDialogProps> = ({
  open,
  onClose,
  queryId,
  sqlText,
  parameters,
  onSave,
  onValidate,
}) => {
  const [localParameters, setLocalParameters] = useState<Parameter[]>([]);
  const [editingParameter, setEditingParameter] = useState<Parameter | null>(null);
  const [parameterForm, setParameterForm] = useState<ParameterForm>({
    name: '',
    type: 'string',
    allow_null: false,
    default_value: '',
    allow_multiple_values: false,
    options: [],
  });
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [showParameterForm, setShowParameterForm] = useState(false);

  // Sincronizar com parâmetros externos
  useEffect(() => {
    setLocalParameters([...parameters]);
  }, [parameters]);

  // Extrair parâmetros do SQL
  const extractParametersFromSQL = (sql: string): string[] => {
    const parameterRegex = /:([a-zA-Z_][a-zA-Z0-9_]*)/g;
    const matches = [];
    let match;
    
    while ((match = parameterRegex.exec(sql)) !== null) {
      matches.push(match[1]);
    }
    
    // Remover duplicatas
    return Array.from(new Set(matches));
  };

  // Validar parâmetros
  const validateParameters = (): ValidationResult => {
    const sqlParameters = extractParametersFromSQL(sqlText);
    const configuredParameters = localParameters.map(p => p.name);
    
    const missingParameters = sqlParameters.filter(p => !configuredParameters.includes(p));
    const extraParameters = configuredParameters.filter(p => !sqlParameters.includes(p));
    
    const isValid = missingParameters.length === 0 && extraParameters.length === 0;
    
    let message = '';
    if (isValid) {
      message = 'Todos os parâmetros estão configurados corretamente!';
    } else {
      const parts = [];
      if (missingParameters.length > 0) {
        parts.push(`Faltam configurações para: ${missingParameters.join(', ')}`);
      }
      if (extraParameters.length > 0) {
        parts.push(`Parâmetros extras configurados: ${extraParameters.join(', ')}`);
      }
      message = parts.join(' | ');
    }
    
    return {
      isValid,
      missingParameters,
      extraParameters,
      message,
    };
  };

  // Executar validação
  const handleValidateParameters = () => {
    const result = validateParameters();
    setValidation(result);
    if (onValidate) {
      onValidate();
    }
  };

  // Adicionar/editar parâmetro
  const handleSaveParameter = () => {
    if (!parameterForm.name.trim()) return;

    const newParameter: Parameter = {
      id: editingParameter?.id || Date.now(), // ID temporário para novos
      name: parameterForm.name.trim(),
      type: parameterForm.type,
      allow_null: parameterForm.allow_null,
      default_value: parameterForm.default_value,
      allow_multiple_values: parameterForm.allow_multiple_values,
    };

    if (editingParameter) {
      // Editar existente
      setLocalParameters(prev => 
        prev.map(p => p.id === editingParameter.id ? newParameter : p)
      );
    } else {
      // Adicionar novo
      setLocalParameters(prev => [...prev, newParameter]);
    }

    // Reset form
    resetParameterForm();
  };

  // Remover parâmetro
  const handleDeleteParameter = (id: number) => {
    setLocalParameters(prev => prev.filter(p => p.id !== id));
  };

  // Editar parâmetro
  const handleEditParameter = (parameter: Parameter) => {
    setEditingParameter(parameter);
    setParameterForm({
      id: parameter.id,
      name: parameter.name,
      type: parameter.type,
      allow_null: parameter.allow_null,
      default_value: parameter.default_value || '',
      allow_multiple_values: parameter.allow_multiple_values,
      options: [],
    });
    setShowParameterForm(true);
  };

  // Reset form
  const resetParameterForm = () => {
    setParameterForm({
      name: '',
      type: 'string',
      allow_null: false,
      default_value: '',
      allow_multiple_values: false,
      options: [],
    });
    setEditingParameter(null);
    setShowParameterForm(false);
  };

  // Auto-sugerir parâmetros do SQL usando o backend
  const handleAutoSuggestParameters = async () => {
    if (!queryId || !sqlText.trim()) {
      alert('Query ID e SQL são necessários para auto-sugestão');
      return;
    }

    try {
      const result = await queryService.extractParameters(sqlText, queryId);
      console.log('Parâmetros extraídos do backend:', result);
      
      if (result.new_parameters && result.new_parameters.length > 0) {
        const newParameters: Parameter[] = result.new_parameters.map((backendParam: any) => ({
          id: Date.now() + Math.random(), // ID temporário único
          name: backendParam.name,
          type: backendParam.type || 'string',
          allow_null: backendParam.allow_null !== false,
          default_value: backendParam.default_value || '',
          allow_multiple_values: backendParam.allow_multiple_values || false,
        }));
        
        setLocalParameters(prev => [...prev, ...newParameters]);
        
        // Mostrar feedback
        alert(`${newParameters.length} novo(s) parâmetro(s) adicionado(s)!`);
      } else {
        alert('Nenhum novo parâmetro encontrado no SQL.');
      }
    } catch (error) {
      console.error('Erro ao extrair parâmetros:', error);
      
      // Fallback para extração local se o backend falhar
      const sqlParameters = extractParametersFromSQL(sqlText);
      const existingNames = localParameters.map(p => p.name);
      
      const newParameters: Parameter[] = sqlParameters
        .filter(name => !existingNames.includes(name))
        .map(name => ({
          id: Date.now() + Math.random(),
          name,
          type: 'string' as const,
          allow_null: true,
          default_value: '',
          allow_multiple_values: false,
        }));
      
      if (newParameters.length > 0) {
        setLocalParameters(prev => [...prev, ...newParameters]);
        alert(`${newParameters.length} parâmetro(s) sugerido(s) localmente (backend indisponível).`);
      } else {
        alert('Nenhum parâmetro encontrado no SQL.');
      }
    }
  };

  // Salvar e fechar
  const handleSave = () => {
    onSave(localParameters);
    onClose();
  };

  // Fechar e cancelar
  const handleCancel = () => {
    setLocalParameters([...parameters]); // Reset para estado original
    resetParameterForm();
    setValidation(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleCancel} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <SettingsIcon sx={{ mr: 1 }} />
            Edição de Parâmetros
          </Box>
          <Button
            startIcon={<CheckIcon />}
            onClick={handleValidateParameters}
            color="primary"
            variant="outlined"
            size="small"
          >
            Validar Parâmetros
          </Button>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mt: 1 }}>
          {/* Resultado da validação */}
          {validation && (
            <Alert 
              severity={validation.isValid ? 'success' : 'warning'} 
              sx={{ mb: 2 }}
              icon={validation.isValid ? <CheckIcon /> : <WarningIcon />}
            >
              <Typography variant="body2">
                {validation.message}
              </Typography>
            </Alert>
          )}

          {/* Botões de ação */}
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <Button
              startIcon={<AddIcon />}
              onClick={() => setShowParameterForm(true)}
              variant="outlined"
              size="small"
            >
              Novo Parâmetro
            </Button>
            <Button
              onClick={handleAutoSuggestParameters}
              variant="outlined"
              size="small"
              color="secondary"
            >
              Auto-sugerir do SQL
            </Button>
          </Box>

          {/* Lista de parâmetros atuais */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Parâmetros Configurados ({localParameters.length})
            </Typography>
            
            {localParameters.length === 0 ? (
              <Alert severity="info">
                Nenhum parâmetro configurado. Use "Auto-sugerir do SQL" ou "Novo Parâmetro".
              </Alert>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Nome</strong></TableCell>
                      <TableCell><strong>Tipo</strong></TableCell>
                      <TableCell><strong>Permite Nulo</strong></TableCell>
                      <TableCell><strong>Valor Padrão</strong></TableCell>
                      <TableCell><strong>Múltiplos Valores</strong></TableCell>
                      <TableCell align="center"><strong>Ações</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {localParameters.map((parameter) => (
                      <TableRow key={parameter.id}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {parameter.name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={parameter.type} 
                            size="small" 
                            color="primary" 
                            variant="outlined" 
                          />
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={parameter.allow_null ? 'Sim' : 'Não'} 
                            size="small" 
                            color={parameter.allow_null ? 'success' : 'default'}
                            variant="outlined" 
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {parameter.default_value || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={parameter.allow_multiple_values ? 'Sim' : 'Não'} 
                            size="small" 
                            color={parameter.allow_multiple_values ? 'success' : 'default'}
                            variant="outlined" 
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <IconButton
                              size="small"
                              onClick={() => handleEditParameter(parameter)}
                              title="Editar parâmetro"
                            >
                              <EditIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteParameter(parameter.id)}
                              title="Remover parâmetro"
                              color="error"
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>

          {/* Formulário de parâmetro */}
          {showParameterForm && (
            <Box sx={{ border: 1, borderColor: 'divider', borderRadius: 1, p: 2, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                {editingParameter ? 'Editar Parâmetro' : 'Novo Parâmetro'}
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mb: 2 }}>
                <TextField
                  label="Nome do Parâmetro"
                  value={parameterForm.name}
                  onChange={(e) => setParameterForm({ ...parameterForm, name: e.target.value })}
                  required
                  placeholder="ex: usuario_id"
                />

                <FormControl>
                  <InputLabel>Tipo</InputLabel>
                  <Select
                    value={parameterForm.type}
                    label="Tipo"
                    onChange={(e) => setParameterForm({ 
                      ...parameterForm, 
                      type: e.target.value as ParameterForm['type'] 
                    })}
                  >
                    <MenuItem value="string">Texto</MenuItem>
                    <MenuItem value="number">Número</MenuItem>
                    <MenuItem value="date">Data</MenuItem>
                    <MenuItem value="datetime">Data e Hora</MenuItem>
                    <MenuItem value="boolean">Verdadeiro/Falso</MenuItem>
                    <MenuItem value="list">Lista</MenuItem>
                  </Select>
                </FormControl>

                <TextField
                  label="Valor Padrão"
                  value={parameterForm.default_value}
                  onChange={(e) => setParameterForm({ ...parameterForm, default_value: e.target.value })}
                  placeholder="Opcional"
                />
              </Box>

              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={parameterForm.allow_null}
                      onChange={(e) => setParameterForm({ ...parameterForm, allow_null: e.target.checked })}
                    />
                  }
                  label="Permite valor nulo"
                />

                <FormControlLabel
                  control={
                    <Switch
                      checked={parameterForm.allow_multiple_values}
                      onChange={(e) => setParameterForm({ ...parameterForm, allow_multiple_values: e.target.checked })}
                    />
                  }
                  label="Permite múltiplos valores (IN)"
                />
              </Box>

              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  onClick={handleSaveParameter}
                  disabled={!parameterForm.name.trim()}
                  size="small"
                >
                  {editingParameter ? 'Atualizar' : 'Adicionar'}
                </Button>
                <Button
                  onClick={resetParameterForm}
                  size="small"
                >
                  Cancelar
                </Button>
              </Box>
            </Box>
          )}

          {/* Informações do SQL */}
          <Box>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" gutterBottom>
              Parâmetros Detectados no SQL
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              {(() => {
                const sqlParams = extractParametersFromSQL(sqlText);
                return sqlParams.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {sqlParams.map((param, index) => (
                      <Chip
                        key={index}
                        label={`:${param}`}
                        size="small"
                        color={localParameters.some(p => p.name === param) ? 'success' : 'warning'}
                        variant="outlined"
                      />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Nenhum parâmetro detectado no SQL (formato :nome_parametro)
                  </Typography>
                );
              })()}
            </Box>
          </Box>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleCancel}>
          Cancelar
        </Button>
        <Button onClick={handleSave} variant="contained">
          Salvar Parâmetros
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ParameterEditDialog;