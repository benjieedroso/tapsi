import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { recipesApi } from '../api/recipes';
import type { RecipeDetailData, RecipeLine, IngredientOption } from '../types/recipes.types';

export const RecipeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [recipe, setRecipe] = useState<RecipeDetailData | null>(null);
  const [ingredients, setIngredients] = useState<IngredientOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Add line form states
  const [selectedIngredientId, setSelectedIngredientId] = useState<string>('');
  const [quantityInput, setQuantityInput] = useState<string>('');
  const [submittingLine, setSubmittingLine] = useState<boolean>(false);

  const fetchRecipe = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await recipesApi.getRecipeDetail(id);
      setRecipe(res.recipe);
      setIngredients(res.meta?.ingredients || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load recipe details.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchRecipe();
  }, [fetchRecipe]);

  const handleDeleteRecipe = async () => {
    if (!id || !recipe) return;
    if (!window.confirm(`Delete recipe '${recipe.name}'?`)) return;
    try {
      await recipesApi.deleteRecipe(id);
      navigate('/recipes');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete recipe.');
    }
  };

  const handleRemoveLine = async (lineId: number) => {
    if (!id) return;
    try {
      await recipesApi.removeLine(id, lineId);
      await fetchRecipe();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove ingredient line.');
    }
  };

  const handleAddLineSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !selectedIngredientId || !quantityInput) {
      alert('Please select an ingredient and enter a quantity.');
      return;
    }

    setSubmittingLine(true);
    try {
      await recipesApi.addLine(id, {
        ingredient_id: Number(selectedIngredientId),
        quantity: Number(quantityInput),
      });
      setSelectedIngredientId('');
      setQuantityInput('');
      await fetchRecipe();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add ingredient line.');
    } finally {
      setSubmittingLine(false);
    }
  };

  if (loading && !recipe) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading recipe...</div>;
  }

  if (error || !recipe) {
    return <div className="alert alert-danger" style={{ margin: 'var(--space-4)' }}>{error || 'Recipe not found.'}</div>;
  }

  const sellingPrice = recipe.menu_item?.price || recipe.addon?.price;

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{recipe.name}</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            {recipe.menu_item ? `Menu item: ${recipe.menu_item.name}` : recipe.addon ? `Add-on: ${recipe.addon.name}` : 'Recipe details'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Link className="btn btn-secondary" to={`/recipes/${recipe.id}/edit`}>
            Edit
          </Link>
          <button
            type="button"
            onClick={handleDeleteRecipe}
            className="btn btn-secondary"
            style={{ color: 'var(--color-error)' }}
          >
            Delete
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
        <div className="table-card" style={{ padding: 'var(--space-4)' }}>
          <h3 style={{ marginBottom: 'var(--space-3)' }}>Recipe Cost (FR-071)</h3>
          <p style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--tapsi-700)' }}>
            ₱{parseFloat(recipe.cost || '0').toFixed(2)}
          </p>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)' }}>From weighted average ingredient costs.</p>
        </div>
        <div className="table-card" style={{ padding: 'var(--space-4)' }}>
          <h3 style={{ marginBottom: 'var(--space-3)' }}>Gross Margin</h3>
          <p style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--tapsi-700)' }}>
            {recipe.margin == null ? '—' : `${Number(recipe.margin).toFixed(1)}%`}
          </p>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)' }}>
            {sellingPrice ? `Selling price ₱${parseFloat(sellingPrice).toFixed(2)}` : 'No price set'}
          </p>
        </div>
      </div>

      <h2 style={{ marginBottom: 'var(--space-3)' }}>Ingredient Lines</h2>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Ingredient</th>
              <th style={{ textAlign: 'right' }}>Quantity</th>
              <th style={{ textAlign: 'right' }}>Unit Cost</th>
              <th style={{ textAlign: 'right' }}>Line Cost</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {!recipe.lines || recipe.lines.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-state">
                  <h3>No ingredient lines</h3>
                </td>
              </tr>
            ) : (
              recipe.lines.map((line: RecipeLine) => (
                <tr key={line.id}>
                  <td>{line.ingredient.name}</td>
                  <td style={{ textAlign: 'right' }}>
                    {line.quantity} {line.ingredient.unit_of_measure}
                  </td>
                  <td style={{ textAlign: 'right' }}>₱{parseFloat(line.ingredient.average_unit_cost || '0').toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }}>₱{parseFloat(line.line_cost || '0').toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      style={{ color: 'var(--color-error)' }}
                      onClick={() => handleRemoveLine(line.id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <h3 style={{ margin: 'var(--space-5) 0 var(--space-3)' }}>Add Ingredient Line</h3>
      <div className="form-card" style={{ maxWidth: '560px' }}>
        <form onSubmit={handleAddLineSubmit} noValidate>
          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Ingredient</label>
            <select
              className="input"
              value={selectedIngredientId}
              onChange={(e) => setSelectedIngredientId(e.target.value)}
              required
            >
              <option value="">Select ingredient...</option>
              {ingredients.map((ing) => (
                <option key={ing.id} value={ing.id}>
                  {ing.name} ({ing.unit_of_measure})
                </option>
              ))}
            </select>
          </div>

          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Quantity</label>
            <input
              type="number"
              step="any"
              className="input"
              value={quantityInput}
              onChange={(e) => setQuantityInput(e.target.value)}
              placeholder="0.00"
              required
            />
          </div>

          <button type="submit" className="btn btn-primary btn-sm" disabled={submittingLine}>
            {submittingLine ? 'Adding...' : 'Add line'}
          </button>
        </form>
      </div>
    </>
  );
};

export default RecipeDetail;