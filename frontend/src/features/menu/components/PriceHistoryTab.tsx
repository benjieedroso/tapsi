import React, { useEffect, useState } from 'react';
import { getPriceHistory } from '../api/menu';
import type { MenuItem, PriceHistoryEntry } from '../types/menu.types';

interface PriceHistoryTabProps {
  item: MenuItem;
  onBack: () => void;
}

export const PriceHistoryTab: React.FC<PriceHistoryTabProps> = ({ item, onBack }) => {
  const [history, setHistory] = useState<PriceHistoryEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await getPriceHistory(item.id);
        setHistory(data);
      } catch (err) {
        setError('Failed to load price history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [item.id]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date);
  };

  return (
    <div className="price-history-tab">
      {/* Page Heading */}
      <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Price History</h2>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Track price changes for <strong>{item.name}</strong>.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onBack}>
          Back to items
        </button>
      </div>

      {/* Current Price Highlight Banner */}
      <div
        style={{
          marginBottom: '1rem',
          padding: '1rem',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          display: 'flex',
          alignItems: 'center',
        }}
      >
        <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Current price:</span>
        <span
          style={{
            fontSize: '1.25rem',
            fontWeight: 'bold',
            color: '#059669',
            marginLeft: '0.5rem',
          }}
        >
          ₱{Number(item.price).toFixed(2)}
        </span>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>{error}</div>}

      {/* History Table */}
      <div className="table-card">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e5e7eb', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Date</th>
              <th style={{ padding: '0.75rem 1rem' }}>Old Price</th>
              <th style={{ padding: '0.75rem 1rem' }}>New Price</th>
              <th style={{ padding: '0.75rem 1rem' }}>Changed By</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '2rem' }}>
                  Loading history...
                </td>
              </tr>
            ) : history.length > 0 ? (
              history.map((entry) => (
                <tr key={entry.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem' }}>{formatDate(entry.created_at)}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>₱{Number(entry.old_price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>₱{Number(entry.new_price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>
                    {entry.changed_by?.display_name || '—'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={4}
                  className="empty-state"
                  style={{ textAlign: 'center', padding: '3rem 1rem' }}
                >
                  <h3>No price changes yet</h3>
                  <p style={{ color: '#6b7280' }}>
                    Price changes will be recorded here when you update the item's price.
                  </p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};