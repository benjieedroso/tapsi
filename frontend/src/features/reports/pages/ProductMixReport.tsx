import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { ProductMixData, ProductMixRow, ProductCategoryOption } from '../types/reports.types';

export const ProductMixReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const defaultStart = searchParams.get('start') || new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0];
  const defaultEnd = searchParams.get('end') || new Date().toISOString().split('T')[0];

  const [reportData, setReportData] = useState<ProductMixData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [startInput, setStartInput] = useState<string>(defaultStart);
  const [endInput, setEndInput] = useState<string>(defaultEnd);
  const [categoryInput, setCategoryInput] = useState<string>(searchParams.get('category') || '');

  const fetchProductMix = useCallback(async () => {
    setLoading(true);
    try {
      const params: { start?: string; end?: string; category?: string } = {};
      const startParam = searchParams.get('start');
      const endParam = searchParams.get('end');
      const categoryParam = searchParams.get('category');

      if (startParam) params.start = startParam;
      if (endParam) params.end = endParam;
      if (categoryParam) params.category = categoryParam;

      const res = await reportsApi.getProductMix(params);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load product mix report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchProductMix();
  }, [fetchProductMix]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams: Record<string, string> = {};
    if (startInput) newParams.start = startInput;
    if (endInput) newParams.end = endInput;
    if (categoryInput) newParams.category = categoryInput;
    setSearchParams(newParams);
  };

  const handleCsvExport = () => {
    const s = searchParams.get('start') || startInput;
    const e = searchParams.get('end') || endInput;
    const c = searchParams.get('category') || categoryInput;
    window.open(`/api/v1/reports/product-mix/?start=${s}&end=${e}&category=${c}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Product Mix Report...</div>;
  }

  const categories = reportData?.categories || [];

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Product Mix Report</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-135 — best and least selling items by quantity and revenue.
          </p>
        </div>
        <button type="button" onClick={handleCsvExport} className="btn btn-secondary">
          Export CSV
        </button>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleFilterSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}
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
        <select
          name="category"
          className="input"
          style={{ width: 'auto' }}
          value={categoryInput}
          onChange={(e) => setCategoryInput(e.target.value)}
        >
          <option value="">All categories</option>
          {categories.map((c: ProductCategoryOption) => (
            <option key={c.id} value={String(c.id)}>
              {c.name}
            </option>
          ))}
        </select>
        <button type="submit" className="btn btn-secondary btn-sm">
          Show
        </button>
      </form>

      {reportData && (
        <div className="table-card">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Item</th>
                <th style={{ textAlign: 'right' }}>Quantity sold</th>
                <th style={{ textAlign: 'right' }}>Revenue</th>
                <th style={{ textAlign: 'right' }}>Line orders</th>
              </tr>
            </thead>
            <tbody>
              {reportData.rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty-state">
                    <h3>No sales in range</h3>
                  </td>
                </tr>
              ) : (
                reportData.rows.map((row: ProductMixRow, index: number) => (
                  <tr key={index}>
                    <td>{index + 1}</td>
                    <td>{row.item_name}</td>
                    <td style={{ textAlign: 'right' }}>{row.qty}</td>
                    <td style={{ textAlign: 'right' }}>₱{(row.revenue ?? 0).toFixed(2)}</td>
                    <td style={{ textAlign: 'right' }}>{row.count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

export default ProductMixReport;