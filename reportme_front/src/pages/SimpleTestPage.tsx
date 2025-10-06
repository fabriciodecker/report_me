import React from 'react';
import {
  Box,
  Typography,
  Paper,
} from '@mui/material';

const SimpleTestPage: React.FC = () => {
  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        🧪 Página de Teste - ReportMe
      </Typography>
      
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom color="success.main">
          ✅ Frontend funcionando!
        </Typography>
        <Typography variant="body1" paragraph>
          Esta é uma página de teste simples para verificar se o React está funcionando corretamente.
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Status: Aplicação carregada com sucesso
        </Typography>
      </Paper>
    </Box>
  );
};

export default SimpleTestPage;
