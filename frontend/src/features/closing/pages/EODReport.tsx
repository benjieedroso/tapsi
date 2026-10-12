import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { closingApi } from '../api/closing';
import type { EODReportData } from '../types/closing.types';

export const EODReport: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [closing, setClosing] = useState<EODReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchReport = async () => {
      try {
        const data = await closingApi.getEODReport(Number(id));
        setClosing(data);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load end-of-day report.');
      } finally {
        setLoading(false);
      }
    };
    fetchReport();
  }, [id]);

  if (loading && !closing) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading End-of-Day report...</div>;
  }

  if (error || !closing) {
    return <div className="alert alert-danger" style={{ margin: 'var(--space-4)' }}>{error || 'Report not found'}</div>;
  }

  const businessDateFormatted = closing.business_date
    ? new Date(closing.business_date).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : '';

  const isClosed = closing.status === 'CLOSED';
  const hasVariance = Boolean(closing.variance);

  const closedByName = closing.closed_by?.get_full_name || closing.closed_by?.email || '—';
  const reopenedByName = closing.reopened_by
    ? closing.reopened_by.get_full_name || closing.reopened_by.email
    : '—';

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>End-of-Day Report</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            {businessDateFormatted}
          </p>
        </div>
        <button type="button" onClick={() => window.print()} className="btn btn-secondary">
          Print
        </button>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            <tr>
              <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Status</td>
              <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>
                {isClosed ? (
                  <span className="badge badge-success">Closed</span>
                ) : (
                  <span className="badge badge-warning">Reopened</span>
                )}
              </td>
            </tr>
            <tr>
              <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Opening float</td>
              <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>
                ₱{(closing.opening_float ?? 0).toFixed(2)}
              </td>
            </tr>
            <tr>
              <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Expected cash</td>
              <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>
                ₱{(closing.expected_cash ?? 0).toFixed(2)}
              </td>
            </tr>
            <tr>
              <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Counted cash</td>
              <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>
                ₱{(closing.counted_cash ?? 0).toFixed(2)}
              </td>
            </tr>
            <tr style={{ borderTop: '2px solid var(--gray-300)' }}>
              <td style={{ padding: 'var(--space-2)', fontWeight: 700 }}>Variance</td>
              <td
                style={{
                  padding: 'var(--space-2)',
                  textAlign: 'right',
                  fontWeight: 700,
                  color: hasVariance ? 'var(--color-error)' : 'var(--color-success)',
                }}
              >
                ₱{(closing.variance ?? 0).toFixed(2)}
              </td>
            </tr>
            <tr>
              <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Variance note</td>
              <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>
                {closing.variance_note || '—'}
              </td>
            </tr>
            <tr>
              <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Closed by</td>
              <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>{closedByName}</td>
            </tr>
            {!isClosed && (
              <>
                <tr>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Reopened by</td>
                  <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>{reopenedByName}</td>
                </tr>
                <tr>
                  <td style={{ padding: 'var(--space-2)', color: 'var(--gray-500)' }}>Reopen reason</td>
                  <td style={{ padding: 'var(--space-2)', textAlign: 'right' }}>
                    {closing.reopen_reason || '—'}
                  </td>
                </tr>
              </>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default EODReport;