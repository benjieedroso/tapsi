import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { inventoryApi } from '../api/inventory';
import type { IngredientOption, TransactionFormMeta } from '../types/inventory.types';

export const TransactionForm: React.FC = () => {
  const navigate = useNavigate();

  const [meta, setMeta] = useState<TransactionFormMeta | null>(null);
  const [loadingMeta, setLoadingMeta] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Form states
  const [ingredient, setIngredient] = useState<string>('');
  const [transactionType, setTransactionType] = useState<string>('PURCHASE');
  const [quantity, setQuantity] = useState<number | ''>('');
  const [direction, setDirection] = useState<string>('ADD');
  const [unitCost, setUnitCost] = useState<number | ''>('');
  const [reference, setReference] = useState<string>('');
  const [reason, setReason] = useState<string>('');

  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const data = await inventoryApi.getTransactionFormMeta();
        setMeta(data);
        if (data?.transaction_types?.length > 0) {
          setTransactionType(data.transaction_types[0][0]);
        }
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load form metadata.']);
      } finally {
        setLoadingMeta(false);
      }
    };
    fetchMeta();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload: any = {
      ingredient: Number(ingredient),
      transaction_type: transactionType,
      quantity: Number(quantity),
      reference: reference || undefined,
      reason: reason || undefined,
    };

    if (transactionType === 'ADJUSTMENT') {
      payload.direction = direction;
    }
    if (transactionType === 'PURCHASE' && unitCost !== '') {
      payload.unit_cost = Number(unitCost);
    }

    try {
      await inventoryApi.createTransaction(payload);
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

  if (loadingMeta) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading form...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Stock Movement</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Record a purchase, consumption, adjustment, spoilage, or return. The ledger is immutable — correct mistakes with a compensating entry.
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

          {/* Ingredient Selection */}
          <div className="field">
            <label htmlFor="id_ingredient">Ingredient</label>
            <select
              id="id_ingredient"
              className="input"
              value={ingredient}
              onChange={(e) => setIngredient(e.target.value)}
              required
            >
              <option value="">---------</option>
              {meta?.ingredients?.map((item: IngredientOption) => (
                <option key={item.id} value={item.id}>
                  {item.name} ({item.unit_of_measure})
                </option>
              ))}
            </select>
            {fieldErrors.ingredient && (
              <ul className="errorlist">
                <li>{fieldErrors.ingredient}</li>
              </ul>
            )}
          </div>

          {/* Transaction Type */}
          <div className="field">
            <label htmlFor="id_transaction_type">Transaction type</label>
            <select
              id="id_transaction_type"
              className="input"
              value={transactionType}
              onChange={(e) => setTransactionType(e.target.value)}
              required
            >
              {meta?.transaction_types?.map(([val, label]) => (
                <option key={val} value={val}>
                  {label}
                </option>
              ))}
            </select>
            {fieldErrors.transaction_type && (
              <ul className="errorlist">
                <li>{fieldErrors.transaction_type}</li>
              </ul>
            )}
          </div>

          {/* Conditional Direction Field (Visible only for ADJUSTMENT) */}
          {transactionType === 'ADJUSTMENT' && (
            <div className="field" id="direction-field">
              <label htmlFor="id_direction">Direction</label>
              <select
                id="id_direction"
                className="input"
                value={direction}
                onChange={(e) => setDirection(e.target.value)}
              >
                {meta?.directions?.map(([val, label]) => (
                  <option key={val} value={val}>
                    {label}
                  </option>
                ))}
              </select>
              {fieldErrors.direction && (
                <ul className="errorlist">
                  <li>{fieldErrors.direction}</li>
                </ul>
              )}
            </div>
          )}

          {/* Quantity */}
          <div className="field">
            <label htmlFor="id_quantity">Quantity</label>
            <input
              type="number"
              id="id_quantity"
              className="input"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value === '' ? '' : Number(e.target.value))}
              min={0}
              step="any"
              required
            />
            {fieldErrors.quantity && (
              <ul className="errorlist">
                <li>{fieldErrors.quantity}</li>
              </ul>
            )}
          </div>

          {/* Conditional Unit Cost Field (Visible only for PURCHASE) */}
          {transactionType === 'PURCHASE' && (
            <div className="field" id="unit-cost-field">
              <label htmlFor="id_unit_cost">Unit cost (₱)</label>
              <input
                type="number"
                id="id_unit_cost"
                className="input"
                value={unitCost}
                onChange={(e) => setUnitCost(e.target.value === '' ? '' : Number(e.target.value))}
                min={0}
                step="0.01"
              />
              <small style={{ color: 'var(--gray-400)' }}>Required for purchases.</small>
              {fieldErrors.unit_cost && (
                <ul className="errorlist">
                  <li>{fieldErrors.unit_cost}</li>
                </ul>
              )}
            </div>
          )}

          {/* Reference */}
          <div className="field">
            <label htmlFor="id_reference">Reference</label>
            <input
              type="text"
              id="id_reference"
              className="input"
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              placeholder="e.g. PO-1029, Receipt #4921"
            />
            {fieldErrors.reference && (
              <ul className="errorlist">
                <li>{fieldErrors.reference}</li>
              </ul>
            )}
          </div>

          {/* Reason */}
          <div className="field">
            <label htmlFor="id_reason">Reason</label>
            <textarea
              id="id_reason"
              className="input"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              placeholder="Explain adjustment, spoilage, or return..."
            />
            <small style={{ color: 'var(--gray-400)' }}>Required for adjustments, spoilage, and returns.</small>
            {fieldErrors.reason && (
              <ul className="errorlist">
                <li>{fieldErrors.reason}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Recording...' : 'Record movement'}
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

export default TransactionForm;