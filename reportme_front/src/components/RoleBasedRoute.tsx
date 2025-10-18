import React from 'react';
import { Navigate } from 'react-router-dom';
import { usePermissions } from '../hooks/usePermissions';

interface RoleBasedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
  readerOnly?: boolean;
}

const RoleBasedRoute: React.FC<RoleBasedRouteProps> = ({ 
  children, 
  adminOnly = false, 
  readerOnly = false 
}) => {
  const { isAdmin, isReader } = usePermissions();

  if (adminOnly && !isAdmin) {
    return <Navigate to="/reader" replace />;
  }

  if (readerOnly && !isReader) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

export default RoleBasedRoute;