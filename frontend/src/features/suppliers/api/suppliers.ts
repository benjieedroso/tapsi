import { apiClient } from '../../../api/client';
import type { PODetail, POCreateMeta, CreatePOPayload, POListResponse, SupplierDetailData, SupplierPaymentPayload, SupplierFormData, SupplierEditDetail, SupplierListResponse } from '../types/suppliers.types';

export const suppliersApi = {
  getPODetail: async (id: number): Promise<PODetail> => {
    const response = await apiClient.get(`/api/v1/suppliers/purchase-orders/${id}/`);
    return response.data;
  },

  placePO: async (id: number): Promise<PODetail> => {
    const response = await apiClient.post(`/api/v1/suppliers/purchase-orders/${id}/place/`);
    return response.data;
  },

  cancelPO: async (id: number): Promise<PODetail> => {
    const response = await apiClient.post(`/api/v1/suppliers/purchase-orders/${id}/cancel/`);
    return response.data;
  },

  getPOCreateMeta: async (): Promise<POCreateMeta> => {
    const response = await apiClient.get('/api/v1/suppliers/purchase-orders/create/meta/');
    return response.data;
  },

  createPO: async (payload: CreatePOPayload): Promise<any> => {
    const response = await apiClient.post('/api/v1/suppliers/purchase-orders/', payload);
    return response.data;
  },

  getPOList: async (params?: { status?: string; supplier?: string }): Promise<POListResponse> => {
    const response = await apiClient.get('/api/v1/suppliers/purchase-orders/', { params });
    return response.data;
  },

  receivePO: async (id: number, payload: Record<string, number> | { items: Array<{ item_id: number; qty_received: number }> }): Promise<any> => {
    const response = await apiClient.post(`/api/v1/suppliers/purchase-orders/${id}/receive/`, payload);
    return response.data;
  },

  getSupplierDetail: async (id: number): Promise<SupplierDetailData> => {
    const response = await apiClient.get(`/api/v1/suppliers/${id}/`);
    return response.data;
  },

  createSupplierPayment: async (supplierId: number, payload: SupplierPaymentPayload): Promise<any> => {
    const response = await apiClient.post(`/api/v1/suppliers/${supplierId}/payments/`, payload);
    return response.data;
  },

  createSupplier: async (payload: SupplierFormData): Promise<SupplierEditDetail> => {
    const response = await apiClient.post('/api/v1/suppliers/', payload);
    return response.data;
  },

  updateSupplier: async (id: number, payload: SupplierFormData): Promise<SupplierEditDetail> => {
    const response = await apiClient.put(`/api/v1/suppliers/${id}/`, payload);
    return response.data;
  },

  getSupplierList: async (params?: { search?: string; is_active?: boolean }): Promise<SupplierDetailData[]> => {
    const response = await apiClient.get('/api/v1/suppliers/', { params });
    const data = response.data;
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.results)) return data.results;
    return [];
  },

  deleteSupplier: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/suppliers/${id}/`);
  },
};