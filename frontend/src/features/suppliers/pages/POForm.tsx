import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';
import type { POCreateMeta, SupplierOption, IngredientOption } from '../types/suppliers.types';

export const POForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEditing = Boolean(id);

  const [meta, setMeta] = useState<POCreateMeta | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Form states
  const [supplier, setSupplier] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  const [lineIngredient, setLineIngredient] = useState<string>('');
  const [qtyOrdered, setQtyOrdered] = useState<number | ''>('');
  const [unitCost, setUnitCost] = useState<number | ''>('');

  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, any>>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const metaData = await suppliersApi.getPOCreateMeta();
        setMeta(metaData);

        if (isEditing && id) {
          const poData = await suppliersApi.getPODetail(Number(id));
          setSupplier(String(poData.supplier_name ? '' : '')); // We map supplier id if available, or fetch detail
          setNotes(poData.notes || '');
          if (poData.items && poData.items.length > 0) {
            setLineIngredient(String(poData.items[0].ingredient_name)); // or ingredient ID if returned
            setQtyOrdered(poData.items[0].qty_ordered);
            setUnitCost(poData.items[0].unit_cost);
          }
        }
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load form data.']);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, isEditing]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload = {
      supplier: Number(supplier),
      notes: notes || undefined,
      items: [
        {
          ingredient: Number(lineIngredient),
          qty_ordered: Number(qtyOrdered),
          unit_cost: Number(unitCost),
        }
      ]
    };

    try {
      if (isEditing && id) {
        await suppliersApi.updatePO(Number(id), payload);
        navigate(`/suppliers/purchase-orders/${id}`);
      } else {
        const res = await suppliersApi.createPO(payload);
        navigate(`/suppliers/purchase-orders/${res.id}`);
      }
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
    return <div style={{ padding: 'var(--space-4)' }}>Loading form...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{isEditing ? 'Edit Purchase Order' : 'New Purchase Order'}</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            {isEditing ? 'Modify draft purchase order details.' : 'Add one line item per ingredient. More lines can be added after saving.'}
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

          {/* Supplier Field */}
          <div className="field">
            <label htmlFor="id_supplier">Supplier</label>
            <select
              id="id_supplier"
              className="input"
              value={supplier}
              onChange={(e) => setSupplier(e.target.value)}
              required
            >
              <option value="">---------</option>
              {(meta?.suppliers || []).map((s: SupplierOption) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            {fieldErrors.supplier && (
              <ul className="errorlist">
                <li>{fieldErrors.supplier}</li>
              </ul>
            )}
          </div>

          {/* Notes Field */}
          <div className="field">
            <label htmlFor="id_notes">Notes</label>
            <textarea
              id="id_notes"
              className="input"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
            {fieldErrors.notes && (
              <ul className="errorlist">
                <li>{fieldErrors.notes}</li>
              </ul>
            )}
          </div>

          {/* First Line Item Section */}
          <div className="settings-section" style={{ marginTop: 'var(--space-4)' }}>
            <h3 className="settings-section-title">First Line Item</h3>

            <div className="field">
              <label htmlFor="id_line_ingredient">Ingredient</label>
              <select
                id="id_line_ingredient"
                className="input"
                value={lineIngredient}
                onChange={(e) => setLineIngredient(e.target.value)}
                required
              >
                <option value="">---------</option>
                {(meta?.ingredients || []).map((ing: IngredientOption) => (
                  <option key={ing.id} value={ing.id}>
                    {ing.name} {ing.unit_of_measure ? `(${ing.unit_of_measure})` : ''}
                  </option>
                ))}
              </select>
              {fieldErrors.items && (
                <ul className="errorlist">
                  <li>Invalid item data</li>
                </ul>
              )}
            </div>

            <div className="field">
              <label htmlFor="id_qty_ordered">Quantity Ordered</label>
              <input
                type="number"
                id="id_qty_ordered"
                className="input"
                value={qtyOrdered}
                onChange={(e) => setQtyOrdered(e.target.value === '' ? '' : Number(e.target.value))}
                min={0}
                step="any"
                required
              />
              {fieldErrors.qty_ordered && (
                <ul className="errorlist">
                  <li>{fieldErrors.qty_ordered}</li>
                </ul>
              )}
            </div>

            <div className="field">
              <label htmlFor="id_unit_cost">Unit Cost (₱)</label>
              <input
                type="number"
                id="id_unit_cost"
                className="input"
                value={unitCost}
                onChange={(e) => setUnitCost(e.target.value === '' ? '' : Number(e.target.value))}
                min={0}
                step="0.01"
                required
              />
              {fieldErrors.unit_cost && (
                <ul className="errorlist">
                  <li>{fieldErrors.unit_cost}</li>
                </ul>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : isEditing ? 'Update purchase order' : 'Create purchase order'}
            </button>
            <Link to="/suppliers/purchase-orders" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default POForm;