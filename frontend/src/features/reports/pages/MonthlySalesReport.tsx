import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { MonthlySalesData, MonthlySalesDayItem } from '../types/reports.types';

export const MonthlySalesReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const currentDate = new Date();
  const defaultYear = searchParams.get('year') || currentDate.getFullYear().toString();
  const defaultMonth = searchParams.get('month') || (currentDate.getMonth() + 1).toString();

  const [reportData, setReportData] = useState<MonthlySalesData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [yearInput, setYearInput] = useState<string>(defaultYear);
  const [monthInput, setMonthInput] = useState<string>(defaultMonth);

  const fetchMonthlySales = useCallback(async () => {
    setLoading(true);
    try {
      const params: { year?: number; month?: number } = {};
      const yParam = searchParams.get('year');
      const mParam = searchParams.get('month');
      if (yParam) params.year = Number(yParam);
      if (mParam) params.month = Number(mParam);

      const res = await reportsApi.getMonthlySales(params);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load monthly sales report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchMonthlySales();
  }, [fetchMonthlySales]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams: Record<string, string> = {};
    if (yearInput) newParams.year = yearInput;
    if (monthInput) newParams.month = monthInput;
    setSearchParams(newParams);
  };

  const handleCsvExport = () => {
    const y = searchParams.get('year') || yearInput;
    const m = searchParams.get('month') || monthInput;
    window.open(`/api/v1/reports/monthly-sales/?year=${y}&month=${m}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Monthly Sales Report...</div>;
  }

  const monthFormatted = reportData?.month?.formatted || `${yearInput}-${monthInput.padStart(2, '0')}`;

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Monthly Sales Report</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-132 — daily totals compared to the previous month.
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
          type="number"
          name="year"
          value={yearInput}
          onChange={(e) => setYearInput(e.target.value)}
          className="input"
          style={{ width: '90px' }}
        />
        <input
          type="number"
          name="month"
          value={monthInput}
          onChange={(e) => setMonthInput(e.target.value)}
          min={1}
          max={12}
          className="input"
          style={{ width: '80px' }}
        />
        <button type="submit" className="btn btn-secondary btn-sm">
          Show
        </button>
      </form>

      {reportData && (
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>Day</th>
                <th style={{ textAlign: 'right' }}>Sales ({monthFormatted})</th>
                <th style={{ textAlign: 'right' }}>Previous month</th>
                <th style={{ textAlign: 'right' }}>Change</th>
              </tr>
            </thead>
            <tbody>
              {reportData.days.length === 0 ? (
                <tr>
                  <td colSpan={4} className="empty-state">
                    <h3>No sales data for this month</h3>
                  </td>
                </tr>
              ) : (
                reportData.days.map((d: MonthlySalesDayItem, idx: number) => {
                  const hasChange = d.change !== null && d.change !== undefined;
                  const isNegative = hasChange && Number(d.change) < 0;

                  return (
                    <tr key={idx}>
                      <td>{d.day}</td>
                      <td style={{ textAlign: 'right' }}>₱{(d.total ?? 0).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }}>₱{(d.prev ?? 0).toFixed(2)}</td>
                      <td style={{ textAlign: 'right' }}>
                        {hasChange ? (
                          <span
                            style={{
                              color: isNegative ? 'var(--color-error)' : 'var(--color-success)',
                            }}
                          >
                            {(Number(d.change) || 0).toFixed(2)}%
                          </span>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
            <tfoot>
              <tr style={{ borderTop: '2px solid var(--gray-300)', fontWeight: 700 }}>
                <td>Month total</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.month_total ?? 0).toFixed(2)}</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.prev_total ?? 0).toFixed(2)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </>
  );
};

export default MonthlySalesReport;