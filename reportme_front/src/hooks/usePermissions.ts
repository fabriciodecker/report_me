import { useAuth } from '../contexts/AuthContext';

export const usePermissions = () => {
  const { user } = useAuth();

  const isAdmin = user?.is_staff || false;
  const isReader = !isAdmin;

  return {
    isAdmin,
    isReader,
    canManageProjects: isAdmin,
    canManageConnections: isAdmin,
    canManageQueries: isAdmin,
    canExecuteQueries: true, // Todos podem executar
    canExportResults: true,  // Todos podem exportar
  };
};