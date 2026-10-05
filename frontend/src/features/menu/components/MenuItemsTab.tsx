import React, { useState, useEffect } from 'react';
import { getMenuItems, createMenuItem, updateMenuItem, toggleMenuItemAvailability, toggleMenuItemAddon, deleteMenuItem, getCategories, getAddons } from '../api/menu';
import type { MenuItem, Category, Addon, ApiErrorResponse } from '../types/menu.types';

interface MenuItemsTabProps {
  onViewPriceHistory?: (item: MenuItem) => void;
}

export const MenuItemsTab: React.FC<MenuItemsTabProps> = ({ onViewPriceHistory }) => {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [availableAddons, setAvailableAddons] = useState<Addon[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');

  // Form / Modal States
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [name, setName] = useState('');
  const [category, setCategory] = useState<string>('');
  const [price, setPrice] = useState('');
  const [prepMinutes, setPrepMinutes] = useState('10');
  const [description, setDescription] = useState('');
  const [isAvailable, setIsAvailable] = useState(true);
  const [selectedAddonIds, setSelectedAddonIds] = useState<number[]>([]);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string | undefined }>({});

  // Delete Modal
  const [deletingItem, setDeletingItem] = useState<MenuItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [itemsData, catsData, addonsData] = await Promise.all([
        getMenuItems({ q: searchQuery, category: selectedCategory }),
        getCategories(),
        getAddons(),
      ]);
      setItems(itemsData);
      setCategories(catsData);
      setAvailableAddons(addonsData);
    } catch (err) {
      setErrorMessage('Failed to load menu items.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInitialData();
  }, [selectedCategory]);

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const itemsData = await getMenuItems({ q: searchQuery, category: selectedCategory });
      setItems(itemsData);
    } catch (err) {
      setErrorMessage('Failed to search menu items.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAvailability = async (item: MenuItem) => {
    try {
      const updated = await toggleMenuItemAvailability(item.id);
      setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
    } catch (err) {
      // Fallback optimistic update
      setItems((prev) =>
        prev.map((i) => (i.id === item.id ? { ...i, is_available: !i.is_available } : i))
      );
    }
  };

  const handleOpenForm = (item?: MenuItem) => {
    setFieldErrors({});
    if (item) {
      setEditingItem(item);
      setName(item.name);
      setCategory(item.category ? item.category.toString() : '');
      setPrice(item.price.toString());
      setPrepMinutes(item.prep_minutes ? item.prep_minutes.toString() : '10');
      setDescription(item.description || '');
      setIsAvailable(item.is_available);
      setImagePreview(item.image || null);
      setImageFile(null);
      
      const attachedIds = item.addon_ids || item.addons?.map((a) => a.id) || [];
      setSelectedAddonIds(attachedIds);
    } else {
      setEditingItem(null);
      setName('');
      setCategory('');
      setPrice('');
      setPrepMinutes('10');
      setDescription('');
      setIsAvailable(true);
      setImagePreview(null);
      setImageFile(null);
      setSelectedAddonIds([]);
    }
    setIsFormOpen(true);
  };

  const handleCloseForm = () => {
    setIsFormOpen(false);
    setEditingItem(null);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleAddonToggleInForm = async (addonId: number) => {
    const isCurrentlyAttached = selectedAddonIds.includes(addonId);
    const updatedIds = isCurrentlyAttached
      ? selectedAddonIds.filter((id) => id !== addonId)
      : [...selectedAddonIds, addonId];
    
    setSelectedAddonIds(updatedIds);

    // If editing existing item, trigger endpoint sync
    if (editingItem) {
      try {
        await toggleMenuItemAddon(editingItem.id, addonId);
      } catch (err) {
        console.error('Failed to sync add-on toggle');
      }
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFieldErrors({});

    const formData = new FormData();
    formData.append('name', name);
    if (category) formData.append('category', category);
    formData.append('price', price);
    formData.append('prep_minutes', prepMinutes);
    formData.append('description', description);
    formData.append('is_available', String(isAvailable));

    if (imageFile) {
      formData.append('image', imageFile);
    }

    selectedAddonIds.forEach((id) => formData.append('addon_ids', String(id)));

    try {
      if (editingItem) {
        const updated = await updateMenuItem(editingItem.id, formData);
        setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
      } else {
        const created = await createMenuItem(formData);
        setItems((prev) => [...prev, created]);
      }
      handleCloseForm();
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};
      setFieldErrors({
        name: Array.isArray(apiErr.name) ? apiErr.name[0] : undefined,
        category: Array.isArray(apiErr.category) ? apiErr.category[0] : undefined,
        price: Array.isArray(apiErr.price) ? apiErr.price[0] : undefined,
        prep_minutes: Array.isArray(apiErr.prep_minutes) ? apiErr.prep_minutes[0] : undefined,
        image: Array.isArray(apiErr.image) ? apiErr.image[0] : undefined,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deletingItem) return;
    setIsDeleting(true);

    try {
      await deleteMenuItem(deletingItem.id);
      setItems((prev) => prev.filter((i) => i.id !== deletingItem.id));
      setDeletingItem(null);
    } catch (err) {
      setErrorMessage('Failed to delete menu item.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading && items.length === 0) {
    return <div>Loading menu items...</div>;
  }

  return (
    <div className="menu-items-tab">
      {/* Top Header Bar */}
      <div className="page-heading" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ margin: 0 }}>Menu Items</h2>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Manage your sellable items, prices, and availability.
          </p>
        </div>
        <button className="btn btn-primary" onClick={() => handleOpenForm()}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '0.5rem' }}>
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add menu item
        </button>
      </div>

      {/* Filters Bar */}
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem', flex: '1', maxWidth: '400px' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name..."
            className="input"
            style={{ flex: 1, padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
          />
          <button type="submit" className="btn btn-secondary btn-sm">Search</button>
        </form>

        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="input"
          style={{ width: 'auto', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
        >
          <option value="">All categories</option>
          {categories.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
      </div>

      {errorMessage && <div className="alert alert-danger" style={{ marginBottom: '1rem' }}>{errorMessage}</div>}

      {/* Table Section */}
      <div className="table-card">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #e5e7eb', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Name</th>
              <th style={{ padding: '0.75rem 1rem' }}>Category</th>
              <th style={{ padding: '0.75rem 1rem' }}>Price</th>
              <th style={{ padding: '0.75rem 1rem' }}>Prep Time</th>
              <th style={{ padding: '0.75rem 1rem' }}>Status</th>
              <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.length > 0 ? (
              items.map((item) => (
                <tr key={item.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 500 }}>{item.name}</td>
                  <td style={{ padding: '0.75rem 1rem', color: '#6b7280' }}>
                    {item.category_name || categories.find((c) => c.id === item.category)?.name || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>₱{Number(item.price).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{item.prep_minutes ?? 10} min</td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {item.is_available ? (
                      <span className="badge badge-success">Available</span>
                    ) : (
                      <span className="badge badge-warning">Unavailable</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => handleToggleAvailability(item)} style={{ marginRight: '0.25rem' }}>
                      {item.is_available ? 'Hide' : 'Show'}
                    </button>
                    {onViewPriceHistory && (
                      <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => onViewPriceHistory?.(item)}
                            style={{ marginRight: '0.25rem' }}
                        >
                            History
                        </button>
                    )}
                    <button className="btn btn-ghost btn-sm" onClick={() => handleOpenForm(item)} style={{ marginRight: '0.25rem' }}>
                      Edit
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setDeletingItem(item)} style={{ color: '#ef4444' }}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="empty-state" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                  <h3>No menu items yet</h3>
                  <p style={{ color: '#6b7280' }}>Add your first menu item to get started.</p>
                  <button className="btn btn-primary" onClick={() => handleOpenForm()} style={{ marginTop: '0.5rem' }}>
                    Add menu item
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Form Modal (Replaces menu_form.html) */}
      {isFormOpen && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '1rem' }}>
          <div className="modal" style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '8px', width: '100%', maxWidth: '560px', maxHeight: '90vh', overflowY: 'auto' }}>
            <h3>{editingItem ? 'Edit' : 'Add'} Menu Item</h3>
            <p style={{ color: '#6b7280', fontSize: '0.875rem', marginBottom: '1.25rem' }}>
              Set up a sellable item for your menu.
            </p>

            <form onSubmit={handleFormSubmit} noValidate>
              {/* Basic Info Section */}
              <div className="settings-section" style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#374151', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.25rem', marginBottom: '0.75rem' }}>
                  Basic Info
                </h4>

                <div className="field" style={{ marginBottom: '0.75rem' }}>
                  <label htmlFor="itemName" style={{ display: 'block', marginBottom: '0.25rem' }}>Name</label>
                  <input
                    type="text"
                    id="itemName"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={saving}
                    style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                  {fieldErrors.name && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.name}</span>}
                </div>

                <div className="field" style={{ marginBottom: '0.75rem' }}>
                  <label htmlFor="itemCategory" style={{ display: 'block', marginBottom: '0.25rem' }}>Category</label>
                  <select
                    id="itemCategory"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    disabled={saving}
                    style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  >
                    <option value="">Select category...</option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                  {fieldErrors.category && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.category}</span>}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <div className="field" style={{ flex: 1, marginBottom: '0.75rem' }}>
                    <label htmlFor="itemPrice" style={{ display: 'block', marginBottom: '0.25rem' }}>Price (₱)</label>
                    <input
                      type="number"
                      step="0.01"
                      id="itemPrice"
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                      disabled={saving}
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                    />
                    {fieldErrors.price && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.price}</span>}
                  </div>

                  <div className="field" style={{ flex: 1, marginBottom: '0.75rem' }}>
                    <label htmlFor="prepMinutes" style={{ display: 'block', marginBottom: '0.25rem' }}>Prep Time (min)</label>
                    <input
                      type="number"
                      id="prepMinutes"
                      value={prepMinutes}
                      onChange={(e) => setPrepMinutes(e.target.value)}
                      disabled={saving}
                      style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                    />
                    {fieldErrors.prep_minutes && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.prep_minutes}</span>}
                  </div>
                </div>

                <div className="field" style={{ marginBottom: '0.75rem' }}>
                  <label htmlFor="itemDescription" style={{ display: 'block', marginBottom: '0.25rem' }}>Description</label>
                  <textarea
                    id="itemDescription"
                    rows={2}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    disabled={saving}
                    style={{ width: '100%', padding: '0.5rem', border: '1px solid #d1d5db', borderRadius: '4px' }}
                  />
                </div>
              </div>

              {/* Image Section */}
              <div className="settings-section" style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#374151', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.25rem', marginBottom: '0.75rem' }}>
                  Image
                </h4>
                <div className="field">
                  <input
                    type="file"
                    id="itemImage"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageChange}
                    disabled={saving}
                  />
                  <small style={{ display: 'block', color: '#6b7280', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                    JPEG, PNG, or WebP. Max 5 MB.
                  </small>
                  {fieldErrors.image && <span className="error-message" style={{ color: '#ef4444', fontSize: '0.75rem' }}>{fieldErrors.image}</span>}
                </div>
                {imagePreview && (
                  <div style={{ marginTop: '0.5rem' }}>
                    <img src={imagePreview} alt="Preview" style={{ maxWidth: '160px', borderRadius: '6px', border: '1px solid #e5e7eb' }} />
                  </div>
                )}
              </div>

              {/* Availability Section */}
              <div className="settings-section" style={{ marginBottom: '1.25rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#374151', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.25rem', marginBottom: '0.75rem' }}>
                  Availability
                </h4>
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    checked={isAvailable}
                    onChange={(e) => setIsAvailable(e.target.checked)}
                    disabled={saving}
                  />
                  <span>Available for ordering</span>
                </label>
              </div>

              {/* Add-Ons Section */}
              <div className="settings-section" style={{ marginBottom: '1.5rem' }}>
                <h4 style={{ fontSize: '0.9rem', color: '#374151', borderBottom: '1px solid #e5e7eb', paddingBottom: '0.25rem', marginBottom: '0.75rem' }}>
                  Add-Ons
                </h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {availableAddons.length > 0 ? (
                    availableAddons.map((addon) => (
                      <label
                        key={addon.id}
                        style={{
                          background: '#f9fafb',
                          padding: '0.375rem 0.625rem',
                          borderRadius: '6px',
                          border: '1px solid #e5e7eb',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.375rem',
                          fontSize: '0.85rem',
                          cursor: 'pointer',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={selectedAddonIds.includes(addon.id)}
                          onChange={() => handleAddonToggleInForm(addon.id)}
                          disabled={saving}
                        />
                        <span>{addon.name} (₱{Number(addon.price).toFixed(2)})</span>
                      </label>
                    ))
                  ) : (
                    <p style={{ color: '#9ca3af', fontSize: '0.85rem' }}>No add-ons created yet.</p>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={handleCloseForm} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Saving...' : `${editingItem ? 'Save' : 'Create'} Menu Item`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingItem && (
        <div className="modal-overlay" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
          <div className="modal" style={{ backgroundColor: '#fff', padding: '1.5rem', borderRadius: '8px', width: '100%', maxWidth: '400px' }}>
            <h3>Delete Menu Item</h3>
            <p>
              Are you sure you want to delete <strong>{deletingItem.name}</strong>? This is a soft delete — the item will remain in historical records.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
              <button className="btn btn-secondary" onClick={() => setDeletingItem(null)} disabled={isDeleting}>
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