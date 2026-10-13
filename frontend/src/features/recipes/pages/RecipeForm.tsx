import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { recipesApi } from '../api/recipes';
import type { RecipeFormMetaOptions, RecipeFormData } from '../types/recipes.types';

export const RecipeForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const actionText = isEdit ? 'Edit' : 'Create';
  const navigate = useNavigate();

  const [meta, setMeta] = useState<RecipeFormMetaOptions>({
    menu_items: [],
    addons: [],
    ingredients: [],
  });

  const [formData, setFormData] = useState<RecipeFormData>({
    name: '',
    menu_item_id: '',
    addon_id: '',
    ingredient_id: '',
    quantity: '',
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFormInitialData = useCallback(async () => {
    setLoading(true);
    try {
      const metaData = await recipesApi.getRecipeFormMeta();
      setMeta(metaData);

      if (isEdit && id) {
        const res = await recipesApi.getRecipeDetail(id);
        const r = res.recipe;
        setFormData({
          name: r.name || '',
          menu_item_id: r.menu_item?.id || '',
          addon_id: r.addon?.id || '',
          ingredient_id: '',
          quantity: '',
        });
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize recipe form.');
    } finally {
      setLoading(false);
    }
  }, [id, isEdit]);

  useEffect(() => {
    fetchFormInitialData();
  }, [fetchFormInitialData]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert('Please enter a recipe name.');
      return;
    }

    setSubmitting(true);
    try {
      const payload: RecipeFormData = {
        name: formData.name,
        menu_item_id: formData.menu_item_id ? Number(formData.menu_item_id) : null,
        addon_id: formData.addon_id ? Number(formData.addon_id) : null,
      };

      if (!isEdit) {
        if (formData.ingredient_id) payload.ingredient_id = Number(formData.ingredient_id);
        if (formData.quantity) payload.quantity = Number(formData.quantity);
      }

      if (isEdit && id) {
        await recipesApi.updateRecipe(id, payload);
        navigate(`/recipes/${id}`);
      } else {
        const created = await recipesApi.createRecipe(payload);
        navigate(`/recipes/${created.id}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${actionText.toLowerCase()} recipe.`);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading recipe form...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{actionText} Recipe</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            One recipe per menu item or add-on (FR-070).
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Recipe Name</label>
            <input
              type="text"
              name="name"
              className="input"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g., Tapsilog Recipe"
              required
            />
          </div>

          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Menu Item (Optional)</label>
            <select
              name="menu_item_id"
              className="input"
              value={formData.menu_item_id || ''}
              onChange={handleChange}
            >
              <option value="">None / Select menu item...</option>
              {meta.menu_items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>

          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Add-on (Optional)</label>
            <select
              name="addon_id"
              className="input"
              value={formData.addon_id || ''}
              onChange={handleChange}
            >
              <option value="">None / Select add-on...</option>
              {meta.addons.map((addon) => (
                <option key={addon.id} value={addon.id}>
                  {addon.name}
                </option>
              ))}
            </select>
          </div>

          {!isEdit && (
            <div className="settings-section" style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-3)', borderTop: '1px solid var(--gray-200)' }}>
              <h3 className="settings-section-title" style={{ marginBottom: 'var(--space-3)' }}>
                First Ingredient Line
              </h3>
              <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
                <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Ingredient</label>
                <select
                  name="ingredient_id"
                  className="input"
                  value={formData.ingredient_id || ''}
                  onChange={handleChange}
                >
                  <option value="">Select ingredient...</option>
                  {meta.ingredients.map((ing) => (
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
                  name="quantity"
                  className="input"
                  value={formData.quantity || ''}
                  onChange={handleChange}
                  placeholder="0.00"
                />
              </div>
            </div>
          )}

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : `${actionText} Recipe`}
            </button>
            <Link to="/recipes" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default RecipeForm;