import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ordersApi } from '../api/orders';
import type { TableListItem, TableStatus, UserRole } from '../types/orders.types';

export const TableList: React.FC = () => {
  const [tables, setTables] = useState<TableListItem[]>([]);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionId, setActionId] = useState<number | null>(null);

  const fetchTables = useCallback(async () => {
  setLoading(true);
  try {
    const response = await ordersApi.getTableList();
    
    // Cast as any or check type to safely extract tables and currentUserRole
    const rawData = response as any;
    
    const tableData: TableListItem[] = Array.isArray(rawData)
      ? rawData
      : rawData.tables || rawData.results || [];

    setTables(tableData);
    
    // Safely check if currentUserRole exists on rawData before setting it
    if (!Array.isArray(rawData) && rawData.currentUserRole) {
      setUserRole(rawData.currentUserRole);
    }
    
    setError(null);
  } catch (err: any) {
    setError(err.response?.data?.detail || 'Failed to load tables.');
  } finally {
    setLoading(false);
  }
}, []);

  useEffect(() => {
    fetchTables();
  }, [fetchTables]);

  const handleStatusChange = async (tableId: number, status: TableStatus) => {
    setActionId(tableId);
    try {
      await ordersApi.updateTableStatus(tableId, status);
      await fetchTables();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update table status.');
    } finally {
      setActionId(null);
    }
  };

  const handleDelete = async (tableId: number) => {
    if (!window.confirm('Are you sure you want to delete this table?')) return;
    setActionId(tableId);
    try {
      await ordersApi.deleteTable(tableId);
      await fetchTables();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete table.');
    } finally {
      setActionId(null);
    }
  };

  // If userRole isn't explicitly passed in response, default canManageTables to true for admins/managers
  const canManageTables = userRole === null || userRole === 'OWNER' || userRole === 'MANAGER';

  const getBorderColor = (status: TableStatus) => {
    switch (status) {
      case 'AVAILABLE':
        return 'var(--tapsi-600)';
      case 'OCCUPIED':
        return 'var(--color-error)';
      case 'RESERVED':
        return 'var(--tapsi-400)';
      default:
        return 'var(--tapsi-200)';
    }
  };

  const getBadgeClass = (status: TableStatus) => {
    switch (status) {
      case 'AVAILABLE':
        return 'badge badge-success';
      case 'OCCUPIED':
        return 'badge badge-warning';
      default:
        return 'badge badge-neutral';
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading tables...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Tables</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Color-coded table grid with running bills (FR-095).
          </p>
        </div>
        {canManageTables && (
          <Link className="btn btn-primary" to="/tables/create">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
            Add table
          </Link>
        )}
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        {tables.length === 0 ? (
          <div className="table-card empty-state" style={{ gridColumn: '1 / -1', padding: 'var(--space-6)', textAlign: 'center' }}>
            <h3>No tables yet</h3>
            <p style={{ marginBottom: 'var(--space-3)' }}>Add tables to start taking dine-in orders.</p>
            {canManageTables && (
              <Link to="/tables/create" className="btn btn-primary">
                Add table
              </Link>
            )}
          </div>
        ) : (
          tables.map((table) => {
            const isBusy = actionId === table.id;
            const hasOpenOrders = Boolean(table.open_orders && table.open_orders.length > 0);
            const runningBill = Number(table.running_bill ?? 0);

            return (
              <div
                key={table.id}
                className="table-card"
                style={{
                  padding: 'var(--space-4)',
                  borderLeft: `4px solid ${getBorderColor(table.status)}`,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: 'var(--font-size-lg)' }}>{table.name}</h3>
                  <span className={getBadgeClass(table.status)}>{table.status_display || table.status}</span>
                </div>

                <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
                  Seats {table.seating_capacity}
                </p>

                {hasOpenOrders && (
                  <>
                    <p style={{ marginTop: 'var(--space-2)', fontWeight: 700, color: 'var(--tapsi-700)' }}>
                      Bill: ₱{runningBill.toFixed(2)}
                    </p>
                    {table.open_orders?.map((order) => (
                      <React.Fragment key={order.id}>
                        <Link
                          to={`/orders/${order.id}`}
                          style={{ fontSize: 'var(--font-size-sm)', color: 'var(--tapsi-700)' }}
                        >
                          #{order.order_number} — {order.status_display || order.status}
                        </Link>
                        <br />
                      </React.Fragment>
                    ))}
                  </>
                )}

                {table.status === 'CLEANING' && userRole !== 'KITCHEN' && (
                  <div style={{ marginTop: 'var(--space-3)' }}>
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => handleStatusChange(table.id, 'AVAILABLE')}
                      disabled={isBusy}
                    >
                      {isBusy ? 'Saving...' : 'Mark available'}
                    </button>
                  </div>
                )}

                {table.status === 'OCCUPIED' && !hasOpenOrders && canManageTables && (
                  <div style={{ marginTop: 'var(--space-3)' }}>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleStatusChange(table.id, 'CLEANING')}
                      disabled={isBusy}
                    >
                      {isBusy ? 'Saving...' : 'Mark cleaning'}
                    </button>
                  </div>
                )}

                {canManageTables && (
                  <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-3)' }}>
                    <Link to={`/tables/${table.id}/edit`} className="btn btn-ghost btn-sm">
                      Edit
                    </Link>
                    {!hasOpenOrders && (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--color-error)' }}
                        onClick={() => handleDelete(table.id)}
                        disabled={isBusy}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </>
  );
};

export default TableList;