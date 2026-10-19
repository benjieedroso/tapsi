import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';
import type { PODetail, POItem } from '../types/suppliers.types';

export const POReceive: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const [po, setPo] = useState<PODetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Map of item id -> received quantity input
  const [receivedValues, setReceivedValues] = useState<Record<number, number | ''>>({});

  useEffect(() => {
    if (!id) return;
    const fetchPO = async () => {
      try {
        const data = await suppliersApi.getPODetail(Number(id));
        setPo(data);

        // Initialize default received quantities to outstanding quantities
        const initialValues: Record<number, number> = {};
        data.items.forEach((item: POItem) => {
          initialValues[item.id] = item.outstanding_qty ?? 0;
        });
        setReceivedValues(initialValues);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load purchase order.');
      } finally {
        setLoading(false);
      }
    };
    fetchPO();
  }, [id]);

  const handleInputChange = (itemId: number, val: string) => {
    setReceivedValues((prev) => ({
      ...prev,
      [itemId]: val === '' ? '' : Number(val),
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !po || !po.items) return;

    setSubmitting(true);
    setError(null);

    const itemsPayload = po.items.map((item: POItem) => {
      const val = receivedValues[item.id];
      const qty = val !== '' && val !== undefined ? Number(val) : Number(item.outstanding_qty ?? 0);
      return {
        item_id: Number(item.id),
        qty_received: qty,
      };
    });

    try {
      await suppliersApi.receivePO(Number(id), { items: itemsPayload });
      navigate(`/suppliers/purchase-orders/${id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to receive stock.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !po) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading receive form...</div>;
  }

  if (error && !po) {
    return <div className="alert alert-danger" style={{ margin: 'var(--space-4)' }}>{error}</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Receive {po?.po_number}</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Enter received quantities (≤ outstanding per line). Stock and weighted average cost update atomically.
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '800px', width: '100%' }}>
        {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="table-card" style={{ marginBottom: 'var(--space-4)', overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '10px' }}>Ingredient</th>
                  <th style={{ textAlign: 'right', padding: '10px' }}>Ordered</th>
                  <th style={{ textAlign: 'right', padding: '10px' }}>Outstanding</th>
                  <th style={{ textAlign: 'right', padding: '10px' }}>Receive</th>
                </tr>
              </thead>
              <tbody>
                {po?.items.map((item: POItem) => (
                  <tr key={item.id} style={{ borderTop: '1px solid var(--gray-200, #eee)' }}>
                    <td style={{ padding: '12px 10px' }}>{item.ingredient_name}</td>
                    <td style={{ textAlign: 'right', padding: '12px 10px' }}>{item.qty_ordered}</td>
                    <td style={{ textAlign: 'right', padding: '12px 10px' }}>{item.outstanding_qty}</td>
                    <td style={{ textAlign: 'right', padding: '12px 10px' }}>
                      <input
                        type="number"
                        className="input"
                        step="0.001"
                        min="0"
                        style={{ width: '120px', textAlign: 'right' }}
                        value={receivedValues[item.id] ?? ''}
                        onChange={(e) => handleInputChange(item.id, e.target.value)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Receiving...' : 'Receive stock'}
            </button>
            <Link to={`/suppliers/purchase-orders/${id}`} className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default POReceive;