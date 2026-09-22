import { apiClient } from '../../../api/client';
import type { ChangeInitialPasswordPayload } from '../types/accounts.types';

export interface RegisterPayload {
  restaurant_name: string;
  username: string;
  email: string;
  password: string;
  password_confirm: string;
}

export const authApi = {
  login: async (credentials: { username: string; password: string }) => {
    const response = await apiClient.post('/api/v1/auth/token/', {
      email: credentials.username,
      username: credentials.username,
      password: credentials.password,
    });

    const token = response.data.access || response.data.token;
    if (token) {
      localStorage.setItem('token', token);
      localStorage.setItem('access_token', token); // Set both to be 100% safe
    }
    return response.data;
  },

  register: async (payload: RegisterPayload) => {
    const response = await apiClient.post('/api/v1/auth/register/', payload);
    return response.data;
  },

  getCurrentUser: async () => {
    const token = localStorage.getItem('token') || localStorage.getItem('access_token');
    const response = await apiClient.get('/api/v1/auth/me/', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  },
};

export const changeInitialPassword = async (
  payload: ChangeInitialPasswordPayload
): Promise<void> => {
  await apiClient.post('/accounts/change-initial-password/', payload);
};