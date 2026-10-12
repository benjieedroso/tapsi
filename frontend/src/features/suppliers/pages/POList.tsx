import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';
import type { POListItem, POListResponse, SupplierOption } from '../types/suppliers.types';

export const POList: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<POListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || '');
  const [supplierFilter, setSupplierFilter] = useState<string>(searchParams.get('supplier') || '');

  const fetchPOList = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      const statusParam = searchParams.get('status');
      const supplierParam = searchParams.get('supplier');

      if (statusParam) params.status = statusParam;
      if (supplierParam) params.supplier = supplierParam;

      const res = await suppliersApi.getPOList(params);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load purchase orders.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchPOList();
  }, [fetchPOList]);

  const updateFilters = (newParams: Record<string, string>) => {
    const updated = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([key, val]) => {
      if (val) {
        updated.set(key, val);
      } else {
        updated.delete(key);
      }
    });
    setSearchParams(updated);
  };

  const getStatusBadgeClass = (status: string) => {
    if (status === 'RECEIVED') return 'badge-success';
    if (status === 'CANCELLED') return 'badge-warning';
    if (status === 'DRAFT') return 'badge-neutral';
    return '';
  };

  const pos = data?.pos || [];
  const suppliers = data?.suppliers || [];
  const statuses = data?.statuses || [];

  if (loading && !data) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading purchase orders...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Purchase Orders</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            DRAFT → ORDERED → PARTIALLY_RECEIVED → RECEIVED.
          </p>
        </div>
        <Link className="btn btn-primary" to="/suppliers/purchase-orders/create">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New purchase order
        </Link>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        method="get"
        style={{
          marginBottom: 'var(--space-4)',
          display: 'flex',
          gap: 'var(--space-3)',
          flexWrap: 'wrap',
        }}
      >
        <select
          name="status"
          className="input"
          style={{ width: 'auto' }}
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            updateFilters({ status: e.target.value, supplier: supplierFilter });
          }}
        >
          <option value="">All statuses</option>
          {statuses.map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </select>

        <select
          name="supplier"
          className="input"
          style={{ width: 'auto' }}
          value={supplierFilter}
          onChange={(e) => {
            setSupplierFilter(e.target.value);
            updateFilters({ status: statusFilter, supplier: e.target.value });
          }}
        >
          <option value="">All suppliers</option>
          {suppliers.map((sup: SupplierOption) => (
            <option key={sup.id} value={String(sup.id)}>
              {sup.name}
            </option>
          ))}
        </select>
      </form>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>PO Number</th>
              <th>Supplier</th>
              <th>Created</th>
              <th style={{ textAlign: 'right' }}>Total</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {pos.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-state">
                  <h3>No purchase orders</h3>
                  <p>Create a purchase order to start receiving stock.</p>
                  <Link to="/suppliers/purchase-orders/create" className="btn btn-primary" style={{ marginTop: 'var(--space-3)' }}>
                    New purchase order
                  </Link>
                </td>
              </tr>
            ) : (
              pos.map((po: POListItem) => (
                <tr key={po.id}>
                  <td>
                    <Link
                      to={`/suppliers/purchase-orders/${po.id}`}
                      style={{ color: 'var(--tapsi-700)', fontWeight: 600 }}
                    >
                      {po.po_number}
                    </Link>
                  </td>
                  <td>{po.supplier_name}</td>
                  <td>
                    {new Date(po.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td style={{ textAlign: 'right' }}>₱{(po.total ?? 0).toFixed(2)}</td>
                  <td>
                    <span className={`badge ${getStatusBadgeClass(po.status)}`}>
                      {po.status_display}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <Link to={`/suppliers/purchase-orders/${po.id}`} className="btn btn-ghost btn-sm">
                      View
                    </Link>
                    {po.status === 'DRAFT' && (
                      <Link to={`/suppliers/purchase-orders/${po.id}/edit`} className="btn btn-ghost btn-sm">
                        Edit
                      </Link>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default POList;