import apiClient from './client';

export const getMenuItems = async () => {
  const response = await apiClient.get('/menu/api/v1/items/');
  return response.data;
};

export const createMenuItem = async (itemData: any) => {
  const response = await apiClient.post('/menu/api/v1/items/', itemData);
  return response.data;
};