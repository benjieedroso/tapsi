import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ordersApi } from '../api/orders';
import type { OrderType, TableOption, CreateOrderPayload } from '../types/orders.types';

export const OrderForm: React.FC = () => {
  const navigate = useNavigate();

  const [orderType, setOrderType] = useState<OrderType>('DINE_IN');
  const [tableId, setTableId] = useState<string>('');
  const [customerName, setCustomerName] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  const [tables, setTables] = useState<TableOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchMeta = async () => {
      try {
        const meta = await ordersApi.getOrderFormMeta();
        setTables(meta.available_tables || []);
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load form metadata.']);
      } finally {
        setLoading(false);
      }
    };
    fetchMeta();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload: CreateOrderPayload = {
      order_type: orderType,
      table_id: orderType === 'DINE_IN' && tableId ? Number(tableId) : null,
      customer_name: customerName,
      notes,
    };

    try {
      const createdOrder = await ordersApi.createOrder(payload);
      navigate(`/orders/${createdOrder.id}`);
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setNonFieldErrors(data.non_field_errors);
        }
        setFieldErrors(data);
      } else {
        setNonFieldErrors(['An unexpected error occurred while creating the order.']);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading order form...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>New Order</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Dine-in requires a table; delivery requires customer details (FR-080).
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        <form onSubmit={handleSubmit} noValidate>
          {nonFieldErrors.length > 0 && (
            <ul className="errorlist">
              {nonFieldErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}

          {/* Order Type Field */}
          <div className="field">
            <label htmlFor="id_order_type">Order type</label>
            <select
              id="id_order_type"
              name="order_type"
              className="input"
              value={orderType}
              onChange={(e) => setOrderType(e.target.value as OrderType)}
            >
              <option value="DINE_IN">Dine-In</option>
              <option value="TAKE_OUT">Take-Out</option>
              <option value="DELIVERY">Delivery</option>
            </select>
            {fieldErrors.order_type && (
              <ul className="errorlist">
                <li>{fieldErrors.order_type}</li>
              </ul>
            )}
          </div>

          {/* Table Field (Conditional for Dine-In) */}
          {orderType === 'DINE_IN' && (
            <div className="field">
              <label htmlFor="id_table">Table</label>
              <select
                id="id_table"
                name="table"
                className="input"
                value={tableId}
                onChange={(e) => setTableId(e.target.value)}
                required
              >
                <option value="">Select a table...</option>
                {tables.map((table) => (
                  <option key={table.id} value={table.id}>
                    {table.name}
                  </option>
                ))}
              </select>
              {fieldErrors.table_id && (
                <ul className="errorlist">
                  <li>{fieldErrors.table_id}</li>
                </ul>
              )}
            </div>
          )}

          {/* Customer Name Field */}
          <div className="field">
            <label htmlFor="id_customer_name">
              Customer name {orderType === 'DELIVERY' && <span style={{ color: 'var(--color-error)' }}>*</span>}
            </label>
            <input
              type="text"
              id="id_customer_name"
              name="customer_name"
              className="input"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              placeholder="e.g. John Doe"
              required={orderType === 'DELIVERY'}
            />
            {fieldErrors.customer_name && (
              <ul className="errorlist">
                <li>{fieldErrors.customer_name}</li>
              </ul>
            )}
          </div>

          {/* Notes Field */}
          <div className="field">
            <label htmlFor="id_notes">Notes</label>
            <textarea
              id="id_notes"
              name="notes"
              className="input"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Special instructions..."
            />
            {fieldErrors.notes && (
              <ul className="errorlist">
                <li>{fieldErrors.notes}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Creating...' : 'Create order'}
            </button>
            <Link to="/orders" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default OrderForm;