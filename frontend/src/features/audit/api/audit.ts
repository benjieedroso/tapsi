import { apiClient } from '../../../api/client';
import type { AuditLogListResponse } from '../types/audit.types';

export const auditApi = {
  getAuditLogs: async (params?: {
    action?: string;
    entity?: string;
    actor?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
  }): Promise<AuditLogListResponse> => {
    const response = await apiClient.get('/api/v1/audit-logs/', { params });
    return response.data;
  },
};