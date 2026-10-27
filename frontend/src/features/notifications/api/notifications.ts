import { apiClient } from '../../../api/client';
import type { NotificationListResponse } from '../types/notifications.types';

export const notificationsApi = {
  getNotifications: async (): Promise<NotificationListResponse> => {
    const response = await apiClient.get('/api/v1/notifications/records/');
    return response.data;
  },

  markAsRead: async (id: number): Promise<void> => {
    await apiClient.post(`/api/v1/notifications/records/${id}/mark-read/`);
  },

  markAllAsRead: async (): Promise<void> => {
    await apiClient.post('/api/v1/notifications/records/mark-all-read/');
  },
};