import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Container
} from '@mui/material';
import {
  Email as EmailIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import { authService } from '../services/api';

const ForgotPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email.trim()) {
      setError('Por favor, digite seu email');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setMessage(null);

      await authService.requestPasswordReset(email);
      
      setEmailSent(true);
      setMessage('Email de recuperação enviado com sucesso! Verifique sua caixa de entrada.');
      
    } catch (err: any) {
      console.error('Erro ao solicitar recuperação de senha:', err);
      setError(
        err.response?.data?.error || 
        'Erro ao enviar email de recuperação. Tente novamente.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper
          elevation={8}
          sx={{
            p: 4,
            width: '100%',
            maxWidth: 400,
            borderRadius: 2,
          }}
        >
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <EmailIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Recuperar Senha
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {emailSent 
                ? 'Instruções enviadas para seu email'
                : 'Digite seu email para receber as instruções de recuperação'
              }
            </Typography>
          </Box>

          {!emailSent ? (
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email"
                name="email"
                autoComplete="email"
                autoFocus
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />

              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}

              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : undefined}
              >
                {loading ? 'Enviando...' : 'Enviar Email de Recuperação'}
              </Button>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center' }}>
              {message && (
                <Alert severity="success" sx={{ mt: 2, mb: 3 }}>
                  {message}
                </Alert>
              )}
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Se você não receber o email em alguns minutos, verifique sua pasta de spam 
                ou tente novamente.
              </Typography>
            </Box>
          )}

          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/login')}
              variant="text"
            >
              Voltar ao Login
            </Button>
          </Box>

          {emailSent && (
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Button
                onClick={() => {
                  setEmailSent(false);
                  setEmail('');
                  setMessage(null);
                  setError(null);
                }}
                variant="outlined"
                size="small"
              >
                Enviar para outro email
              </Button>
            </Box>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default ForgotPasswordPage;