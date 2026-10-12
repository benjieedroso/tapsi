import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { inventoryApi } from '../api/inventory';

export const IngredientForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const action = isEdit ? 'Edit' : 'Add';

  const [name, setName] = useState<string>('');
  const [unit, setUnit] = useState<string>('');
  const [minimumStock, setMinimumStock] = useState<number | ''>(0);
  const [costPerUnit, setCostPerUnit] = useState<number | ''>('');

  const [loading, setLoading] = useState<boolean>(isEdit);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!id) return;
    const fetchIngredient = async () => {
      try {
        const data = await inventoryApi.getIngredientDetail(Number(id));
        setName(data.name);
        setUnit(data.unit);
        setMinimumStock(data.minimum_stock);
        setCostPerUnit(data.cost_per_unit ?? '');
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load ingredient details.']);
      } finally {
        setLoading(false);
      }
    };
    fetchIngredient();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload = {
      name,
      unit,
      minimum_stock: Number(minimumStock),
      cost_per_unit: costPerUnit === '' ? undefined : Number(costPerUnit),
    };

    try {
      if (isEdit && id) {
        await inventoryApi.updateIngredient(Number(id), payload);
      } else {
        await inventoryApi.createIngredient(payload);
      }
      navigate('/inventory/ingredients');
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setNonFieldErrors(data.non_field_errors);
        }
        setFieldErrors(data);
      } else {
        setNonFieldErrors(['An unexpected error occurred. Please try again.']);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading ingredient data...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{action} Ingredient</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Master data for a tracked ingredient.
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        <form onSubmit={handleSubmit} noValidate>
          {nonFieldErrors.length > 0 && (
            <ul className="errorlist">
              {nonFieldErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}

          <div className="field">
            <label htmlFor="id_name">Name</label>
            <input
              type="text"
              id="id_name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            {fieldErrors.name && (
              <ul className="errorlist">
                <li>{fieldErrors.name}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_unit">Unit</label>
            <input
              type="text"
              id="id_unit"
              className="input"
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              placeholder="e.g. kg, pcs, grams"
              required
            />
            {fieldErrors.unit && (
              <ul className="errorlist">
                <li>{fieldErrors.unit}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_minimum_stock">Minimum stock</label>
            <input
              type="number"
              id="id_minimum_stock"
              className="input"
              value={minimumStock}
              onChange={(e) => setMinimumStock(e.target.value === '' ? '' : Number(e.target.value))}
              min={0}
              step="any"
              required
            />
            {fieldErrors.minimum_stock && (
              <ul className="errorlist">
                <li>{fieldErrors.minimum_stock}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_cost_per_unit">Cost per unit (₱)</label>
            <input
              type="number"
              id="id_cost_per_unit"
              className="input"
              value={costPerUnit}
              onChange={(e) => setCostPerUnit(e.target.value === '' ? '' : Number(e.target.value))}
              min={0}
              step="0.01"
            />
            {fieldErrors.cost_per_unit && (
              <ul className="errorlist">
                <li>{fieldErrors.cost_per_unit}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : `${action} Ingredient`}
            </button>
            <Link to="/inventory/ingredients" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default IngredientForm;