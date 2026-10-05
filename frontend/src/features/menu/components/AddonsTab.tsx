import React, { useState, useEffect } from 'react';
import { getAddons, createAddon, updateAddon, deleteAddon } from '../api/menu';
import type { Addon, ApiErrorResponse } from '../types/menu.types';

export const AddonsTab: React.FC = () => {
  const [addons, setAddons] = useState<Addon[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form / Modal States
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingAddon, setEditingAddon] = useState<Addon | null>(null);
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [isAvailable, setIsAvailable] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ name?: string; price?: string }>({});

  // Delete Modal States
  const [deletingAddon, setDeletingAddon] = useState<Addon | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchAddonsData = async () => {
    try {
      setLoading(true);
      const data = await getAddons();
      setAddons(data);
    } catch (err) {
      setErrorMessage('Failed to load add-ons.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAddonsData();
  }, []);

  const handleOpenForm = (addon?: Addon) => {
    setFieldErrors({});
    if (addon) {
      setEditingAddon(addon);
      setName(addon.name);
      setPrice(addon.price.toString());
      setIsAvailable(addon.is_available);
    } else {
      setEditingAddon(null);
      setName('');
      setPrice('');
      setIsAvailable(true);
    }
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingAddon(null);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFieldErrors({});

    const payload = {
      name,
      price: parseFloat(price) || 0,
      is_available: isAvailable,
    };

    try {
      if (editingAddon) {
        const updated = await updateAddon(editingAddon.id, payload);
        setAddons((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      } else {
        const created = await createAddon(payload);
        setAddons((prev) => [...prev, created]);
      }
      handleCloseForm();
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};
      setFieldErrors({
        name: Array.isArray(apiErr.name) ? apiErr.name[0] : undefined,
        price: Array.isArray(apiErr.price) ? apiErr.price[0] : undefined,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingAddon) return;
    setIsDeleting(true);

    try {
      await deleteAddon(deletingAddon.id);
      setAddons((prev) => prev.filter((item) => item.id !== deletingAddon.id));
      setDeletingAddon(null);
    } catch (err) {
      setErrorMessage('Failed to delete add-on.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return <div>Loading add-ons...</div>;
  }

  return (
    <div className="addons-tab">
      {/* Heading & Top Bar */}
      <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Add-Ons</h2>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Extra items customers can add to their orders.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenForm()}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '0.5rem' }}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add add-on
        </button>
      </div>

      {errorMessage && <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>{errorMessage}</div>}

      {/* Table Section */}
      <div className="table-card">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e5e7eb', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Name</th>
              <th style={{ padding: '0.75rem 1rem' }}>Price</th>
              <th style={{ padding: '0.75rem 1rem' }}>Status</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {addons.length > 0 ? (
              addons.map((addon) => (
                <tr key={addon.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem' }}>{addon.name}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>₱{Number(addon.price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {addon.is_available ? (
                      <span className="badge badge-success">Available</span>
                    ) : (
                      <span className="badge badge-warning">Unavailable</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleOpenForm(addon)} style={{ marginRight: '0.5rem' }}>
                      Edit
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setDeletingAddon(addon)} style={{ color: '#ef4444' }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="empty-state" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                  <h3>No add-ons yet</h3>
                  <p style={{ color: '#6b7280' }}>Create add-ons like extra rice or extra egg.</p>
                  <button className="btn btn-primary" onClick={() => handleOpenForm()} style={{ marginTop: '0.5rem' }}>
                    Add add-on
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Create / Edit Modal Form */}
      {isFormOpen && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div className="modal" style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '8px', width: '100%', maxWidth: '420px' }}>
            <h3>{editingAddon ? 'Edit' : 'Add'} Add-On</h3>
            <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '1rem' }}>
              Extra items customers can add to their orders.
            </p>

            <form onSubmit={handleFormSubmit} noValidate>
              <div className="field" style={{ marginBottom: '1rem' }}>
                <label htmlFor="name" style={{ display: 'block', marginBottom: '0.25rem' }}>Name</label>
                <input
                  type="text"
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={saving}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
                {fieldErrors.name && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.name}</span>}
              </div>

              <div className="field" style={{ marginBottom: '1rem' }}>
                <label htmlFor="price" style={{ display: 'block', marginBottom: '0.25rem' }}>Price (₱)</label>
                <input
                  type="number"
                  step="0.01"
                  id="price"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  disabled={saving}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
                {fieldErrors.price && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.price}</span>}
              </div>

              <div className="field" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="is_available"
                  checked={isAvailable}
                  onChange={(e) => setIsAvailable(e.target.checked)}
                  disabled={saving}
                />
                <label htmlFor="is_available">Available for ordering</label>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={handleCloseForm} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : `${editingAddon ? 'Save' : 'Create'} Add-On`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingAddon && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div className="modal" style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '8px', width: '100%', maxWidth: '400px' }}>
            <h3>Delete Add-On</h3>
            <p>Are you sure you want to delete <strong>{deletingAddon.name}</strong>?</p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" onClick={() => setDeletingAddon(null)} disabled={isDeleting}>
                Cancel
              </button>
              <button className="btn btn-primary" onClick={handleDelete} disabled={isDeleting} style={{ backgroundColor: '#ef4444' }}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};