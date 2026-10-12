import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';
import type { SupplierDetailData, SupplierPOHistoryItem } from '../types/suppliers.types';

export const SupplierDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [supplier, setSupplier] = useState<SupplierDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Payment form states
  const [paymentAmount, setPaymentAmount] = useState<number | ''>('');
  const [paymentNotes, setPaymentNotes] = useState<string>('');
  const [submittingPayment, setSubmittingPayment] = useState<boolean>(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);

  const fetchSupplierDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await suppliersApi.getSupplierDetail(Number(id));
      setSupplier(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load supplier details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSupplierDetail();
  }, [id]);

  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    setSubmittingPayment(true);
    setPaymentError(null);

    try {
      await suppliersApi.createSupplierPayment(Number(id), {
        amount: Number(paymentAmount),
        notes: paymentNotes || undefined,
      });
      setPaymentAmount('');
      setPaymentNotes('');
      await fetchSupplierDetail();
    } catch (err: any) {
      setPaymentError(err.response?.data?.detail || 'Failed to record payment.');
    } finally {
      setSubmittingPayment(false);
    }
  };

  if (loading && !supplier) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading supplier details...</div>;
  }

  if (error || !supplier) {
    return <div className="alert alert-danger" style={{ margin: 'var(--space-4)' }}>{error || 'Supplier not found'}</div>;
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
          <h1>{supplier.name}</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            {supplier.payment_terms_display} · {supplier.phone || 'no phone'}
            {!supplier.is_active && (
              <span className="badge badge-warning" style={{ marginLeft: 'var(--space-2)' }}>
                Inactive
              </span>
            )}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Link className="btn btn-primary" to="/suppliers/purchase-orders/create">
            New Purchase Order
          </Link>
          <Link className="btn btn-secondary" to={`/suppliers/${supplier.id}/edit`}>
            Edit
          </Link>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-4)',
        }}
      >
        {/* Outstanding Balance (FR-051) */}
        <div className="table-card" style={{ padding: 'var(--space-4)' }}>
          <h3 style={{ marginBottom: 'var(--space-3)' }}>Outstanding Balance (FR-051)</h3>
          <p style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--tapsi-700)' }}>
            ₱{(supplier.outstanding_balance ?? 0).toFixed(2)}
          </p>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)' }}>
            Received but unpaid purchase orders.
          </p>
        </div>

        {/* Record Payment (FR-052) */}
        <div className="table-card" style={{ padding: 'var(--space-4)' }}>
          <h3 style={{ marginBottom: 'var(--space-3)' }}>Record Payment (FR-052)</h3>
          {paymentError && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-3)' }}>{paymentError}</div>}
          <form onSubmit={handlePaymentSubmit} noValidate>
            <div className="field">
              <label htmlFor="id_payment_amount">Amount (₱)</label>
              <input
                type="number"
                id="id_payment_amount"
                className="input"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value === '' ? '' : Number(e.target.value))}
                min={0}
                step="0.01"
                required
              />
            </div>
            <div className="field">
              <label htmlFor="id_payment_notes">Notes</label>
              <input
                type="text"
                id="id_payment_notes"
                className="input"
                value={paymentNotes}
                onChange={(e) => setPaymentNotes(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn-primary btn-sm" disabled={submittingPayment}>
              {submittingPayment ? 'Recording...' : 'Record payment'}
            </button>
          </form>
        </div>
      </div>

      <h2 style={{ marginBottom: 'var(--space-3)' }}>Purchase History</h2>
      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>PO Number</th>
              <th>Date</th>
              <th style={{ textAlign: 'right' }}>Total</th>
              <th style={{ textAlign: 'right' }}>Received</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {supplier.pos.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-state">
                  <h3>No purchase orders</h3>
                  <p>Create a purchase order for this supplier.</p>
                </td>
              </tr>
            ) : (
              supplier.pos.map((po: SupplierPOHistoryItem) => (
                <tr key={po.id}>
                  <td>
                    <Link
                      to={`/suppliers/purchase-orders/${po.id}`}
                      style={{ color: 'var(--tapsi-700)' }}
                    >
                      {po.po_number}
                    </Link>
                  </td>
                  <td>
                    {new Date(po.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td style={{ textAlign: 'right' }}>₱{(po.total ?? 0).toFixed(2)}</td>
                  <td style={{ textAlign: 'right' }}>₱{(po.received_total ?? 0).toFixed(2)}</td>
                  <td>
                    <span className={`badge ${getStatusBadgeClass(po.status)}`}>
                      {po.status_display}
                    </span>
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

export default SupplierDetail;