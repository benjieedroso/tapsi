import { apiClient } from '../../../api/client';
import type { DailyClosingListResponse, ClosingPrepareData, ClosingCompletePayload, EODReportData } from '../types/closing.types';

export const closingApi = {
  getClosingList: async (): Promise<DailyClosingListResponse> => {
    const response = await apiClient.get('/api/v1/closing/');
    return response.data;
  },

  reopenClosing: async (id: number, reason: string): Promise<void> => {
    await apiClient.post(`/api/v1/closing/${id}/reopen/`, { reason });
  },

  getClosingPrepare: async (): Promise<ClosingPrepareData> => {
    const response = await apiClient.get('/api/v1/closing/prepare/');
    return response.data;
  },

  completeClosing: async (payload: ClosingCompletePayload): Promise<any> => {
    const response = await apiClient.post('/api/v1/closing/complete/', payload);
    return response.data;
  },

  getEODReport: async (id: number): Promise<EODReportData> => {
    const response = await apiClient.get(`/api/v1/closing/${id}/report/`);
    return response.data;
  },
};