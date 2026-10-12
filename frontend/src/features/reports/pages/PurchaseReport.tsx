import React, { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { reportsApi } from '../api/reports';
import type { PurchaseReportData, PurchaseReportPORow } from '../types/reports.types';

export const PurchaseReport: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const defaultStart =
    searchParams.get('start') ||
    new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0];
  const defaultEnd = searchParams.get('end') || new Date().toISOString().split('T')[0];

  const [reportData, setReportData] = useState<PurchaseReportData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [startInput, setStartInput] = useState<string>(defaultStart);
  const [endInput, setEndInput] = useState<string>(defaultEnd);
  const [supplierInput, setSupplierInput] = useState<string>(searchParams.get('supplier') || '');

  const fetchPurchaseReport = useCallback(async () => {
    setLoading(true);
    try {
      const params: { start?: string; end?: string; supplier?: string } = {};
      const startParam = searchParams.get('start');
      const endParam = searchParams.get('end');
      const supplierParam = searchParams.get('supplier');

      if (startParam) params.start = startParam;
      if (endParam) params.end = endParam;
      if (supplierParam) params.supplier = supplierParam;

      const res = await reportsApi.getPurchaseReport(params);
      setReportData(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load purchase report.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchPurchaseReport();
  }, [fetchPurchaseReport]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newParams: Record<string, string> = {};
    if (startInput) newParams.start = startInput;
    if (endInput) newParams.end = endInput;
    if (supplierInput) newParams.supplier = supplierInput;
    setSearchParams(newParams);
  };

  const handleCsvExport = () => {
    const s = searchParams.get('start') || startInput;
    const e = searchParams.get('end') || endInput;
    const sup = searchParams.get('supplier') || supplierInput;
    window.open(`/api/v1/reports/purchases/?start=${s}&end=${e}&supplier=${sup}&export=1`, '_blank');
  };

  if (loading && !reportData) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading Purchase Report...</div>;
  }

  const suppliersList = reportData?.suppliers || [];

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Purchase Report</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            FR-136 — POs by supplier and range, with totals and outstanding balances.
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
          name="supplier"
          className="input"
          style={{ width: 'auto' }}
          value={supplierInput}
          onChange={(e) => setSupplierInput(e.target.value)}
        >
          <option value="">All suppliers</option>
          {suppliersList.map(([sid, sname]) => (
            <option key={sid} value={String(sid)}>
              {sname}
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
                <th>PO #</th>
                <th>Supplier</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Total</th>
                <th style={{ textAlign: 'right' }}>Received</th>
                <th style={{ textAlign: 'right' }}>Outstanding</th>
              </tr>
            </thead>
            <tbody>
              {reportData.rows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-state">
                    <h3>No purchase orders in range</h3>
                  </td>
                </tr>
              ) : (
                reportData.rows.map((row: PurchaseReportPORow, index: number) => (
                  <tr key={index}>
                    <td>{row.po.po_number}</td>
                    <td>{row.supplier}</td>
                    <td>
                      <span className="badge badge-secondary">{row.po.get_status_display}</span>
                    </td>
                    <td style={{ textAlign: 'right' }}>₱{(row.total ?? 0).toFixed(2)}</td>
                    <td style={{ textAlign: 'right' }}>₱{(row.received ?? 0).toFixed(2)}</td>
                    <td style={{ textAlign: 'right' }}>₱{(row.outstanding ?? 0).toFixed(2)}</td>
                  </tr>
                ))
              )}
            </tbody>
            <tfoot>
              <tr style={{ borderTop: '2px solid var(--gray-300)', fontWeight: 700 }}>
                <td colSpan={4}>Totals</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.total_received ?? 0).toFixed(2)}</td>
                <td style={{ textAlign: 'right' }}>₱{(reportData.total_outstanding ?? 0).toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </>
  );
};

export default PurchaseReport;