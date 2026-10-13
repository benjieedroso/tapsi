import { apiClient } from '../../../api/client';
import type { RecipeDetailData, RecipeFormMeta, RecipeFormMetaOptions, RecipeFormData, RecipeListResponse } from '../types/recipes.types';

export const recipesApi = {
  getRecipeDetail: async (id: string): Promise<{ recipe: RecipeDetailData; meta: RecipeFormMeta }> => {
    const response = await apiClient.get(`/api/v1/recipes/${id}/`);
    return response.data;
  },

  deleteRecipe: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/v1/recipes/${id}/`);
  },

  addLine: async (recipeId: string, payload: { ingredient_id: number; quantity: number }): Promise<void> => {
    await apiClient.post(`/api/v1/recipes/${recipeId}/lines/`, payload);
  },

  removeLine: async (recipeId: string, lineId: number): Promise<void> => {
    await apiClient.delete(`/api/v1/recipes/${recipeId}/lines/${lineId}/`);
  },

  getRecipeFormMeta: async (): Promise<RecipeFormMetaOptions> => {
    const response = await apiClient.get('/api/v1/recipes/meta/');
    return response.data;
  },

  createRecipe: async (payload: RecipeFormData): Promise<{ id: number }> => {
    const response = await apiClient.post('/api/v1/recipes/', payload);
    return response.data;
  },

  updateRecipe: async (id: string, payload: RecipeFormData): Promise<void> => {
    await apiClient.put(`/api/v1/recipes/${id}/`, payload);
  },

  getRecipeList: async (): Promise<RecipeListResponse> => {
    const response = await apiClient.get('/api/v1/recipes/');
    return response.data;
  },
};