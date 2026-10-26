import { apiClient } from '../../../api/client';
import type { 
  DailySalesData, 
  InventoryReportData, 
  MonthlySalesData, 
  ProductMixData, 
  ProfitLossData, 
  PurchaseReportData, 
  TaxSummaryData 
} from '../types/reports.types';

export const reportsApi = {
  getDailySales: async (date?: string): Promise<DailySalesData> => {
    const params = date ? { date } : {};
    const response = await apiClient.get('/api/v1/reports/daily-sales/', { params });
    return response.data;
  },

  getInventoryReport: async (params?: { start?: string; end?: string }): Promise<InventoryReportData> => {
    const response = await apiClient.get('/api/v1/reports/inventory/', { params });
    return response.data;
  },

  getMonthlySales: async (params?: { year?: number; month?: number }): Promise<MonthlySalesData> => {
    const response = await apiClient.get('/api/v1/reports/monthly-sales/', { params });
    return response.data;
  },

  getProductMix: async (params?: { start?: string; end?: string; category?: string }): Promise<ProductMixData> => {
    const response = await apiClient.get('/api/v1/reports/product-mix/', { params });
    return response.data;
  },

  getProfitLoss: async (params?: { start?: string; end?: string }): Promise<ProfitLossData> => {
    const response = await apiClient.get('/api/v1/reports/profit-loss/', { params });
    return response.data;
  },

  getPurchaseReport: async (params?: { start?: string; end?: string; supplier?: string }): Promise<PurchaseReportData> => {
    const response = await apiClient.get('/api/v1/reports/purchases/', { params });
    return response.data;
  },

  getTaxSummary: async (params?: { start?: string; end?: string }): Promise<TaxSummaryData> => {
    const response = await apiClient.get('/api/v1/reports/tax-summary/', { params });
    return response.data;
  },
};