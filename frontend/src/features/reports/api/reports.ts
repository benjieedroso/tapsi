import { apiClient } from '../../../api/client';
import type { DailySalesResponse, InventoryReportResponse, MonthlySalesResponse, ProductMixResponse, ProfitLossResponse, PurchaseReportResponse, TaxSummaryResponse } from '../types/reports.types';

export const reportsApi = {
  getDailySales: async (date?: string): Promise<DailySalesResponse> => {
    const params = date ? { date } : {};
    const response = await apiClient.get('/api/v1/reports/daily-sales/', { params });
    return response.data;
  },

  getInventoryReport: async (params?: { start?: string; end?: string }): Promise<InventoryReportResponse> => {
    const response = await apiClient.get('/api/v1/reports/inventory/', { params });
    return response.data;
  },

  getMonthlySales: async (params?: { year?: number; month?: number }): Promise<MonthlySalesResponse> => {
    const response = await apiClient.get('/api/v1/reports/monthly-sales/', { params });
    return response.data;
  },

  getProductMix: async (params?: { start?: string; end?: string; category?: string }): Promise<ProductMixResponse> => {
    const response = await apiClient.get('/api/v1/reports/product-mix/', { params });
    return response.data;
  },

  getProfitLoss: async (params?: { start?: string; end?: string }): Promise<ProfitLossResponse> => {
    const response = await apiClient.get('/api/v1/reports/profit-loss/', { params });
    return response.data;
  },

  getPurchaseReport: async (params?: { start?: string; end?: string; supplier?: string }): Promise<PurchaseReportResponse> => {
    const response = await apiClient.get('/api/v1/reports/purchases/', { params });
    return response.data;
  },

  getTaxSummary: async (params?: { start?: string; end?: string }): Promise<TaxSummaryResponse> => {
    const response = await apiClient.get('/api/v1/reports/tax-summary/', { params });
    return response.data;
  },
};