import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';
import type { PODetail as PODetailType, POItem } from '../types/suppliers.types';

export const PODetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [po, setPo] = useState<PODetailType | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const fetchPODetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await suppliersApi.getPODetail(Number(id));
      setPo(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load purchase order details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPODetail();
  }, [id]);

  const handlePlaceOrder = async () => {
    if (!id) return;
    setActionLoading(true);
    try {
      await suppliersApi.placePO(Number(id));
      await fetchPODetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to place purchase order.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancelPO = async () => {
    if (!id || !window.confirm('Are you sure you want to cancel this purchase order?')) return;
    setActionLoading(true);
    try {
      await suppliersApi.cancelPO(Number(id));
      await fetchPODetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel purchase order.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !po) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading purchase order...</div>;
  }

  if (error || !po) {
    return <div className="alert alert-danger" style={{ margin: 'var(--space-4)' }}>{error || 'PO not found'}</div>;
  }

  const getStatusBadgeClass = (status: string) => {
    if (status === 'RECEIVED') return 'badge-success';
    if (status === 'CANCELLED') return 'badge-warning';
    return 'badge-neutral';
  };

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{po.po_number}</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            {po.supplier_name} · {new Date(po.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            {' · '}
            <span className={`badge ${getStatusBadgeClass(po.status)}`}>
              {po.status_display}
            </span>
            {po.is_read_only && <span className="badge badge-neutral" style={{ marginLeft: 'var(--space-2)' }}>Read-only</span>}
          </p>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          {po.status === 'DRAFT' && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={handlePlaceOrder}
              disabled={actionLoading}
            >
              Place order
            </button>
          )}

          {(po.status === 'DRAFT' || po.status === 'ORDERED') && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCancelPO}
              disabled={actionLoading}
            >
              Cancel PO
            </button>
          )}

          {(po.status === 'ORDERED' || po.status === 'PARTIALLY_RECEIVED') && (
            <Link className="btn btn-primary" to={`/suppliers/purchase-orders/${po.id}/receive`}>
              Receive stock
            </Link>
          )}
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Ingredient</th>
              <th style={{ textAlign: 'right' }}>Ordered</th>
              <th style={{ textAlign: 'right' }}>Received</th>
              <th style={{ textAlign: 'right' }}>Outstanding</th>
              <th style={{ textAlign: 'right' }}>Unit Cost</th>
              <th style={{ textAlign: 'right' }}>Line Total</th>
              <th style={{ textAlign: 'right' }}>Variance</th>
            </tr>
          </thead>
          <tbody>
            {po.items.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">
                  <h3>No line items</h3>
                </td>
              </tr>
            ) : (
              po.items.map((item: POItem) => (
                <tr key={item.id}>
                  <td>{item.ingredient_name}</td>
                  <td style={{ textAlign: 'right' }}>{item.qty_ordered}</td>
                  <td style={{ textAlign: 'right' }}>{item.qty_received}</td>
                  <td style={{ textAlign: 'right' }}>{item.outstanding_qty}</td>
                  <td style={{ textAlign: 'right' }}>₱{(item.unit_cost ?? 0).toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }}>₱{(item.line_total ?? 0).toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }}>{(item.qty_ordered ?? 0).toFixed(2)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {po.notes && (
        <p style={{ color: 'var(--gray-600)', marginTop: 'var(--space-3)' }}>
          <strong>Notes:</strong> {po.notes}
        </p>
      )}
    </>
  );
};

export default PODetail;