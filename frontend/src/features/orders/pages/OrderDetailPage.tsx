import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ordersApi } from '../api/orders';
import type { OrderDetail, TableOption, MenuItemOption, UserRole, Shortfall } from '../types/orders.types';

interface OrderDetailPageProps {
  userRole?: string;
}

export const OrderDetailPage: React.FC<OrderDetailPageProps> = ({ userRole }) => {
  const { id } = useParams<{ id: string }>();
  const orderId = Number(id);

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [shortfalls, setShortfalls] = useState<Shortfall[]>([]);
  const [availableTables, setAvailableTables] = useState<TableOption[]>([]);
  const [menuItems, setMenuItems] = useState<MenuItemOption[]>([]);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Forms state
  const [transferTableId, setTransferTableId] = useState<string>('');
  const [newItemId, setNewItemId] = useState<string>('');
  const [newItemQty, setNewItemQty] = useState<number>(1);
  const [newItemNotes, setNewItemNotes] = useState<string>('');

  const [paymentMethod, setPaymentMethod] = useState<string>('CASH');
  const [paymentAmount, setPaymentAmount] = useState<string>('');

  const [discountType, setDiscountType] = useState<string>('PERCENTAGE');
  const [discountValue, setDiscountValue] = useState<string>('');
  const [discountRef, setDiscountRef] = useState<string>('');

  const [refundReasons, setRefundReasons] = useState<Record<number, string>>({});

  const fetchOrderData = useCallback(async () => {
    if (!orderId) return;
    try {
      const data = await ordersApi.getOrderDetail(orderId);
      setOrder(data.order);
      setShortfalls(data.shortfalls || []);
      setAvailableTables(data.availableTables || []);
      setMenuItems(data.menuItems || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load order details.');
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    fetchOrderData();
  }, [fetchOrderData]);

  if (loading) return <div className="p-4">Loading order...</div>;
  if (error || !order) return <div className="alert alert-danger">{error || 'Order not found.'}</div>;

  const isCompletedOrCancelled = order.status === 'COMPLETED' || order.status === 'CANCELLED';
  const isOwnerOrManager = userRole === 'OWNER' || userRole === 'MANAGER';

  // Action Handlers
  const handleComplete = async () => {
    try {
      const updated = await ordersApi.completeOrder(orderId);
      setOrder(updated);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to complete order.');
    }
  };

  const handleCancel = async () => {
    const reason = prompt(`Reason for cancelling ${order.order_number}?`);
    if (!reason) return;
    try {
      const updated = await ordersApi.cancelOrder(orderId, reason);
      setOrder(updated);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel order.');
    }
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transferTableId) return;
    try {
      const updated = await ordersApi.transferTable(orderId, Number(transferTableId));
      setOrder(updated);
      setTransferTableId('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to transfer table.');
    }
  };

  const handleApproveDiscount = async () => {
    try {
      const updated = await ordersApi.approveDiscount(orderId);
      setOrder(updated);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve discount.');
    }
  };

  const handleAddItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItemId) return;
    try {
      const updated = await ordersApi.addItem(orderId, {
        item_id: Number(newItemId),
        quantity: newItemQty,
        notes: newItemNotes,
      });
      setOrder(updated);
      setNewItemId('');
      setNewItemQty(1);
      setNewItemNotes('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add item.');
    }
  };

  const handleRemoveItem = async (itemId: number) => {
    try {
      const updated = await ordersApi.removeItem(orderId, itemId);
      setOrder(updated);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove item.');
    }
  };

  const handleRecordPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!paymentAmount) return;
    try {
      const updated = await ordersApi.recordPayment(orderId, {
        method: paymentMethod,
        amount: parseFloat(paymentAmount),
      });
      setOrder(updated);
      setPaymentAmount('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to record payment.');
    }
  };

  const handleApplyDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!discountValue) return;
    try {
      const updated = await ordersApi.applyDiscount(orderId, {
        discount_type: discountType,
        value: parseFloat(discountValue),
        ref: discountRef,
      });
      setOrder(updated);
      setDiscountValue('');
      setDiscountRef('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to apply discount.');
    }
  };

  const handleRefund = async (paymentId: number) => {
    const reason = refundReasons[paymentId];
    if (!reason) {
      alert('Please state a reason for refunding.');
      return;
    }
    try {
      await ordersApi.refundPayment(paymentId, reason);
      fetchOrderData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to refund payment.');
    }
  };

  return (
    <div className="order-detail-container">
      {/* Top Header */}
      <div className="page-heading">
        <div>
          <h1>Order {order.order_number}</h1>
          <p className="subtext">
            {order.order_type_display}
            {order.table ? ` · Table ${order.table.name}` : ''}
            {order.customer_name ? ` · ${order.customer_name}` : ''}
            {' · '}
            <span
              className={`badge ${
                order.status === 'COMPLETED'
                  ? 'badge-success'
                  : order.status === 'CANCELLED'
                  ? 'badge-warning'
                  : 'badge-neutral'
              }`}
            >
              {order.status_display}
            </span>
          </p>
        </div>

        <div className="action-button-group">
          {!isCompletedOrCancelled && (
            <>
              {userRole !== 'KITCHEN' && (
                <button
                  onClick={handleComplete}
                  className="btn btn-primary"
                  title={
                    Number(order.outstanding_balance) > 0
                      ? `Outstanding balance: ₱${order.outstanding_balance}`
                      : undefined
                  }
                >
                  Complete
                </button>
              )}
              {isOwnerOrManager && (
                <button onClick={handleCancel} className="btn btn-secondary btn-danger-text">
                  Cancel order
                </button>
              )}
            </>
          )}

          {order.status === 'COMPLETED' && (
            <>
              <Link className="btn btn-secondary" to={`/orders/${order.id}/receipt`}>
                Receipt
              </Link>
              <Link className="btn btn-ghost btn-sm" to={`/orders/${order.id}/receipt/reprint`}>
                Reprint
              </Link>
            </>
          )}

          {order.status === 'PENDING' && order.order_type === 'DINE_IN' && (
            <form onSubmit={handleTransfer} className="inline-form">
              <select
                value={transferTableId}
                onChange={(e) => setTransferTableId(e.target.value)}
                className="input input-compact"
                required
              >
                <option value="">Transfer to…</option>
                {availableTables.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
              <button type="submit" className="btn btn-ghost btn-sm">
                Transfer
              </button>
            </form>
          )}
        </div>
      </div>

      {/* Shortfalls Warning */}
      {shortfalls.length > 0 && (
        <div className="alert alert-warning">
          <strong>Projected stock warning: </strong>
          {shortfalls.map((s, idx) => (
            <span key={idx}>
              {s.ingredient_name} (need {s.need}, have {s.have})
              {idx < shortfalls.length - 1 ? ', ' : ''}
            </span>
          ))}
        </div>
      )}

      {/* Discount Approval Banner */}
      {order.discount_needs_approval && (
        <div className="alert alert-warning flex-between">
          <span>
            <strong>Discount requires approval</strong> — manual discount above 10%.
          </span>
          {isOwnerOrManager && (
            <button onClick={handleApproveDiscount} className="btn btn-primary btn-sm">
              Approve
            </button>
          )}
        </div>
      )}

      {/* Grid Content */}
      <div className="order-detail-grid">
        {/* Left Column: Items */}
        <div className="left-column">
          <div className="table-card">
            <h3 className="card-title">Items</h3>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Item</th>
                  <th className="text-right">Qty</th>
                  <th className="text-right">Price</th>
                  <th>Notes</th>
                  {order.status === 'PENDING' && <th></th>}
                </tr>
              </thead>
              <tbody>
                {(!order.items || order.items.length === 0) ? (
                  <tr>
                    <td colSpan={5} className="empty-state">
                      <h3>No items</h3>
                    </td>
                  </tr>
                ) : (
                  order.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        {item.item_name}
                        {item.addons?.map((addon) => (
                          <div key={addon.id} className="addon-text">
                            + {addon.addon_name} (₱{parseFloat(addon.price).toFixed(2)})
                          </div>
                        ))}
                      </td>
                      <td className="text-right">{item.quantity}</td>
                      <td className="text-right">₱{parseFloat(item.line_total).toFixed(2)}</td>
                      <td>{item.notes || '—'}</td>
                      {order.status === 'PENDING' && (
                        <td className="text-right">
                          <button
                            onClick={() => handleRemoveItem(item.id)}
                            className="btn btn-ghost btn-sm btn-danger-text"
                          >
                            Remove
                          </button>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {order.status === 'PENDING' && (
            <div className="table-card mt-4 p-4">
              <h3>Add Item</h3>
              <form onSubmit={handleAddItem} className="form-stack">
                <div className="field">
                  <label>Select Item</label>
                  <select
                    value={newItemId}
                    onChange={(e) => setNewItemId(e.target.value)}
                    className="input"
                    required
                  >
                    <option value="">Choose item...</option>
                    {menuItems.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} (₱{m.price})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label>Quantity</label>
                  <input
                    type="number"
                    min="1"
                    value={newItemQty}
                    onChange={(e) => setNewItemQty(Number(e.target.value))}
                    className="input"
                    required
                  />
                </div>
                <div className="field">
                  <label>Notes</label>
                  <input
                    type="text"
                    value={newItemNotes}
                    onChange={(e) => setNewItemNotes(e.target.value)}
                    className="input"
                    placeholder="E.g., No onions"
                  />
                </div>
                <button type="submit" className="btn btn-primary btn-sm">
                  Add item
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Right Column: Totals & Payments */}
        <div className="right-column">
          <div className="table-card p-4">
            <h3 className="mb-3">Totals</h3>
            <div className="summary-row">
              <span className="text-muted">Subtotal</span>
              <span>₱{parseFloat(order.subtotal).toFixed(2)}</span>
            </div>

            {Number(order.discount_amount) > 0 && (
              <div className="summary-row">
                <span className="text-muted">
                  Discount ({order.discount_type_display}
                  {order.discount_ref ? ` ${order.discount_ref}` : ''})
                </span>
                <span className="text-danger">
                  −₱{parseFloat(order.discount_amount).toFixed(2)}
                </span>
              </div>
            )}

            <div className="summary-row">
              <span className="text-muted">VAT (12%)</span>
              <span>₱{parseFloat(order.vat_amount).toFixed(2)}</span>
            </div>

            <div className="summary-row grand-total">
              <span>Total</span>
              <span>₱{parseFloat(order.total).toFixed(2)}</span>
            </div>

            <div className="summary-row mt-2">
              <span className="text-muted">Paid</span>
              <span>₱{parseFloat(order.paid).toFixed(2)}</span>
            </div>

            {Number(order.paid) > 0 && (
              <div className={`summary-row balance-row ${order.is_settled ? 'settled' : 'unsettled'}`}>
                <span>Balance</span>
                <span>₱{parseFloat(order.outstanding_balance).toFixed(2)}</span>
              </div>
            )}
          </div>

          {!isCompletedOrCancelled && (
            <>
              {/* Payment Form */}
              <div className="table-card mt-4 p-4">
                <h3 className="mb-3">Record Payment</h3>
                <form onSubmit={handleRecordPayment} className="form-stack">
                  <div className="field">
                    <label>Method</label>
                    <select
                      value={paymentMethod}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="input"
                    >
                      <option value="CASH">Cash</option>
                      <option value="CARD">Card</option>
                      <option value="GCASH">GCash</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Amount</label>
                    <input
                      type="number"
                      step="0.01"
                      value={paymentAmount}
                      onChange={(e) => setPaymentAmount(e.target.value)}
                      className="input"
                      placeholder="0.00"
                      required
                    />
                  </div>
                  <button type="submit" className="btn btn-primary btn-sm">
                    Record payment
                  </button>
                </form>
              </div>

              {/* Discount Form */}
              <div className="table-card mt-4 p-4">
                <h3 className="mb-3">Apply Discount (FR-087)</h3>
                <form onSubmit={handleApplyDiscount} className="form-stack">
                  <div className="field">
                    <label>Discount Type</label>
                    <select
                      value={discountType}
                      onChange={(e) => setDiscountType(e.target.value)}
                      className="input"
                    >
                      <option value="PERCENTAGE">Percentage (%)</option>
                      <option value="FLAT">Flat Amount (₱)</option>
                      <option value="SENIOR">Senior Citizen (20%)</option>
                      <option value="PWD">PWD (20%)</option>
                    </select>
                  </div>
                  <div className="field">
                    <label>Value / Percent</label>
                    <input
                      type="number"
                      step="0.01"
                      value={discountValue}
                      onChange={(e) => setDiscountValue(e.target.value)}
                      className="input"
                      placeholder="E.g. 10"
                      required
                    />
                  </div>
                  <div className="field">
                    <label>Reference / ID No.</label>
                    <input
                      type="text"
                      value={discountRef}
                      onChange={(e) => setDiscountRef(e.target.value)}
                      className="input"
                      placeholder="ID or note"
                    />
                  </div>
                  <button type="submit" className="btn btn-secondary btn-sm">
                    Apply discount
                  </button>
                </form>
              </div>
            </>
          )}

          {/* Payments Ledger */}
          {order.payments && order.payments.length > 0 && (
            <div className="table-card mt-4 p-4">
              <h3 className="mb-3">Payments</h3>
              <table className="data-table">
                <tbody>
                  {order.payments.map((payment) => (
                    <tr key={payment.id}>
                      <td>{payment.method_display}</td>
                      <td
                        className={`text-right ${
                          Number(payment.amount) < 0 ? 'text-danger' : ''
                        }`}
                      >
                        ₱{parseFloat(payment.amount).toFixed(2)}
                      </td>
                      <td>{payment.created_at}</td>
                      {Number(payment.amount) > 0 && isOwnerOrManager && (
                        <td>
                          <div className="inline-refund">
                            <input
                              type="text"
                              placeholder="Reason"
                              value={refundReasons[payment.id] || ''}
                              onChange={(e) =>
                                setRefundReasons({
                                  ...refundReasons,
                                  [payment.id]: e.target.value,
                                })
                              }
                              className="input input-compact"
                            />
                            <button
                              onClick={() => handleRefund(payment.id)}
                              className="btn btn-ghost btn-sm btn-danger-text"
                            >
                              Refund
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Status History Table */}
      <h3 className="section-heading mt-5">Status History</h3>
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>From</th>
              <th>To</th>
              <th>By</th>
              <th>Reason</th>
              <th>When</th>
            </tr>
          </thead>
          <tbody>
            {order.status_history?.map((entry) => (
              <tr key={entry.id}>
                <td>{entry.old_status_display}</td>
                <td>{entry.new_status_display}</td>
                <td>{entry.changed_by || '—'}</td>
                <td>{entry.reason || '—'}</td>
                <td>{entry.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OrderDetailPage;