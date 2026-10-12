import { apiClient } from '../../../api/client';
import type { OrderDetail, KitchenOrder, TableOption, MenuItemOption, OrderFormMeta, CreateOrderPayload, OrderListResponse, ReceiptData, TableDetail, TableFormData, TableListResponse, TableStatus } from '../types/orders.types';

export const ordersApi = {
  // Kitchen Queue API
  getKitchenQueue: async (): Promise<KitchenOrder[]> => {
    const response = await apiClient.get('/api/v1/orders/kitchen/');
    return response.data;
  },

  advanceOrderStatus: async (orderId: number): Promise<KitchenOrder> => {
    const response = await apiClient.post(`/api/v1/orders/kitchen/${orderId}/advance/`);
    return response.data;
  },

  // Order Detail API
  getOrderDetail: async (id: number): Promise<{
    order: OrderDetail;
    shortfalls: any[];
    availableTables: TableOption[];
    menuItems: MenuItemOption[];
  }> => {
    const response = await apiClient.get(`/api/v1/orders/${id}/`);
    return response.data;
  },

  completeOrder: async (id: number): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${id}/complete/`);
    return response.data;
  },

  cancelOrder: async (id: number, reason: string): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${id}/cancel/`, { reason });
    return response.data;
  },

  transferTable: async (id: number, tableId: number): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${id}/transfer/`, { table_id: tableId });
    return response.data;
  },

  approveDiscount: async (id: number): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${id}/discount/approve/`);
    return response.data;
  },

  addItem: async (orderId: number, data: { item_id: number; quantity: number; notes?: string }): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${orderId}/items/`, data);
    return response.data;
  },

  removeItem: async (orderId: number, itemId: number): Promise<OrderDetail> => {
    const response = await apiClient.delete(`/api/v1/orders/${orderId}/items/${itemId}/`);
    return response.data;
  },

  recordPayment: async (orderId: number, data: { method: string; amount: number }): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${orderId}/payments/`, data);
    return response.data;
  },

  refundPayment: async (paymentId: number, reason: string): Promise<void> => {
    await apiClient.post(`/api/v1/orders/payments/${paymentId}/refund/`, { reason });
  },

  applyDiscount: async (orderId: number, data: { discount_type: string; value: number; ref?: string }): Promise<OrderDetail> => {
    const response = await apiClient.post(`/api/v1/orders/${orderId}/discount/`, data);
    return response.data;
  },
  // Order Form API
  getOrderFormMeta: async (): Promise<OrderFormMeta> => {
    const response = await apiClient.get('/api/v1/orders/create/meta/');
    return response.data;
  },

  createOrder: async (payload: CreateOrderPayload): Promise<OrderDetail> => {
    const response = await apiClient.post('/api/v1/orders/', payload);
    return response.data;
  },

  // Order List API
  getOrderList: async (params?: { status?: string; type?: string }): Promise<OrderListResponse> => {
    const response = await apiClient.get('/api/v1/orders/', { params });
    return response.data;
  },

  // Receipt API
  getReceipt: async (orderId: number): Promise<ReceiptData> => {
    const response = await apiClient.get(`/api/v1/orders/${orderId}/receipt/`);
    return response.data;
  },


  // Table Form API
  getTableDetail: async (id: number): Promise<TableDetail> => {
    const response = await apiClient.get(`/api/v1/tables/${id}/`);
    return response.data;
  },

  createTable: async (payload: TableFormData): Promise<TableDetail> => {
    const response = await apiClient.post('/api/v1/tables/', payload);
    return response.data;
  },

  updateTable: async (id: number, payload: TableFormData): Promise<TableDetail> => {
    const response = await apiClient.put(`/api/v1/tables/${id}/`, payload);
    return response.data;
  },

  // Table List API
  getTableList: async (): Promise<TableListResponse> => {
    const response = await apiClient.get('/api/v1/tables/');
    return response.data;
  },

  updateTableStatus: async (id: number, status: TableStatus): Promise<void> => {
    await apiClient.post(`/api/v1/tables/${id}/status/`, { status });
  },

  deleteTable: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/tables/${id}/`);
  },
};