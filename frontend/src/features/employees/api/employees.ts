import { apiClient } from '../../../api/client';
import type { AttendanceDetail, AttendanceUpdatePayload, AttendanceListResponse, EmployeeDetail, EmployeeFormData, EmployeeListResponse } from '../types/employees.types';

export const employeesApi = {
  getAttendanceDetail: async (id: number): Promise<AttendanceDetail> => {
    const response = await apiClient.get(`/api/v1/employees/attendance/${id}/`);
    return response.data;
  },

  updateAttendance: async (id: number, payload: AttendanceUpdatePayload): Promise<AttendanceDetail> => {
    const response = await apiClient.put(`/api/v1/employees/attendance/${id}/`, payload);
    return response.data;
  },

  getAttendanceList: async (params?: { month?: string }): Promise<AttendanceListResponse> => {
    const response = await apiClient.get('/api/v1/employees/attendance/', { params });
    return response.data;
  },

  clockAttendance: async (action: 'in' | 'out'): Promise<void> => {
    await apiClient.post('/api/v1/employees/attendance/clock/', { action });
  },

  getEmployeeDetail: async (id: number): Promise<EmployeeDetail> => {
    const response = await apiClient.get(`/api/v1/employees/profiles/${id}/`);
    return response.data;
  },

  createEmployee: async (payload: EmployeeFormData): Promise<EmployeeDetail> => {
    const response = await apiClient.post('/api/v1/employees/profiles/', payload);
    return response.data;
  },

  updateEmployee: async (id: number, payload: EmployeeFormData): Promise<EmployeeDetail> => {
    const response = await apiClient.put(`/api/v1/employees/profiles/${id}/`, payload);
    return response.data;
  },

  getEmployeeList: async (params?: { q?: string }): Promise<EmployeeListResponse> => {
    const response = await apiClient.get('/api/v1/employees/profiles/', { params });
    return response.data;
  },

  deleteEmployee: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/employees/profiles/${id}/`);
  },
};