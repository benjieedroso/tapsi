import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: 'OWNER' | 'MANAGER' | 'CASHIER' | 'KITCHEN';
  restaurant?: {
    id: number;
    name: string;
  };
}

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: { username: string; password: string }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load user profile on initial mount if token exists
  useEffect(() => {
    const fetchCurrentUser = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const response = await apiClient.get('/api/v1/auth/me/');
          setUser(response.data);
        } catch (error) {
          // Token expired or invalid
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    fetchCurrentUser();
  }, []);
  
    const login = async (credentials: { username: string; password: string }) => {
        const response = await apiClient.post('/api/v1/auth/token/', {
          email: credentials.username,
          username: credentials.username,
          password: credentials.password,
        });
        const token = response.data.access || response.data.token;
        if (token) {
          localStorage.setItem('access_token', token);
          localStorage.setItem('token', token);
        }
        const userResponse = await apiClient.get('/api/v1/auth/me/');
        setUser(userResponse.data);
    };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token');
    localStorage.removeItem('restaurant_id');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook for consuming auth state in components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};