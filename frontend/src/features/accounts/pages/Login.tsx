import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../api/accounts';

// 1. Define the component Props interface
interface LoginProps {
  onLoginSuccess?: (userData: any) => void;
}

// 2. Pass props into the component
export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');

  try {
    // 1. Authenticate and save token
    await authApi.login(credentials);
    
    // 2. Fetch user profile (silently catch if endpoint has issues)
    try {
      const userData = await authApi.getCurrentUser();
      if (onLoginSuccess) {
        onLoginSuccess(userData);
      }
    } catch (profileErr) {
      console.warn('Could not fetch user profile, proceeding with token:', profileErr);
    }

    // 3. Navigate straight to dashboard
    navigate('/dashboard');

  } catch (err: any) {
    console.error('DRF Login Error Details:', err.response?.data);
    const serverMessage = 
      err.response?.data?.detail || 
      err.response?.data?.non_field_errors?.[0] || 
      'Invalid credentials. Please try again.';
      
    setError(serverMessage);
  }
};


  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <section className="auth-card max-w-md w-full bg-white rounded-lg shadow-md p-8 border border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Welcome back</h1>
        <p className="text-sm text-gray-600 mb-6">Log in to manage your restaurant.</p>

        {error && (
          <div className="alert alert-error mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-md text-sm">
            <p>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div className="field">
            <label className="block text-sm font-medium text-gray-700 mb-1">Username or Email</label>
            <input
              type="text"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            />
          </div>

          <div className="field">
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md transition-colors"
          >
            Log in
          </button>
        </form>

        <div className="mt-6 text-sm text-gray-600 space-y-1">
          <p><Link to="/forgot-password" className="text-blue-600 hover:underline">Forgot your password?</Link></p>
          <p>New to TAPSI? <Link to="/register" className="text-blue-600 hover:underline">Register your restaurant</Link>.</p>
        </div>
      </section>
    </div>
  );
};