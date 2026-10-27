import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { closingApi } from '../api/closing';
import type { ClosingPrepareData, OpenOrder } from '../types/closing.types';

export const ClosingPrepare: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [data, setData] = useState<ClosingPrepareData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [countedCash, setCountedCash] = useState<number | ''>('');
  const [varianceNote, setVarianceNote] = useState<string>('');

  const fetchPrepareData = useCallback(async () => {
    setLoading(true);
    try {
      const dateParam = searchParams.get('date') || new Date().toISOString().split('T')[0];
      const res = await closingApi.getClosingPrepare(dateParam);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.response?.data?.date?.[0] || 
        'Failed to load closing preparation data.'
      );
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchPrepareData();
  }, [fetchPrepareData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const dateParam = searchParams.get('date') || new Date().toISOString().split('T')[0];

    try {
      await closingApi.completeClosing({
        business_date: dateParam,
        counted_cash: Number(countedCash),
        variance_note: varianceNote || undefined,
      });
      navigate('/closing');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to complete day closing.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && !data) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading closing preparation...</div>;
  }

  const businessDateFormatted = data?.business_date
    ? new Date(data.business_date).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';

  const alreadyClosedDateFormatted = data?.business_date
    ? new Date(data.business_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Close Business Day</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            {businessDateFormatted}
          </p>
        </div>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      {data?.already_closed ? (
        <div
          className="alert"
          style={{
            background: 'var(--gray-100)',
            border: '1px solid var(--gray-300)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
          }}
        >
          <strong>
            {alreadyClosedDateFormatted} is already {data.already_closed?.status?.toLowerCase()}.
          </strong>
          {data.already_closed?.status === 'REOPENED' &&
            ' It must be re-closed by the Owner — the day is currently unlocked.'}
        </div>
      ) : data?.open_orders && data.open_orders.length > 0 ? (
        <div
          className="alert"
          style={{
            background: 'var(--color-error-bg)',
            border: '1px solid var(--color-error)',
            color: 'var(--color-error)',
            padding: 'var(--space-4)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-4)',
          }}
        >
          <strong>{data.open_orders.length} open order(s) still exist (FR-140):</strong>
          <ul style={{ margin: 'var(--space-2) 0 0 var(--space-4)' }}>
            {data.open_orders.map((order: OpenOrder) => (
              <li key={order.id}>
                #{order.order_number} — {order.status_display} — ₱{(order.total ?? 0).toFixed(2)}
              </li>
            ))}
          </ul>
          <p style={{ marginTop: 'var(--space-2)' }}>Complete or cancel them before closing the day.</p>
        </div>
      ) : (
        <div className="form-card" style={{ maxWidth: '480px' }}>
          <h2 style={{ marginBottom: 'var(--space-4)' }}>Cash Reconciliation</h2>
          <p style={{ color: 'var(--gray-500)', marginBottom: 'var(--space-3)' }}>
            Expected cash (FR-140): opening float + cash sales − cash refunds − cash expenses.
          </p>

          <div className="field">
            <label>Opening float</label>
            <div className="input" style={{ background: 'var(--gray-100)' }}>
              ₱{(data?.opening_float ?? 0).toFixed(2)}
            </div>
          </div>

          <div className="field">
            <label>Expected cash</label>
            <div className="input" style={{ background: 'var(--gray-100)' }}>
              ₱{(data?.expected_cash ?? 0).toFixed(2)}
            </div>
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label htmlFor="counted_cash">Counted cash</label>
              <input
                type="number"
                step="0.01"
                min="0"
                name="counted_cash"
                id="counted_cash"
                className="input"
                value={countedCash}
                onChange={(e) => setCountedCash(e.target.value === '' ? '' : Number(e.target.value))}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="variance_note">
                Variance explanation (required if beyond ±₱100, FR-141)
              </label>
              <input
                type="text"
                name="variance_note"
                id="variance_note"
                className="input"
                value={varianceNote}
                onChange={(e) => setVarianceNote(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Closing...' : 'Close day & lock'}
              </button>
              <Link to="/closing" className="btn btn-secondary">
                Cancel
              </Link>
            </div>
          </form>
        </div>
      )}
    </>
  );
};

export default ClosingPrepare;