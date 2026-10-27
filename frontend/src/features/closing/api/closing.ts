import { apiClient } from '../../../api/client';
import type { DailyClosingListResponse, ClosingPrepareData, ClosingCompletePayload, EODReportData } from '../types/closing.types';


const getTenantHeaders = () => {
  const restaurantId = localStorage.getItem('restaurant_id'); // fallback for your tenant ID 4
  return {
    headers: {
      'X-Restaurant-ID': restaurantId,
    },
  };
};

export const closingApi = {
  getClosingList: async (): Promise<DailyClosingListResponse> => {
    // 2. Pass getTenantHeaders() as the second argument to apiClient.get()
    const response = await apiClient.get('/api/v1/closing/', getTenantHeaders());
    return response.data;
  },

  reopenClosing: async (id: number, reason: string): Promise<void> => {
    await apiClient.post(`/api/v1/closing/${id}/reopen/`, { reopen_reason: reason }, getTenantHeaders());
  },

  getClosingPrepare: async (date: string): Promise<ClosingPrepareData> => {
    const response = await apiClient.get('/api/v1/closing/prepare/', {
      ...getTenantHeaders(),
      params: { date },
    });
    return response.data;
  },

  completeClosing: async (payload: ClosingCompletePayload): Promise<any> => {
    const response = await apiClient.post('/api/v1/closing/complete/', payload, getTenantHeaders());
    return response.data;
  },

  getEODReport: async (id: number): Promise<EODReportData> => {
    const response = await apiClient.get(`/api/v1/closing/${id}/report/`, getTenantHeaders());
    return response.data;
  },
};