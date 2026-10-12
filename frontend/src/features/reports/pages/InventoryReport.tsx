import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { InventoryReportData, InventoryIngredientItem, InventoryUsageRow } from '../types/reports.types';

export const InventoryReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [reportData, setReportData] = useState<InventoryReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const defaultStart = searchParams.get('start') || new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0];
  const defaultEnd = searchParams.get('end') || new Date().toISOString().split('T')[0];

  const [startInput, setStartInput] = useState<string>(defaultStart);
  const [endInput, setEndInput] = useState<string>(defaultEnd);

  const fetchInventoryReport = useCallback(async () => {
    setLoading(true);
    try {
      const params: { start?: string; end?: string } = {};
      const startParam = searchParams.get('start');
      const endParam = searchParams.get('end');
      if (startParam) params.start = startParam;
      if (endParam) params.end = endParam;

      const res = await reportsApi.getInventoryReport(params);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load inventory report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchInventoryReport();
  }, [fetchInventoryReport]);

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
    window.open(`/api/v1/reports/inventory/?start=${s}&end=${e}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Inventory Report...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Inventory Report</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-134 — current stock levels, usage, and spoilage cost.
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
        <>
          <h2 className="page-heading" style={{ fontSize: 'var(--font-size-lg)' }}>
            Current stock levels
          </h2>
          <div className="table-card" style={{ marginBottom: 'var(--space-6)' }}>
            <table>
              <thead>
                <tr>
                  <th>Ingredient</th>
                  <th>Unit</th>
                  <th style={{ textAlign: 'right' }}>Stock</th>
                  <th style={{ textAlign: 'right' }}>Min</th>
                  <th style={{ textAlign: 'right' }}>Avg cost</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {reportData.ingredients.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-state">
                      <h3>No ingredients</h3>
                    </td>
                  </tr>
                ) : (
                  reportData.ingredients.map((ingredient: InventoryIngredientItem) => {
                    const isLowStock = ingredient.current_stock < ingredient.minimum_stock;
                    return (
                      <tr key={ingredient.id}>
                        <td>{ingredient.name}</td>
                        <td>{ingredient.unit_of_measure}</td>
                        <td style={{ textAlign: 'right' }}>{ingredient.current_stock}</td>
                        <td style={{ textAlign: 'right' }}>{ingredient.minimum_stock}</td>
                        <td style={{ textAlign: 'right' }}>₱{(ingredient.average_unit_cost ?? 0).toFixed(2)}</td>
                        <td>
                          {isLowStock && <span className="badge badge-warning">Low stock</span>}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 'var(--space-3)' }}>
            Usage by ingredient ({reportData.start} → {reportData.end})
          </h2>
          <div className="table-card">
            <table>
              <thead>
                <tr>
                  <th>Ingredient</th>
                  <th style={{ textAlign: 'right' }}>Quantity consumed</th>
                  <th style={{ textAlign: 'right' }}>Transactions</th>
                </tr>
              </thead>
              <tbody>
                {reportData.usage_rows.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="empty-state">
                      <h3>No consumption in range</h3>
                    </td>
                  </tr>
                ) : (
                  reportData.usage_rows.map((u: InventoryUsageRow, idx: number) => (
                    <tr key={idx}>
                      <td>{u.name}</td>
                      <td style={{ textAlign: 'right' }}>{u.qty}</td>
                      <td style={{ textAlign: 'right' }}>{u.count}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <p style={{ marginTop: 'var(--space-4)' }}>
            <strong>Spoilage cost in range:</strong> ₱{(reportData.spoilage_cost ?? 0).toFixed(2)}
          </p>
        </>
      )}
    </>
  );
};

export default InventoryReport;