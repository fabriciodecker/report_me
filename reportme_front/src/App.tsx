import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import LoginPage from './pages/LoginPage';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectNodesPage from './pages/ProjectNodesPage';
import ConnectionsPage from './pages/ConnectionsPage';
import QueriesPage from './pages/QueriesPage';
import ReaderPortalPage from './pages/ReaderPortalPage';
import ReaderProjectTreePage from './pages/ReaderProjectTreePage';
import ReaderExecuteQueryPage from './pages/ReaderExecuteQueryPage';
import ProtectedRoute from './components/ProtectedRoute';
import RoleBasedRoute from './components/RoleBasedRoute';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <RoleBasedRoute adminOnly>
                    <DashboardPage />
                  </RoleBasedRoute>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/projects" 
              element={
                <ProtectedRoute>
                  <RoleBasedRoute adminOnly>
                    <ProjectsPage />
                  </RoleBasedRoute>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/projects/:projectId/nodes" 
              element={
                <ProtectedRoute>
                  <RoleBasedRoute adminOnly>
                    <ProjectNodesPage />
                  </RoleBasedRoute>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/connections" 
              element={
                <ProtectedRoute>
                  <RoleBasedRoute adminOnly>
                    <ConnectionsPage />
                  </RoleBasedRoute>
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/queries" 
              element={
                <ProtectedRoute>
                  <RoleBasedRoute adminOnly>
                    <QueriesPage />
                  </RoleBasedRoute>
                </ProtectedRoute>
              } 
            />
            <Route
              path="/reader"
              element={
                <ProtectedRoute>
                  <ReaderPortalPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reader/projects/:projectId"
              element={
                <ProtectedRoute>
                  <ReaderProjectTreePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reader/execute-query/:queryId"
              element={
                <ProtectedRoute>
                  <ReaderExecuteQueryPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
