import React, { useEffect, useState, useCallback } from 'react';
import { ordersApi } from '../api/orders';
import type { KitchenOrder } from '../types/orders.types';

export const KitchenQueue: React.FC = () => {
  const [orders, setOrders] = useState<KitchenOrder[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [advancingId, setAdvancingId] = useState<number | null>(null);

  // Fetch orders from API
  const fetchQueue = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    try {
      const data = await ordersApi.getKitchenQueue();
      setOrders(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load kitchen queue.');
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, []);

  // Initial load + Auto-polling every 10 seconds for real-time order updates
  useEffect(() => {
    fetchQueue();
    const interval = setInterval(() => {
      fetchQueue(true);
    }, 10000);

    return () => clearInterval(interval);
  }, [fetchQueue]);

  // Handle status progression (PENDING -> PREPARING -> READY)
  const handleAdvance = async (orderId: number) => {
    setAdvancingId(orderId);
    try {
      await ordersApi.advanceOrderStatus(orderId);
      await fetchQueue(true); // Soft refresh after status update
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to advance order status.');
    } finally {
      setAdvancingId(null);
    }
  };

  return (
    <div className="kitchen-queue-container">
      <div className="page-heading">
        <div>
          <h1>Kitchen Queue</h1>
          <p className="subtext">
            PENDING and PREPARING orders, oldest first (FR-088).
          </p>
        </div>
        <button 
          className="btn btn-secondary btn-sm" 
          onClick={() => fetchQueue()}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {!loading && orders.length === 0 && (
        <div className="kitchen-card empty-state">
          <h3>All caught up</h3>
          <p>No pending or preparing orders right now.</p>
        </div>
      )}

      <div className="kitchen-grid">
        {orders.map((order) => {
          const isPreparing = order.status === 'PREPARING';
          const isBusy = advancingId === order.id;

          return (
            <div
              key={order.id}
              className={`kitchen-card ${isPreparing ? 'status-preparing' : 'status-pending'}`}
            >
              <div className="card-header">
                <h3>
                  {order.order_number}{' '}
                  <span className="order-type">
                    {order.order_type_display}
                    {order.table_name ? ` · ${order.table_name}` : ''}
                  </span>
                </h3>
                <span className={`badge ${isPreparing ? 'badge-warning' : 'badge-neutral'}`}>
                  {order.status_display}
                </span>
              </div>

              <p className="elapsed-time">
                Elapsed: {order.elapsed_minutes} min (FR-089)
              </p>

              <div className="order-items-list">
                {order.items.map((item) => (
                  <div key={item.id} className="order-item-row">
                    <strong className="item-title">
                      {item.quantity}× {item.item_name}
                    </strong>

                    {item.addons && item.addons.length > 0 && (
                      <div className="item-addons">
                        {item.addons.map((addon) => (
                          <div key={addon.id} className="addon-note">
                            + {addon.addon_name}
                          </div>
                        ))}
                      </div>
                    )}

                    {item.notes && (
                      <div className="item-instruction">
                        Note: {item.notes}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="card-actions">
                <button
                  type="button"
                  className={`btn ${isPreparing ? 'btn-success' : 'btn-primary'} full-width`}
                  onClick={() => handleAdvance(order.id)}
                  disabled={isBusy}
                >
                  {isBusy
                    ? 'Updating...'
                    : order.status === 'PENDING'
                    ? 'Start preparing'
                    : 'Mark ready'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default KitchenQueue;