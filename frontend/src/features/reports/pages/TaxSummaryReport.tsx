import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { TaxSummaryData } from '../types/reports.types';

export const TaxSummaryReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const defaultStart =
    searchParams.get('start') ||
    new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0];
  const defaultEnd = searchParams.get('end') || new Date().toISOString().split('T')[0];

  const [reportData, setReportData] = useState<TaxSummaryData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [startInput, setStartInput] = useState<string>(defaultStart);
  const [endInput, setEndInput] = useState<string>(defaultEnd);

  const fetchTaxSummary = useCallback(async () => {
    setLoading(true);
    try {
      const params: { start?: string; end?: string } = {};
      const startParam = searchParams.get('start');
      const endParam = searchParams.get('end');
      if (startParam) params.start = startParam;
      if (endParam) params.end = endParam;

      const res = await reportsApi.getTaxSummary(params);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tax summary report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchTaxSummary();
  }, [fetchTaxSummary]);

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
    window.open(`/api/v1/reports/tax-summary/?start=${s}&end=${e}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Tax Summary Report...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Tax Summary</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-137 — VATable sales, VAT-exempt sales (Senior/PWD), and output VAT.
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
                <td>VATable sales</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.vatable ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>VAT-exempt sales (Senior/PWD)</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.exempt ?? 0).toFixed(2)}</td>
              </tr>
              <tr>
                <td>Discounts (Senior/PWD + manual)</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.discounts ?? 0).toFixed(2)}</td>
              </tr>
              <tr style={{ borderTop: '2px solid var(--gray-300)' }}>
                <td>
                  <strong>Output VAT (12%)</strong>
                </td>
                <td style={{ textAlign: 'right', fontWeight: 700 }}>
                  ₱{(reportData.output_vat ?? 0).toFixed(2)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

export default TaxSummaryReport;