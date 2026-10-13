import { apiClient } from '../../../api/client';
import type {
  RequestEmailChangePayload,
  EmailChangeResponse,
  PasswordResetConfirmPayload,
  PasswordResetConfirmResponse,
  RequestPasswordResetPayload,
  RequestPasswordResetResponse,
  UserProfile,
  RestaurantSettingsData,
  UpdateRestaurantSettingsPayload,
  StaffMember,
  UpdateStaffPayload,
  CreateStaffPayload,
  StaffRole,
  ResetStaffPasswordPayload,
  ChangePasswordParams
} from '../types/accounts.types';

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
      localStorage.setItem('access_token', token);
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

  logout: async () => {
    // If you have a backend logout endpoint, call it here, otherwise clear tokens locally
    return Promise.resolve();
  }
};

export const requestEmailChange = async (
  payload: RequestEmailChangePayload
): Promise<EmailChangeResponse> => {
  const response = await apiClient.post<EmailChangeResponse>(
    '/api/v1/profile/email/',
    payload
  );
  return response.data;
};

export const confirmPasswordReset = async (
  payload: PasswordResetConfirmPayload
): Promise<PasswordResetConfirmResponse> => {
  const response = await apiClient.post<PasswordResetConfirmResponse>(
    '/api/v1/auth/password/reset/confirm/',
    payload
  );
  return response.data;
};

export const requestPasswordReset = async (
  payload: RequestPasswordResetPayload
): Promise<RequestPasswordResetResponse> => {
  const response = await apiClient.post<RequestPasswordResetResponse>(
    '/api/v1/auth/password/reset/',
    payload
  );
  return response.data;
};

export const changePassword = async (data: ChangePasswordParams) => {
  const response = await apiClient.post('/api/v1/auth/password/change/', data);
  return response.data;
};

export const getProfile = async (): Promise<UserProfile> => {
  const response = await apiClient.get<UserProfile>('/api/v1/auth/me/');
  return response.data;
};

export const updateProfile = async (payload: {
  first_name: string;
  last_name: string;
  avatar?: File | null;
}) => {
  const formData = new FormData();
  formData.append('first_name', payload.first_name);
  formData.append('last_name', payload.last_name);

  if (payload.avatar instanceof File) {
    formData.append('avatar', payload.avatar);
  }

  const response = await apiClient.patch('/api/v1/auth/me/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// Restaurant Settings (managed via the RestaurantViewSet router or custom detail route)
export const getRestaurantSettings = async (): Promise<RestaurantSettingsData> => {
  // Assuming the router provides a list/detail for restaurants or a singleton endpoint
  const response = await apiClient.get<RestaurantSettingsData>('/api/v1/restaurants/');
  return Array.isArray(response.data) ? response.data[0] : response.data;
};

export const updateRestaurantSettings = async (
  payload: UpdateRestaurantSettingsPayload
): Promise<RestaurantSettingsData> => {
  const response = await apiClient.put<RestaurantSettingsData>(
    '/api/v1/restaurants/1/',
    payload
  );
  return response.data;
};

// Staff Management (handled via DefaultRouter register(r"staff", ...))
export const getStaffMember = async (id: string | number): Promise<StaffMember> => {
  const response = await apiClient.get<StaffMember>(`/api/v1/staff/${id}/`);
  return response.data;
};

export const updateStaffMember = async (
  id: string | number,
  payload: UpdateStaffPayload
): Promise<StaffMember> => {
  const response = await apiClient.put<StaffMember>(
    `/api/v1/staff/${id}/`,
    payload
  );
  return response.data;
};

export const createStaffMember = async (
  payload: CreateStaffPayload
): Promise<StaffMember> => {
  const response = await apiClient.post<StaffMember>(
    '/api/v1/staff/',
    payload
  );
  return response.data;
};

export const getStaffList = async (): Promise<StaffMember[]> => {
  const response = await apiClient.get<StaffMember[]>('/api/v1/staff/');
  // Handle DRF paginated vs non-paginated responses gracefully
  return Array.isArray(response.data) ? response.data : (response.data as any).results || [];
};

export const updateStaffRole = async (
  userId: number,
  role: StaffRole
): Promise<StaffMember> => {
  const response = await apiClient.patch<StaffMember>(
    `/api/v1/staff/${userId}/role/`,
    { role }
  );
  return response.data;
};

export const toggleStaffStatus = async (
  userId: number,
  isActive: boolean
): Promise<StaffMember> => {
  const response = await apiClient.patch<StaffMember>(
    `/api/v1/staff/${userId}/status/`,
    { is_active: isActive }
  );
  return response.data;
};

export const resetStaffPassword = async (
  userId: string | number,
  payload: ResetStaffPasswordPayload
): Promise<void> => {
  await apiClient.post(`/api/v1/staff/${userId}/reset-password/`, payload);
};