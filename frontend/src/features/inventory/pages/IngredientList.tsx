import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { inventoryApi } from '../api/inventory';
import type { IngredientListItem, LowStockAlert } from '../types/inventory.types';

export const IngredientList: React.FC = () => {
  const [ingredients, setIngredients] = useState<IngredientListItem[]>([]);
  const [openAlerts, setOpenAlerts] = useState<LowStockAlert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchInput, setSearchInput] = useState<string>('');
  const [lowStockFilter, setLowStockFilter] = useState<boolean>(false);

  // Delete modal state
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; name: string } | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);

  const fetchInventory = useCallback(async () => {
    setLoading(true);
    try {
      const params: { q?: string; low_stock?: string } = {};
      if (searchQuery) params.q = searchQuery;
      if (lowStockFilter) params.low_stock = '1';

      const response = await inventoryApi.getIngredientList(params);
      setIngredients(response.ingredients || []);
      setOpenAlerts(response.open_alerts || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load inventory data.');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, lowStockFilter]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await inventoryApi.deleteIngredient(deleteTarget.id);
      setDeleteTarget(null);
      await fetchInventory();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete ingredient.');
    } finally {
      setDeleting(false);
    }
  };

  if (loading && ingredients.length === 0) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading inventory...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Inventory</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Track ingredient stock with a complete transaction ledger.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <Link className="btn btn-secondary" to="/inventory/transactions/create">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Stock movement
          </Link>
          <Link className="btn btn-primary" to="/inventory/ingredients/create">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add ingredient
          </Link>
        </div>
      </div>

      {openAlerts.length > 0 && (
        <div className="alert alert-warning">
          <strong>Low stock: </strong>
          {openAlerts.map((alert, idx) => (
            <span key={alert.ingredient.id}>
              {alert.ingredient.name} ({alert.ingredient.current_stock} {alert.ingredient.unit_of_measure})
              {idx < openAlerts.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}

      {error && <div className="alert alert-danger">{error}</div>}

      <div style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 'var(--space-2)', flex: 1, maxWidth: '400px' }}>
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

        <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
          <label className="checkbox-label" style={{ whiteSpace: 'nowrap', cursor: 'pointer' }}>
            <input
              type="checkbox"
              name="low_stock"
              checked={lowStockFilter}
              onChange={(e) => setLowStockFilter(e.target.checked)}
            />
            <span>Low stock only</span>
          </label>
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Unit</th>
              <th>Current Stock</th>
              <th>Minimum</th>
              <th>Avg Cost</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {ingredients.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty-state">
                  <h3>No ingredients yet</h3>
                  <p>Add your first ingredient to start tracking stock.</p>
                  <Link to="/inventory/ingredients/create" className="btn btn-primary" style={{ marginTop: 'var(--space-3)' }}>
                    Add ingredient
                  </Link>
                </td>
              </tr>
            ) : (
              ingredients.map((ingredient) => {
                const currentStock = ingredient.stock ?? 0;
                const minStock = ingredient.minimum_stock ?? 0;
                const isLow = currentStock <= minStock;

                return (
                  <tr key={ingredient.id}>
                    <td>{ingredient.name}</td>
                    <td>{ingredient.unit_of_measure}</td>
                    <td>
                      {currentStock.toFixed(2)}
                      {isLow && <span className="badge badge-warning" style={{ marginLeft: 'var(--space-2)' }}>Low</span>}
                    </td>
                    <td>{minStock.toFixed(2)}</td>
                    <td>₱{(ingredient.average_unit_cost ?? 0).toFixed(2)}</td>
                    <td style={{ textAlign: 'right' }}>
                      <Link to={`/inventory/ingredients/${ingredient.id}/stock-card`} className="btn btn-ghost btn-sm">
                        Stock card
                      </Link>
                      <Link to={`/inventory/ingredients/${ingredient.id}/edit`} className="btn btn-ghost btn-sm">
                        Edit
                      </Link>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--color-error)' }}
                        onClick={() => setDeleteTarget({ id: ingredient.id, name: ingredient.name })}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {deleteTarget && (
        <div
          className="modal-overlay"
          style={{ display: 'flex' }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setDeleteTarget(null);
          }}
        >
          <div className="modal">
            <h3>Delete Ingredient</h3>
            <p>
              Are you sure you want to delete <strong>{deleteTarget.name}</strong>? Its transaction history is kept for the audit trail.
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
                style={{ background: 'var(--color-error)' }}
                onClick={handleDeleteConfirm}
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

export default IngredientList;