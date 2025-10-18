import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const HomePage: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Todos os usuários (admin e comum) vão para o portal de leitura
  // Admins têm acesso ao "Manage" via TopBar
  return <Navigate to="/reader" replace />;
};

export default HomePage;