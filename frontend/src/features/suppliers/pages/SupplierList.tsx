import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';
import type { SupplierListItem } from '../types/suppliers.types';

export const SupplierList: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [suppliers, setSuppliers] = useState<SupplierListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState<string>(searchParams.get('q') || '');

  // Delete modal state
  const [deleteTarget, setDeleteTarget] = useState<SupplierListItem | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);

  const fetchSuppliers = useCallback(async () => {
    setLoading(true);
    try {
      const params: { q?: string } = {};
      const qParam = searchParams.get('q');
      if (qParam) params.q = qParam;

      const res = await suppliersApi.getSupplierList(params);
      setSuppliers(res.suppliers || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load suppliers.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchSuppliers();
  }, [fetchSuppliers]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput) {
      setSearchParams({ q: searchInput });
    } else {
      setSearchParams({});
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    setDeleting(true);
    try {
      await suppliersApi.deleteSupplier(deleteTarget.id);
      setDeleteTarget(null);
      await fetchSuppliers();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete supplier.');
    } finally {
      setDeleting(false);
    }
  };

  if (loading && suppliers.length === 0) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading suppliers...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Suppliers</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Manage vendors and purchase orders.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Link className="btn btn-secondary" to="/suppliers/purchase-orders">
            Purchase Orders
          </Link>
          <Link className="btn btn-primary" to="/suppliers/create">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add supplier
          </Link>
        </div>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleSearchSubmit}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)', maxWidth: '400px' }}
      >
        <input
          type="text"
          name="q"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search by name..."
          className="input"
          style={{ flex: 1 }}
        />
        <button type="submit" className="btn btn-secondary btn-sm">
          Search
        </button>
      </form>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Contact</th>
              <th>Phone</th>
              <th>Terms</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-state">
                  <h3>No suppliers yet</h3>
                  <p>Add your first supplier to start purchasing.</p>
                  <Link to="/suppliers/create" className="btn btn-primary" style={{ marginTop: 'var(--space-3)' }}>
                    Add supplier
                  </Link>
                </td>
              </tr>
            ) : (
              suppliers.map((supplier: SupplierListItem) => (
                <tr key={supplier.id}>
                  <td>
                    <Link
                      to={`/suppliers/${supplier.id}`}
                      style={{ color: 'var(--tapsi-700)', fontWeight: 600 }}
                    >
                      {supplier.name}
                    </Link>
                  </td>
                  <td>{supplier.contact_person || '—'}</td>
                  <td>{supplier.phone || '—'}</td>
                  <td>{supplier.payment_terms_display}</td>
                  <td>
                    {supplier.is_active ? (
                      <span className="badge badge-success">Active</span>
                    ) : (
                      <span className="badge badge-warning">Inactive</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <Link to={`/suppliers/${supplier.id}/edit`} className="btn btn-ghost btn-sm">
                      Edit
                    </Link>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      style={{ color: 'var(--color-error)' }}
                      onClick={() => setDeleteTarget(supplier)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div
          className="modal-overlay"
          style={{ display: 'flex' }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setDeleteTarget(null);
          }}
        >
          <div className="modal">
            <h3>Delete Supplier</h3>
            <p>
              Delete <strong>{deleteTarget.name}</strong>? Suppliers with purchase history are deactivated instead.
            </p>
            <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end', marginTop: 'var(--space-6)' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setDeleteTarget(null)}
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{ background: 'var(--color-error)', borderColor: 'var(--color-error)' }}
                onClick={handleConfirmDelete}
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SupplierList;