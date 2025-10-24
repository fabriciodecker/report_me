import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Container,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  Lock as LockIcon,
  Visibility,
  VisibilityOff,
  CheckCircle as SuccessIcon
} from '@mui/icons-material';
import { authService } from '../services/api';

const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);

  useEffect(() => {
    if (!token) {
      setError('Token de recuperação não encontrado');
      setTokenValid(false);
    } else {
      // Aqui você poderia validar o token com o backend se necessário
      setTokenValid(true);
    }
  }, [token]);

  const validatePassword = (pwd: string): string[] => {
    const errors = [];
    if (pwd.length < 8) {
      errors.push('Mínimo de 8 caracteres');
    }
    if (!/(?=.*[a-z])/.test(pwd)) {
      errors.push('Pelo menos uma letra minúscula');
    }
    if (!/(?=.*[A-Z])/.test(pwd)) {
      errors.push('Pelo menos uma letra maiúscula');
    }
    if (!/(?=.*\d)/.test(pwd)) {
      errors.push('Pelo menos um número');
    }
    if (!/(?=.*[@$!%*?&])/.test(pwd)) {
      errors.push('Pelo menos um caractere especial (@$!%*?&)');
    }
    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!token) {
      setError('Token inválido');
      return;
    }

    if (!password.trim()) {
      setError('Por favor, digite a nova senha');
      return;
    }

    if (!confirmPassword.trim()) {
      setError('Por favor, confirme a nova senha');
      return;
    }

    if (password !== confirmPassword) {
      setError('As senhas não coincidem');
      return;
    }

    const passwordErrors = validatePassword(password);
    if (passwordErrors.length > 0) {
      setError(`Senha inválida: ${passwordErrors.join(', ')}`);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setMessage(null);

      await authService.resetPassword(token, password);
      
      setSuccess(true);
      setMessage('Senha redefinida com sucesso! Você será redirecionado para o login.');
      
      // Redirecionar para login após 3 segundos
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: 'Senha redefinida com sucesso! Faça login com sua nova senha.' 
          } 
        });
      }, 3000);
      
    } catch (err: any) {
      console.error('Erro ao redefinir senha:', err);
      setError(
        err.response?.data?.error || 
        'Erro ao redefinir senha. Verifique se o link não expirou.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (tokenValid === false) {
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
          <Paper elevation={8} sx={{ p: 4, textAlign: 'center' }}>
            <Alert severity="error" sx={{ mb: 3 }}>
              Link de recuperação inválido ou expirado
            </Alert>
            <Button
              variant="contained"
              onClick={() => navigate('/forgot-password')}
            >
              Solicitar Nova Recuperação
            </Button>
          </Paper>
        </Box>
      </Container>
    );
  }

  if (success) {
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
              textAlign: 'center',
            }}
          >
            <SuccessIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom color="success.main">
              Sucesso!
            </Typography>
            {message && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {message}
              </Alert>
            )}
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Redirecionando para o login...
            </Typography>
            <CircularProgress size={24} sx={{ mt: 2 }} />
          </Paper>
        </Box>
      </Container>
    );
  }

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
            <LockIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Nova Senha
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Digite sua nova senha
            </Typography>
          </Box>

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Nova Senha"
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirmar Nova Senha"
              type={showConfirmPassword ? 'text' : 'password'}
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={loading}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      edge="end"
                    >
                      {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Box sx={{ mt: 2, mb: 2 }}>
              <Typography variant="caption" color="text.secondary">
                A senha deve conter:
              </Typography>
              <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                <Typography variant="caption" component="li" color="text.secondary">
                  Mínimo de 8 caracteres
                </Typography>
                <Typography variant="caption" component="li" color="text.secondary">
                  Letras maiúsculas e minúsculas
                </Typography>
                <Typography variant="caption" component="li" color="text.secondary">
                  Números e caracteres especiais
                </Typography>
              </Box>
            </Box>

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
              {loading ? 'Redefinindo...' : 'Redefinir Senha'}
            </Button>
          </Box>

          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Button
              onClick={() => navigate('/login')}
              variant="text"
            >
              Voltar ao Login
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default ResetPasswordPage;