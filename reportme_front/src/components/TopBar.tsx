import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';

const TopBar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleManage = () => {
    navigate('/dashboard');
  };

  const handleReader = () => {
    navigate('/reader');
  };

  const isInAdminPortal = location.pathname.startsWith('/dashboard') || 
                         location.pathname.startsWith('/projects') || 
                         location.pathname.startsWith('/connections') || 
                         location.pathname.startsWith('/queries');

  const isInReaderPortal = location.pathname.startsWith('/reader') || location.pathname === '/';

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          ReportMe
        </Typography>

        {/* Informações do usuário */}
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 3 }}>
            <Typography variant="body2" sx={{ mr: 1 }}>
              Olá, {user.username}
            </Typography>
            <Chip 
              label={user.is_staff ? "Admin" : "Leitor"} 
              color={user.is_staff ? "secondary" : "default"}
              size="small"
              variant="outlined"
              sx={{ color: 'white', borderColor: 'rgba(255,255,255,0.7)' }}
            />
          </Box>
        )}

        {/* Navegação entre portais */}
        <Box sx={{ display: 'flex', gap: 1, mr: 2 }}>
          {/* Portal de Leitura - sempre visível */}
          <Button 
            color="inherit" 
            onClick={handleReader}
            variant={isInReaderPortal ? "outlined" : "text"}
            sx={{
              backgroundColor: isInReaderPortal ? 'rgba(255,255,255,0.1)' : 'transparent',
              borderColor: isInReaderPortal ? 'rgba(255,255,255,0.7)' : 'transparent'
            }}
          >
            📊 Portal de Leitura
          </Button>

          {/* Portal Admin - só para admins */}
          {user?.is_staff && (
            <Button 
              color="inherit" 
              onClick={handleManage}
              variant={isInAdminPortal ? "outlined" : "text"}
              sx={{
                backgroundColor: isInAdminPortal ? 'rgba(255,255,255,0.1)' : 'transparent',
                borderColor: isInAdminPortal ? 'rgba(255,255,255,0.7)' : 'transparent'
              }}
            >
              ⚙️ Portal Admin
            </Button>
          )}
        </Box>

        {/* Logout */}
        {user ? (
          <Button 
            color="inherit" 
            onClick={() => { logout(); navigate('/login'); }}
            variant="outlined"
            sx={{ borderColor: 'rgba(255,255,255,0.7)' }}
          >
            Sair
          </Button>
        ) : (
          <Button color="inherit" onClick={() => navigate('/login')}>
            Entrar
          </Button>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;
