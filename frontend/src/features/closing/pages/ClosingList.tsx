import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { closingApi } from '../api/closing';
import type { DailyClosingItem } from '../types/closing.types';

interface ClosingListProps {
  userRole?: 'OWNER' | 'MANAGER' | 'CASHIER' | 'STAFF';
}

export const ClosingList: React.FC<ClosingListProps> = ({ userRole }) => {
  const [closings, setClosings] = useState<DailyClosingItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reopeningId, setReopeningId] = useState<number | null>(null);

  const fetchClosings = useCallback(async () => {
  setLoading(true);
  try {
    const res = await closingApi.getClosingList();
    
    // Ensure data is parsed correctly whether DRF returns a raw list or object wrapper
    const listData = Array.isArray(res) ? res : (res.closings || res.results || []);
    console.log("Fetched closings payload:", listData);
    
    setClosings(listData);
    setError(null);
  } catch (err: any) {
    setError(err.response?.data?.detail || 'Failed to load daily closings.');
  } finally {
    setLoading(false);
  }
}, []);

  useEffect(() => {
    fetchClosings();
  }, [fetchClosings]);

  const handleReopen = async (id: number) => {
    const reason = window.prompt('Reopen reason (required):');
    if (reason === null || !reason.trim()) return;

    setReopeningId(id);
    try {
      await closingApi.reopenClosing(id, reason.trim());
      await fetchClosings();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reopen daily closing.');
    } finally {
      setReopeningId(null);
    }
  };

  const isOwner = userRole === 'OWNER';

  if (loading && closings.length === 0) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading daily closings...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Daily Closings</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Closing locks the business day (BR-008) — no orders, payments, or expenses after closing (FR-142).
          </p>
        </div>
        <Link to="/closing/prepare" className="btn btn-primary">
          Close today
        </Link>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Business Date</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Expected Cash</th>
              <th style={{ textAlign: 'right' }}>Counted Cash</th>
              <th style={{ textAlign: 'right' }}>Variance</th>
              <th>Note</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {closings.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">
                  <h3>No closings yet</h3>
                  <p>Close the day to generate your End-of-Day report.</p>
                  <Link to="/closing/prepare" className="btn btn-primary" style={{ marginTop: 'var(--space-3)' }}>
                    Close today
                  </Link>
                </td>
              </tr>
            ) : (
              closings.map((closing: DailyClosingItem) => {
                const isClosed = closing.status === 'CLOSED';
                const hasVariance = Boolean(closing.variance);

                return (
                  <tr key={closing.id}>
                    <td>
                      {new Date(closing.business_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </td>
                    <td>
                      {isClosed ? (
                        <span className="badge badge-success">Closed</span>
                      ) : (
                        <span className="badge badge-warning">Reopened</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      ₱{Number(closing.expected_cash ?? 0).toFixed(2)}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      ₱{Number(closing.counted_cash ?? 0).toFixed(2)}
                    </td>
                    <td
                      style={{
                        textAlign: 'right',
                        color: hasVariance ? 'var(--color-error)' : 'inherit',
                      }}
                    >
                      ₱{Number(closing.variance ?? 0).toFixed(2)}
                    </td>
                    <td>{closing.variance_note || '—'}</td>
                    <td style={{ textAlign: 'right' }}>
                      <Link
                        to={`/closing/${closing.id}/report`}
                        className="btn btn-ghost btn-sm"
                      >
                        Report
                      </Link>
                      {isClosed && isOwner && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--color-error)' }}
                          onClick={() => handleReopen(closing.id)}
                          disabled={reopeningId === closing.id}
                        >
                          Reopen
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default ClosingList;