import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ordersApi } from '../api/orders';
import type { OrderListItem, OrderListFilterOptions } from '../types/orders.types';

interface OrderListProps {
  userRole?: string;
}

export const OrderList: React.FC<OrderListProps> = ({ userRole }) => {
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [filters, setFilters] = useState<OrderListFilterOptions>({
    statusChoices: [],
    typeChoices: [],
  });

  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ordersApi.getOrderList({
        status: selectedStatus || undefined,
        type: selectedType || undefined,
      });
      // Safely handle potential undefined/null arrays from the response
      setOrders(data?.orders || []);
      if (data?.filters) {
        setFilters(data.filters);
      }
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load orders.');
    } finally {
      setLoading(false);
    }
  }, [selectedStatus, selectedType]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'badge badge-success';
      case 'CANCELLED':
        return 'badge badge-warning';
      case 'READY':
        return 'badge';
      default:
        return 'badge badge-neutral';
    }
  };

  const statusChoices = filters?.statusChoices || [];
  const typeChoices = filters?.typeChoices || [];
  const safeOrders = orders || [];

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Orders</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Dine-in, take-out, and delivery orders.
          </p>
        </div>
        <Link className="btn btn-primary" to="/orders/create">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New order
        </Link>
      </div>

      <form
        onSubmit={(e) => e.preventDefault()}
        style={{ marginBottom: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)' }}
      >
        <select
          name="status"
          className="input"
          style={{ width: 'auto' }}
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          {statusChoices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>

        <select
          name="type"
          className="input"
          style={{ width: 'auto' }}
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
        >
          <option value="">All types</option>
          {typeChoices.map((choice) => (
            <option key={choice.value} value={choice.value}>
              {choice.label}
            </option>
          ))}
        </select>
      </form>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Order</th>
              <th>Type</th>
              <th>Table</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Total</th>
              <th>Cashier</th>
              <th>Created</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: 'var(--space-4)' }}>
                  Loading orders...
                </td>
              </tr>
            ) : safeOrders.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-state">
                  <h3>No orders yet</h3>
                  <p>Create your first order to start selling.</p>
                  <Link to="/orders/create" className="btn btn-primary">
                    New order
                  </Link>
                </td>
              </tr>
            ) : (
              safeOrders.map((order) => (
                <tr key={order.id}>
                  <td>
                    <Link
                      to={`/orders/${order.id}`}
                      style={{ color: 'var(--tapsi-700)', fontWeight: 600 }}
                    >
                      {order.order_number}
                    </Link>
                  </td>
                  <td>{order.order_type_display}</td>
                  <td>{order.table_name || '—'}</td>
                  <td>
                    <span className={getStatusBadgeClass(order.status)}>
                      {order.status_display}
                    </span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    ₱{parseFloat(order.total || '0').toFixed(2)}
                  </td>
                  <td>{order.created_by_name || '—'}</td>
                  <td>{order.created_at}</td>
                  <td style={{ textAlign: 'right' }}>
                    <Link to={`/orders/${order.id}`} className="btn btn-ghost btn-sm">
                      View
                    </Link>
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

export default OrderList;