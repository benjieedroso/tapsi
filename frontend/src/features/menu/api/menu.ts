import { apiClient } from '../../../api/client';
import type { Category, MenuItem, Addon, PriceHistoryEntry } from '../types/menu.types';

// Categories
export const getCategories = async () => 
  (await apiClient.get<Category[]>('/api/v1/menu/categories/')).data;
export const createCategory = async (data: Partial<Category>) => 
  (await apiClient.post<Category>('/api/v1/menu/categories/', data)).data;
export const updateCategory = async (id: number, data: Partial<Category>) => 
  (await apiClient.patch<Category>(`/api/v1/menu/categories/${id}/`, data)).data;
export const deleteCategory = async (id: number) => 
  await apiClient.delete(`/api/v1/menu/categories/${id}/`);

// Menu Items
export const getMenuItems = async (params?: { q?: string; category?: string | number }) => {
  const response = await apiClient.get<MenuItem[]>('/api/v1/menu/items/', { params });
  return response.data;
};
export const createMenuItem = async (formData: FormData) => {
  const response = await apiClient.post<MenuItem>('/api/v1/menu/items/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
export const updateMenuItem = async (id: number, formData: FormData) => {
  const response = await apiClient.patch<MenuItem>(`/api/v1/menu/items/${id}/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
export const toggleMenuItemAvailability = async (id: number) => {
  const response = await apiClient.post<MenuItem>(`/api/v1/menu/items/${id}/toggle/`);
  return response.data;
};
export const toggleMenuItemAddon = async (id: number, addonId: number) => {
  const response = await apiClient.post(`/api/v1/menu/items/${id}/toggle-addon/`, { addon_id: addonId });
  return response.data;
};
export const deleteMenuItem = async (id: number) => {
  await apiClient.delete(`/api/v1/menu/items/${id}/`);
};
// Addons
export const getAddons = async () => (await apiClient.get<Addon[]>('/api/v1/menu/addons/')).data;
export const createAddon = async (data: Partial<Addon>) => (await apiClient.post<Addon>('/api/v1/menu/addons/', data)).data;
export const updateAddon = async (id: number, data: Partial<Addon>) => (await apiClient.patch<Addon>(`/api/v1/menu/addons/${id}/`, data)).data;
export const deleteAddon = async (id: number) => await apiClient.delete(`/api/v1/menu/addons/${id}/`);

// Price History
export const getPriceHistory = async (itemId: number) => {
  const response = await apiClient.get<PriceHistoryEntry[]>(`/api/v1/menu/items/${itemId}/price-history/`);
  return response.data;
};