import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { recipesApi } from '../api/recipes';
import type { RecipeListItem } from '../types/recipes.types';

export const RecipeList: React.FC = () => {
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRecipes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await recipesApi.getRecipeList();
      
      // Handle direct arrays, DRF pagination 'results', or 'recipes' keys
      if (Array.isArray(res)) {
        setRecipes(res);
      } else if (res) {
        const dataAny = res as any;
        setRecipes(dataAny.results || dataAny.recipes || dataAny.data || []);
      } else {
        setRecipes([]);
      }

      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load recipes.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRecipes();
  }, [fetchRecipes]);

  const safeRecipes = recipes || [];

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Recipes</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Bill of materials — drives automatic stock deduction on order completion.
          </p>
        </div>
        <Link className="btn btn-primary" to="/recipes/create">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New recipe
        </Link>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Recipe</th>
              <th>Target</th>
              <th style={{ textAlign: 'right' }}>Cost</th>
              <th style={{ textAlign: 'right' }}>Margin</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: 'var(--space-4)' }}>
                  Loading recipes...
                </td>
              </tr>
            ) : safeRecipes.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-state">
                  <h3>No recipes yet</h3>
                  <p>Define ingredient quantities so stock deducts automatically.</p>
                  <Link to="/recipes/create" className="btn btn-primary">
                    New recipe
                  </Link>
                </td>
              </tr>
            ) : (
              safeRecipes.map((recipe: any) => (
                <tr key={recipe.id}>
                  <td>
                    <Link
                      to={`/recipes/${recipe.id}`}
                      style={{ color: 'var(--tapsi-700)', fontWeight: 600 }}
                    >
                      {recipe.name}
                    </Link>
                  </td>
                  <td>
                    {recipe.menu_item
                      ? `Menu: ${typeof recipe.menu_item === 'object' ? recipe.menu_item.name : recipe.menu_item}`
                      : recipe.addon
                      ? `Add-on: ${typeof recipe.addon === 'object' ? recipe.addon.name : recipe.addon}`
                      : '—'}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    ₱{parseFloat(recipe.cost || '0').toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    {recipe.margin == null ? '—' : `${Number(recipe.margin).toFixed(1)}%`}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <Link to={`/recipes/${recipe.id}`} className="btn btn-ghost btn-sm">
                      View
                    </Link>
                    <Link to={`/recipes/${recipe.id}/edit`} className="btn btn-ghost btn-sm">
                      Edit
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default RecipeList;