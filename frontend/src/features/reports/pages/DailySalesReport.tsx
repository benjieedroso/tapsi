import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { DailySalesData } from '../types/reports.types';

export const DailySalesReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [reportData, setReportData] = useState<DailySalesData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const currentDateParam = searchParams.get('date') || new Date().toISOString().split('T')[0];
  const [dateInput, setDateInput] = useState<string>(currentDateParam);

  const fetchDailySales = useCallback(async () => {
    setLoading(true);
    try {
      const res = await reportsApi.getDailySales(searchParams.get('date') || undefined);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load daily sales report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchDailySales();
  }, [fetchDailySales]);

  const handleDateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (dateInput) {
      setSearchParams({ date: dateInput });
    } else {
      setSearchParams({});
    }
  };

  const handleCsvExport = () => {
    const dateVal = searchParams.get('date') || dateInput;
    // Direct link or window open for CSV export endpoint
    window.open(`/api/v1/reports/daily-sales/?date=${dateVal}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Daily Sales Report...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Daily Sales Report</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-130 — figures from immutable completed orders.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button type="button" onClick={handleCsvExport} className="btn btn-secondary">
            Export CSV
          </button>
          <button type="button" onClick={() => window.print()} className="btn btn-secondary">
            Print PDF
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleDateSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)' }}
      >
        <input
          type="date"
          name="date"
          value={dateInput}
          onChange={(e) => setDateInput(e.target.value)}
          className="input"
          style={{ width: 'auto' }}
        />
        <button type="submit" className="btn btn-secondary btn-sm">
          Show
        </button>
      </form>

      {reportData && (
        <div className="table-card">
          <table>
            <tbody>
              <tr>
                <td>
                  <strong>Gross sales</strong>
                </td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.gross ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Discounts</td>
                <td style={{ textAlign: 'right' }}>− ₱{(reportData.discounts ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>
                  <strong>Net sales</strong>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <strong>₱{(reportData.net ?? 0).toFixed(2)}</strong>
                </td>
              </tr>
              <tr>
                <td>VATable sales</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.vatable ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>VAT-exempt sales (Senior/PWD)</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.exempt ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Output VAT (12%)</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.vat ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Refunds</td>
                <td style={{ textAlign: 'right', color: 'var(--color-error)' }}>
                  ₱{(reportData.refunds ?? 0).toFixed(2)}
                </td>
              </tr>
              <tr>
                <td>Orders completed</td>
                <td style={{ textAlign: 'right' }}>{reportData.order_count}</td>
              </tr>
              <tr>
                <td>Average order value</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.aov ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Cancelled orders</td>
                <td style={{ textAlign: 'right' }}>{reportData.cancelled}</td>
              </tr>
              {reportData.method_breakdown &&
                Object.entries(reportData.method_breakdown).map(([method, amount]) => (
                  <tr key={method}>
                    <td>{method} sales</td>
                    <td style={{ textAlign: 'right' }}>₱{(Number(amount) || 0).toFixed(2)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

export default DailySalesReport;