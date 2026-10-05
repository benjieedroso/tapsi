import React, { useState, useEffect } from 'react';
import { getCategories, createCategory, updateCategory, deleteCategory } from '../api/menu';
import type { Category, ApiErrorResponse } from '../types/menu.types';

export const CategoriesTab: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form / Modal States
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [name, setName] = useState('');
  const [displayOrder, setDisplayOrder] = useState<number | string>(0);
  const [isActive, setIsActive] = useState(true);
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ name?: string; display_order?: string }>({});

  // Delete Modal States
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchCategoriesData = async () => {
    try {
      setLoading(true);
      const data = await getCategories();
      setCategories(data);
    } catch (err) {
      setErrorMessage('Failed to load categories.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategoriesData();
  }, []);

  const handleOpenForm = (category?: Category) => {
    setFieldErrors({});
    if (category) {
      setEditingCategory(category);
      setName(category.name);
      setDisplayOrder(category.display_order);
      setIsActive(category.is_active);
    } else {
      setEditingCategory(null);
      setName('');
      setDisplayOrder(categories.length + 1);
      setIsActive(true);
    }
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingCategory(null);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFieldErrors({});

    const payload = {
      name,
      display_order: typeof displayOrder === 'string' ? parseInt(displayOrder, 10) || 0 : displayOrder,
      is_active: isActive,
    };

    try {
      if (editingCategory) {
        const updated = await updateCategory(editingCategory.id, payload);
        setCategories((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      } else {
        const created = await createCategory(payload);
        setCategories((prev) => [...prev, created]);
      }
      handleCloseForm();
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};
      setFieldErrors({
        name: Array.isArray(apiErr.name) ? apiErr.name[0] : undefined,
        display_order: Array.isArray(apiErr.display_order) ? apiErr.display_order[0] : undefined,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingCategory) return;
    setIsDeleting(true);

    try {
      await deleteCategory(deletingCategory.id);
      setCategories((prev) => prev.filter((item) => item.id !== deletingCategory.id));
      setDeletingCategory(null);
    } catch (err) {
      setErrorMessage('Failed to delete category.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return <div>Loading categories...</div>;
  }

  return (
    <div className="categories-tab">
      {/* Page Heading & Top Action */}
      <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Menu Categories</h2>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Organize your menu items into groups.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenForm()}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '0.5rem' }}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add category
        </button>
      </div>

      {errorMessage && <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>{errorMessage}</div>}

      {/* Table Section */}
      <div className="table-card">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e5e7eb', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Order</th>
              <th style={{ padding: '0.75rem 1rem' }}>Name</th>
              <th style={{ padding: '0.75rem 1rem' }}>Items</th>
              <th style={{ padding: '0.75rem 1rem' }}>Status</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {categories.length > 0 ? (
              categories.map((cat) => (
                <tr key={cat.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem' }}>{cat.display_order}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{cat.name}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{cat.items_count ?? 0}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {cat.is_active ? (
                      <span className="badge badge-success">Active</span>
                    ) : (
                      <span className="badge badge-error" style={{ backgroundColor: '#fee2e2', color: '#991b1b', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem' }}>
                        Inactive
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleOpenForm(cat)} style={{ marginRight: '0.5rem' }}>
                      Edit
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setDeletingCategory(cat)} style={{ color: '#ef4444' }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="empty-state" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                  <h3>No categories yet</h3>
                  <p style={{ color: '#6b7280' }}>Create your first category to organize menu items.</p>
                  <button className="btn btn-primary" onClick={() => handleOpenForm()} style={{ marginTop: '0.5rem' }}>
                    Add category
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
          <div className="modal" style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '8px', width: '100%', maxWidth: '480px' }}>
            <h3>{editingCategory ? 'Edit' : 'Add'} Category</h3>
            <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '1rem' }}>
              Organize your menu items into groups.
            </p>

            <form onSubmit={handleFormSubmit} noValidate>
              <div className="field" style={{ marginBottom: '1rem' }}>
                <label htmlFor="categoryName" style={{ display: 'block', marginBottom: '0.25rem' }}>Category Name</label>
                <input
                  type="text"
                  id="categoryName"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={saving}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
                {fieldErrors.name && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.name}</span>}
              </div>

              <div className="field" style={{ marginBottom: '1rem' }}>
                <label htmlFor="displayOrder" style={{ display: 'block', marginBottom: '0.25rem' }}>Display Order</label>
                <input
                  type="number"
                  id="displayOrder"
                  value={displayOrder}
                  onChange={(e) => setDisplayOrder(e.target.value)}
                  disabled={saving}
                  style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                />
                <small style={{ color: '#6b7280', fontSize: '0.75rem' }}>Determines the sorting order on the menu display.</small>
                {fieldErrors.display_order && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem', display: 'block' }}>{fieldErrors.display_order}</span>}
              </div>

              <div className="field" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="is_active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  disabled={saving}
                />
                <label htmlFor="is_active">Active (visible on menu)</label>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={handleCloseForm} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : `${editingCategory ? 'Save' : 'Create'} Category`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingCategory && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div className="modal" style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '8px', width: '100%', maxWidth: '400px' }}>
            <h3>Delete Category</h3>
            <p>
              Are you sure you want to delete <strong>{deletingCategory.name}</strong>? Items in this category will become uncategorized.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" onClick={() => setDeletingCategory(null)} disabled={isDeleting}>
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