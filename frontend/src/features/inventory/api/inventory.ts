import { apiClient } from '../../../api/client';
import type { IngredientDetail, IngredientFormData, IngredientListResponse, StockCardResponse, TransactionFormMeta, CreateTransactionPayload } from '../types/inventory.types';

export const inventoryApi = {
  getIngredientDetail: async (id: number): Promise<IngredientDetail> => {
    const response = await apiClient.get(`/api/v1/inventory/ingredients/${id}/`);
    return response.data;
  },

  createIngredient: async (payload: IngredientFormData): Promise<IngredientDetail> => {
    const response = await apiClient.post('/api/v1/inventory/ingredients/', payload);
    return response.data;
  },

  updateIngredient: async (id: number, payload: IngredientFormData): Promise<IngredientDetail> => {
    const response = await apiClient.put(`/api/v1/inventory/ingredients/${id}/`, payload);
    return response.data;
  },

  getIngredientList: async (params?: { q?: string; low_stock?: string }): Promise<IngredientListResponse> => {
    const response = await apiClient.get('/api/v1/inventory/ingredients/', { params });
    return response.data;
  },

  deleteIngredient: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/inventory/ingredients/${id}/`);
  },

  getStockCard: async (id: number, params?: { type?: string; from?: string; to?: string }): Promise<StockCardResponse> => {
    const response = await apiClient.get(`/api/v1/inventory/ingredients/${id}/stock-card/`, { params });
    return response.data;
  },

  getTransactionFormMeta: async (): Promise<TransactionFormMeta> => {
    const response = await apiClient.get('/api/v1/inventory/transactions/create/meta/');
    return response.data;
  },

  createTransaction: async (payload: CreateTransactionPayload): Promise<void> => {
    await apiClient.post('/api/v1/inventory/transactions/', payload);
  },
};