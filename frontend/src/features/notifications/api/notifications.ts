import { apiClient } from '../../../api/client';
import type { NotificationListResponse } from '../types/notifications.types';

export const notificationsApi = {
  getNotifications: async (): Promise<NotificationListResponse> => {
    const response = await apiClient.get('/api/v1/notifications/');
    return response.data;
  },

  markAsRead: async (id: number): Promise<void> => {
    await apiClient.post(`/api/v1/notifications/${id}/read/`);
  },

  markAllAsRead: async (): Promise<void> => {
    await apiClient.post('/api/v1/notifications/read-all/');
  },
};