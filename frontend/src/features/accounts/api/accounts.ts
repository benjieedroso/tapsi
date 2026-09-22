import { apiClient } from '../../../api/client';
import type {
  RequestEmailChangePayload,
  EmailChangeResponse,
  ChangeInitialPasswordPayload,
  PasswordResetConfirmPayload,
  PasswordResetConfirmResponse,
  RequestPasswordResetPayload,
  RequestPasswordResetResponse,
  UpdateProfilePayload,
  UserProfile,
  RestaurantSettingsData,
  UpdateRestaurantSettingsPayload,
  StaffMember,
  UpdateStaffPayload,
  CreateStaffPayload,
  StaffRole,
  ResetStaffPasswordPayload
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

export const requestEmailChange = async (
  payload: RequestEmailChangePayload
): Promise<EmailChangeResponse> => {
  const response = await apiClient.post<EmailChangeResponse>(
    '/accounts/email-change/',
    payload
  );
  return response.data;
};

export const confirmPasswordReset = async (
  payload: PasswordResetConfirmPayload
): Promise<PasswordResetConfirmResponse> => {
  const response = await apiClient.post<PasswordResetConfirmResponse>(
    '/accounts/password-reset-confirm/',
    payload
  );
  return response.data;
};

export const requestPasswordReset = async (
  payload: RequestPasswordResetPayload
): Promise<RequestPasswordResetResponse> => {
  const response = await apiClient.post<RequestPasswordResetResponse>(
    '/accounts/password-reset/',
    payload
  );
  return response.data;
};

export const getProfile = async (): Promise<UserProfile> => {
  const response = await apiClient.get<UserProfile>('/accounts/profile/');
  return response.data;
};

export const updateProfile = async (
  payload: UpdateProfilePayload
): Promise<UserProfile> => {
  const formData = new FormData();
  formData.append('first_name', payload.first_name);
  formData.append('last_name', payload.last_name);

  if (payload.avatar) {
    formData.append('avatar', payload.avatar);
  }

  const response = await apiClient.patch<UserProfile>(
    '/accounts/profile/',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
};

//restaurant_settings
export const getRestaurantSettings = async (): Promise<RestaurantSettingsData> => {
  const response = await apiClient.get<RestaurantSettingsData>('/accounts/restaurant-settings/');
  return response.data;
};

export const updateRestaurantSettings = async (
  payload: UpdateRestaurantSettingsPayload
): Promise<RestaurantSettingsData> => {
  const response = await apiClient.put<RestaurantSettingsData>(
    '/accounts/restaurant-settings/',
    payload
  );
  return response.data;
};

//staff_edit.html
export const getStaffMember = async (id: string | number): Promise<StaffMember> => {
  const response = await apiClient.get<StaffMember>(`/accounts/staff/${id}/`);
  return response.data;
};

export const updateStaffMember = async (
  id: string | number,
  payload: UpdateStaffPayload
): Promise<StaffMember> => {
  const response = await apiClient.put<StaffMember>(
    `/accounts/staff/${id}/`,
    payload
  );
  return response.data;
};

//staff_form.html
export const createStaffMember = async (
  payload: CreateStaffPayload
): Promise<StaffMember> => {
  const response = await apiClient.post<StaffMember>(
    '/accounts/staff/',
    payload
  );
  return response.data;
};

//staff_list.html
export const getStaffList = async (): Promise<StaffMember[]> => {
  const response = await apiClient.get<StaffMember[]>('/accounts/staff/');
  return response.data;
};

export const updateStaffRole = async (
  userId: number,
  role: StaffRole
): Promise<StaffMember> => {
  const response = await apiClient.patch<StaffMember>(
    `/accounts/staff/${userId}/role/`,
    { role }
  );
  return response.data;
};

export const toggleStaffStatus = async (
  userId: number,
  isActive: boolean
): Promise<StaffMember> => {
  const response = await apiClient.patch<StaffMember>(
    `/accounts/staff/${userId}/status/`,
    { is_active: isActive }
  );
  return response.data;
};

export const resetStaffPassword = async (
  userId: string | number,
  payload: ResetStaffPasswordPayload
): Promise<void> => {
  await apiClient.post(`/accounts/staff/${userId}/reset-password/`, payload);
};