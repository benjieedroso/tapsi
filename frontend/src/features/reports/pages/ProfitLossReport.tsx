import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { ProfitLossData } from '../types/reports.types';

export const ProfitLossReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const defaultStart =
    searchParams.get('start') ||
    new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0];
  const defaultEnd = searchParams.get('end') || new Date().toISOString().split('T')[0];

  const [reportData, setReportData] = useState<ProfitLossData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [startInput, setStartInput] = useState<string>(defaultStart);
  const [endInput, setEndInput] = useState<string>(defaultEnd);

  const fetchProfitLoss = useCallback(async () => {
    setLoading(true);
    try {
      const params: { start?: string; end?: string } = {};
      const startParam = searchParams.get('start');
      const endParam = searchParams.get('end');
      if (startParam) params.start = startParam;
      if (endParam) params.end = endParam;

      const res = await reportsApi.getProfitLoss(params);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load profit & loss report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchProfitLoss();
  }, [fetchProfitLoss]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams: Record<string, string> = {};
    if (startInput) newParams.start = startInput;
    if (endInput) newParams.end = endInput;
    setSearchParams(newParams);
  };

  const handleCsvExport = () => {
    const s = searchParams.get('start') || startInput;
    const e = searchParams.get('end') || endInput;
    window.open(`/api/v1/reports/profit-loss/?start=${s}&end=${e}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Profit &amp; Loss Report...</div>;
  }

  const isLoss = (reportData?.profit ?? 0) < 0;

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Profit &amp; Loss</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-133 — net sales − cost of goods (consumption + spoilage) − expenses = profit.
          </p>
        </div>
        <button type="button" onClick={handleCsvExport} className="btn btn-secondary">
          Export CSV
        </button>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleFilterSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)' }}
      >
        <input
          type="date"
          name="start"
          value={startInput}
          onChange={(e) => setStartInput(e.target.value)}
          className="input"
          style={{ width: 'auto' }}
        />
        <input
          type="date"
          name="end"
          value={endInput}
          onChange={(e) => setEndInput(e.target.value)}
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
                  <strong>Net sales</strong> (completed orders)
                </td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.net_sales ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Cost of goods sold (consumption + spoilage)</td>
                <td style={{ textAlign: 'right' }}>− ₱{(reportData.cogs ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Expenses (approved)</td>
                <td style={{ textAlign: 'right' }}>− ₱{(reportData.expenses ?? 0).toFixed(2)}</td>
              </tr>
              <tr style={{ borderTop: '2px solid var(--gray-300)' }}>
                <td>
                  <strong>Profit</strong>
                </td>
                <td
                  style={{
                    textAlign: 'right',
                    fontWeight: 700,
                    color: isLoss ? 'var(--color-error)' : 'var(--color-success)',
                  }}
                >
                  ₱{(reportData.profit ?? 0).toFixed(2)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

export default ProfitLossReport;