import { apiClient } from '../../../api/client';
import type { AttendanceDetail, AttendanceUpdatePayload, AttendanceRecord, EmployeeDetail, EmployeeFormData, EmployeeListResponse } from '../types/employees.types';

export const employeesApi = {
  getAttendanceDetail: async (id: number): Promise<AttendanceDetail> => {
    const response = await apiClient.get(`/api/v1/employees/attendance/${id}/`);
    return response.data;
  },

  updateAttendance: async (id: number, payload: AttendanceUpdatePayload): Promise<AttendanceDetail> => {
    const response = await apiClient.put(`/api/v1/employees/attendance/${id}/`, payload);
    return response.data;
  },

  getAttendanceList: async (params?: { month?: string }): Promise<AttendanceRecord[]> => {
    const response = await apiClient.get('/api/v1/employees/attendance/', { params });
    const data = response.data;

    // Handle plain arrays, paginated results, or object responses
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    if (Array.isArray(data.records)) return data.records;
    
    return [];
  },

  clockIn: async (): Promise<void> => {
    await apiClient.post('/api/v1/employees/attendance/clock-in/', {});
  },

  clockOut: async (): Promise<void> => {
    await apiClient.post('/api/v1/employees/attendance/clock-out/', {});
  },

  getEmployeeDetail: async (id: number): Promise<EmployeeDetail> => {
    const response = await apiClient.get(`/api/v1/employees/records/${id}/`);
    return response.data;
  },

  createEmployee: async (payload: EmployeeFormData): Promise<EmployeeDetail> => {
    const response = await apiClient.post('/api/v1/employees/records/', payload);
    return response.data;
  },

  updateEmployee: async (id: number, payload: EmployeeFormData): Promise<EmployeeDetail> => {
    const response = await apiClient.put(`/api/v1/employees/records/${id}/`, payload);
    return response.data;
  },

  getEmployeeList: async (params?: { q?: string }): Promise<EmployeeDetail[]> => {
    const response = await apiClient.get('/api/v1/employees/records/', { params });
    const data = response.data;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    return [];
  },

  deleteEmployee: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/employees/records/${id}/`);
  },
};