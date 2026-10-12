import React, { useEffect, useState, useCallback } from 'react';
import { notificationsApi } from '../api/notifications';
import type { NotificationItem } from '../types/notifications.types';

export const NotificationList: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const res = await notificationsApi.getNotifications();
      setNotifications(res.notifications || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load notifications.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleMarkRead = async (id: number) => {
    try {
      await notificationsApi.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, unread: false } : n))
      );
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to mark notification as read.');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to mark all notifications as read.');
    }
  };

  if (loading && notifications.length === 0) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading notifications...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Notifications</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            In-app alerts for orders, stock, discounts, and closing (FR-150..152).
          </p>
        </div>
        <button type="button" onClick={handleMarkAllRead} className="btn btn-secondary">
          Mark all read
        </button>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Type</th>
              <th>Message</th>
              <th>Received</th>
            </tr>
          </thead>
          <tbody>
            {notifications.length === 0 ? (
              <tr>
                <td colSpan={4} className="empty-state">
                  <h3>No notifications</h3>
                  <p>Alerts for low stock, new orders, and more will appear here.</p>
                </td>
              </tr>
            ) : (
              notifications.map((n: NotificationItem) => {
                const createdAtFormatted = n.created_at
                  ? new Date(n.created_at).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false,
                    })
                  : '';

                return (
                  <tr
                    key={n.id}
                    style={{ fontWeight: n.unread ? 600 : 'normal' }}
                  >
                    <td style={{ width: '40px' }}>
                      {n.unread && (
                        <span className="badge" style={{ background: 'var(--color-primary)', color: '#fff' }}>
                          NEW
                        </span>
                      )}
                    </td>
                    <td>
                      <span className="badge badge-secondary">{n.type_display}</span>
                    </td>
                    <td>
                      <strong>{n.title}</strong>
                      {n.body && (
                        <>
                          <br />
                          <span style={{ color: 'var(--gray-500)', fontWeight: 400 }}>{n.body}</span>
                        </>
                      )}
                      {n.unread && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          style={{ display: 'inline', marginLeft: 'var(--space-2)' }}
                          onClick={() => handleMarkRead(n.id)}
                        >
                          Mark read
                        </button>
                      )}
                    </td>
                    <td style={{ whiteSpace: 'nowrap' }}>{createdAtFormatted}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default NotificationList;