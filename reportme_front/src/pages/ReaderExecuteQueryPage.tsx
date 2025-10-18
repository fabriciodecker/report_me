import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { queryService, parameterService } from '../services/api';
import { Query, Parameter } from '../types';
import Layout from '../components/Layout';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Button,
  TextField,
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
  TablePagination,
  IconButton,
  Chip
} from '@mui/material';
import {
  ArrowBack,
  PlayArrow,
  Download,
  Refresh
} from '@mui/icons-material';

interface ExecutionResult {
  data: any[];
  columns: string[];
  total_count: number;
  execution_time?: number;
}

const ReaderExecuteQueryPage: React.FC = () => {
  const { queryId } = useParams<{ queryId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const nodeName = location.state?.nodeName;
  
  const [query, setQuery] = useState<Query | null>(null);
  const [parameters, setParameters] = useState<Parameter[]>([]);
  const [parameterValues, setParameterValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  
  // Paginação
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  useEffect(() => {
    if (!queryId) return;

    const loadQueryData = async () => {
      try {
        setLoading(true);
        console.log('Carregando consulta:', queryId);
        
        // Carregar dados da consulta
        const queryData = await queryService.getById(Number(queryId));
        setQuery(queryData);
        
        // Carregar parâmetros da consulta
        const parametersData = await parameterService.getAll(Number(queryId));
        setParameters(parametersData.results || []);
        
        // Inicializar valores dos parâmetros
        const initialValues: Record<string, any> = {};
        parametersData.results?.forEach(param => {
          initialValues[param.name] = param.default_value || '';
        });
        setParameterValues(initialValues);
        
        setError(null);
      } catch (err: any) {
        console.error('Erro ao carregar consulta:', err);
        setError(err.response?.data?.detail || err.message || 'Erro ao carregar consulta');
      } finally {
        setLoading(false);
      }
    };

    loadQueryData();
  }, [queryId]);

  const handleParameterChange = (paramName: string, value: any) => {
    setParameterValues(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  const validateParameters = (): boolean => {
    for (const param of parameters) {
      if (!param.allow_null && !parameterValues[param.name]) {
        setError(`Parâmetro obrigatório não preenchido: ${param.name}`);
        return false;
      }
    }
    return true;
  };

  const executeQuery = async () => {
    if (!query) return;
    
    if (!validateParameters()) {
      return;
    }

    try {
      setExecuting(true);
      setError(null);
      
      console.log('Executando consulta no portal de leitura:', {
        queryId: query.id,
        parameters: parameterValues,
        query: query
      });
      
      const response = await queryService.execute(query.id, parameterValues);
      
      console.log('Resposta da execução no portal de leitura:', response);
      
      setResult({
        data: response.rows || [], // Usar rows ao invés de data
        columns: response.columns || [],
        total_count: response.total_count || response.rows?.length || 0,
        execution_time: response.execution_time_ms || response.execution_time
      });
    } catch (err: any) {
      console.error('Erro ao executar consulta:', err);
      setError(err.response?.data?.detail || err.message || 'Erro ao executar consulta');
    } finally {
      setExecuting(false);
    }
  };

  const handleExecuteClick = () => {
    executeQuery();
  };

  const handleExport = () => {
    if (!result?.data || !Array.isArray(result.data) || result.data.length === 0) {
      alert('Não há dados para exportar');
      return;
    }
    
    console.log('Debug Export - result.data:', result.data);
    console.log('Debug Export - result.columns:', result.columns);
    console.log('Debug Export - primeiro registro:', result.data[0]);
    console.log('Debug Export - total de registros:', result.data.length);
    
    try {
      // Criar CSV com escape adequado
      const headers = result.columns.map(col => `"${String(col).replace(/"/g, '""')}"`).join(',');
      
      const rows = result.data.map((row, rowIndex) => {
        if (!Array.isArray(row)) {
          console.error(`Linha ${rowIndex} não é um array:`, row);
          return '';
        }
        return row.map((value: any) => {
          if (value === null || value === undefined) {
            return '""';
          }
          const stringValue = String(value);
          // Escape aspas duplas e envolver em aspas
          return `"${stringValue.replace(/"/g, '""')}"`;
        }).join(',');
      }).filter(row => row !== ''); // Remover linhas vazias
      
      const csv = [headers, ...rows].join('\n');
      
      console.log('Debug Export - Cabeçalhos:', headers);
      console.log('Debug Export - Primeira linha de dados:', rows[0]);
      console.log('Debug Export - Total de linhas no CSV:', rows.length + 1);
      console.log('Debug Export - CSV completo (primeiras 500 chars):', csv.substring(0, 500));
      
      // Download com BOM para UTF-8
      const BOM = '\uFEFF';
      const csvWithBOM = BOM + csv;
      const blob = new Blob([csvWithBOM], { type: 'text/csv;charset=utf-8;' });
      
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      
      const fileName = `consulta_${query?.name?.replace(/[^a-zA-Z0-9]/g, '_') || 'resultado'}_${new Date().toISOString().slice(0, 10)}.csv`;
      link.setAttribute('download', fileName);
      
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Limpar URL
      URL.revokeObjectURL(url);
      
      console.log('Export realizado com sucesso:', fileName);
      
    } catch (error) {
      console.error('Erro durante a exportação:', error);
      alert('Erro ao exportar dados. Verifique o console para mais detalhes.');
    }
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const renderParameterField = (param: Parameter) => {
    const value = parameterValues[param.name] || '';
    
    switch (param.type) {
      case 'string':
        return (
          <TextField
            fullWidth
            label={param.name}
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            required={!param.allow_null}
          />
        );
        
      case 'number':
        return (
          <TextField
            fullWidth
            type="number"
            label={param.name}
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            required={!param.allow_null}
          />
        );
        
      case 'date':
        return (
          <TextField
            fullWidth
            type="date"
            label={param.name}
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            required={!param.allow_null}
            InputLabelProps={{ shrink: true }}
          />
        );
        
      case 'datetime':
        return (
          <TextField
            fullWidth
            type="datetime-local"
            label={param.name}
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            required={!param.allow_null}
            InputLabelProps={{ shrink: true }}
          />
        );
        
      case 'boolean':
        return (
          <FormControl fullWidth>
            <InputLabel>{param.name}</InputLabel>
            <Select
              value={value}
              label={param.name}
              onChange={(e) => handleParameterChange(param.name, e.target.value)}
            >
              <MenuItem value="true">Sim</MenuItem>
              <MenuItem value="false">Não</MenuItem>
            </Select>
          </FormControl>
        );
        
      default:
        return (
          <TextField
            fullWidth
            label={param.name}
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
            required={!param.allow_null}
          />
        );
    }
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

  if (error && !query) {
    return (
      <Layout>
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      </Layout>
    );
  }

  if (!query) {
    return (
      <Layout>
        <Alert severity="warning" sx={{ m: 2 }}>
          Consulta não encontrada
        </Alert>
      </Layout>
    );
  }

  return (
    <Layout>
      <Paper sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <IconButton onClick={() => navigate(-1)} sx={{ mr: 2 }}>
              <ArrowBack />
            </IconButton>
            <Box>
              <Typography variant="h4">
                {nodeName || query.name}
              </Typography>
              <Typography variant="h6" color="primary">
                Query: {query.name}
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Parâmetros */}
        {parameters.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Parâmetros da Consulta
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Preencha os parâmetros necessários e clique em "Executar" para visualizar os resultados.
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 }}>
                {parameters.map((param) => (
                  <Box key={param.id} sx={{ flex: '1 1 300px', minWidth: '250px' }}>
                    {renderParameterField(param)}
                    {param.description && (
                      <Typography variant="caption" color="text.secondary">
                        {param.description}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
              
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={executing ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={handleExecuteClick}
                  disabled={executing}
                >
                  {executing ? 'Executando...' : 'Executar Consulta'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Caso não tenha parâmetros, mostrar botão de execução */}
        {parameters.length === 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">
                  Consulta sem parâmetros
                </Typography>
                <Button
                  variant="contained"
                  startIcon={executing ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={handleExecuteClick}
                  disabled={executing}
                >
                  {executing ? 'Executando...' : 'Executar'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Informações da consulta */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Informações da Consulta
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="text.secondary">
                  Conexão: {query.connection_name || 'N/A'}
                </Typography>
              </Box>
              <Box sx={{ flex: '1 1 200px' }}>
                <Typography variant="body2" color="text.secondary">
                  Parâmetros: {parameters.length}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Erro */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Resultados */}
        {result && (
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Resultados ({result.total_count} registros)
                </Typography>
                <Box>
                  {result.execution_time && (
                    <Chip 
                      label={`${result.execution_time}ms`} 
                      size="small" 
                      sx={{ mr: 1 }}
                    />
                  )}
                  <Button
                    startIcon={<Download />}
                    onClick={handleExport}
                    disabled={!result.data.length}
                  >
                    Exportar CSV
                  </Button>
                </Box>
              </Box>

              {result.data.length === 0 ? (
                <Alert severity="info">
                  Nenhum resultado encontrado
                </Alert>
              ) : (
                <>
                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          {result.columns.map((column) => (
                            <TableCell key={column}>
                              <Typography variant="subtitle2" fontWeight="bold">
                                {column}
                              </Typography>
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {result.data
                          .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                          .map((row, index) => (
                            <TableRow key={index}>
                              {row.map((value: any, cellIndex: number) => (
                                <TableCell key={cellIndex}>
                                  {value !== null && value !== undefined
                                    ? String(value)
                                    : '-'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                  
                  <TablePagination
                    rowsPerPageOptions={[10, 50, 100]}
                    component="div"
                    count={result.data.length}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    labelRowsPerPage="Registros por página:"
                    labelDisplayedRows={({ from, to, count }) => 
                      `${from}-${to} de ${count !== -1 ? count : `mais de ${to}`}`
                    }
                  />
                </>
              )}
            </CardContent>
          </Card>
        )}
      </Paper>
    </Layout>
  );
};

export default ReaderExecuteQueryPage;