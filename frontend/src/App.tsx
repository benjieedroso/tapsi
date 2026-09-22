import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login } from './features/accounts/pages/Login';
import { Register } from './features/accounts/pages/Register';
import { SidebarLayout } from './components/layout/SidebarLayout';
import { ProtectedRoute } from './components/routes/ProtectedRoute';
import { Dashboard } from './features/dashboard/pages/Dashboard';
import { authApi } from './features/accounts/api/accounts';

export default function App() {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token') || localStorage.getItem('access_token');
      if (token) {
        try {
          const userData = await authApi.getCurrentUser();
          setUser(userData);
        } catch {
          localStorage.removeItem('token');
          localStorage.removeItem('access_token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-500">
        Loading...
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Render Login directly without conditional inline <Navigate /> */}
        <Route path="/login" element={<Login onLoginSuccess={setUser} />} />
        <Route path="/register" element={<Register />} />

        {/* Protected Routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<SidebarLayout user={user} />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/menu" element={<h1>Menu View</h1>} />
            <Route path="/inventory" element={<h1>Inventory View</h1>} />
          </Route>
        </Route>

        {/* Default route */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}