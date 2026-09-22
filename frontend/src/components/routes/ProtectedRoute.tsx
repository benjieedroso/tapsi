import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

export const ProtectedRoute: React.FC = () => {
  const token = localStorage.getItem('token') || localStorage.getItem('access_token');

  // Debug check in DevTools Console
  console.log('[ProtectedRoute Check] Token exists:', Boolean(token));

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};