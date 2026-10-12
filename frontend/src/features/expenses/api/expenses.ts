import { apiClient } from '../../../api/client';
import type { ExpenseCategory, ExpenseDetail, ExpenseFilterParams, ExpenseListResponse, ExpenseListItem } from '../types/expenses.types';

export const expensesApi = {
  getCategories: async (): Promise<ExpenseCategory[]> => {
    const response = await apiClient.get('/api/v1/expenses/categories/');
    return response.data;
  },

  getExpenseDetail: async (id: number): Promise<ExpenseDetail> => {
    const response = await apiClient.get(`/api/v1/expenses/${id}/`);
    return response.data;
  },

  createExpense: async (formData: FormData): Promise<ExpenseDetail> => {
    const response = await apiClient.post('/api/v1/expenses/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  updateExpense: async (id: number, formData: FormData): Promise<ExpenseDetail> => {
    const response = await apiClient.put(`/api/v1/expenses/${id}/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getExpenseList: async (params?: ExpenseFilterParams): Promise<ExpenseListResponse> => {
    const response = await apiClient.get('/api/v1/expenses/', { params });
    return response.data;
  },

  approveExpense: async (id: number): Promise<ExpenseListItem> => {
    const response = await apiClient.post(`/api/v1/expenses/${id}/approve/`);
    return response.data;
  },

  deleteExpense: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/expenses/${id}/`);
  },
};