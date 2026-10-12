import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ordersApi } from '../api/orders';
import type { ReceiptData } from '../types/orders.types';

export const Receipt: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<ReceiptData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchReceipt = async () => {
      try {
        const response = await ordersApi.getReceipt(Number(id));
        setData(response);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load receipt.');
      } finally {
        setLoading(false);
      }
    };
    fetchReceipt();
  }, [id]);

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading receipt...</div>;
  }

  if (error || !data) {
    return <div className="alert alert-danger">{error || 'Receipt not found.'}</div>;
  }

  const { order, reprint, restaurant, items, payments } = data;

  return (
    <>
      <style>{`
        @media print {
          body { background: white !important; }
          .navbar, .page-heading, .container > .alert { display: none !important; }
          #receipt { border: none !important; border-radius: 0 !important; max-width: 80mm !important; margin: 0 !important; padding: 0 !important; }
        }
      `}</style>

      <div className="page-heading">
        <div>
          <h1>Receipt — {order.order_number}</h1>
          {reprint && (
            <p style={{ color: 'var(--color-error)', fontWeight: 600, marginTop: 'var(--space-1)' }}>
              REPRINT — issued {order.receipt_reprinted_count}×
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <button type="button" onClick={() => window.print()} className="btn btn-primary">
            Print
          </button>
          <Link to={`/orders/${order.id}`} className="btn btn-secondary">
            Back to order
          </Link>
        </div>
      </div>

      <div
        id="receipt"
        style={{
          maxWidth: '400px',
          margin: '0 auto',
          background: 'white',
          border: '1px solid var(--gray-200)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-5)',
          fontFamily: "'Courier New', monospace",
          fontSize: '13px',
          lineHeight: '1.5',
        }}
      >
        {reprint && (
          <div style={{ textAlign: 'center', fontWeight: 700, letterSpacing: '2px', marginBottom: 'var(--space-2)' }}>
            *** REPRINT ***
          </div>
        )}

        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '18px', marginBottom: '2px' }}>{restaurant.name}</h2>
          {restaurant.address && <div>{restaurant.address}</div>}
          {restaurant.contact_number && <div>Tel: {restaurant.contact_number}</div>}
          {restaurant.tin && <div>TIN: {restaurant.tin}</div>}
          <div>{restaurant.is_vat_registered ? 'VAT Registered' : 'Non-VAT'}</div>
          <div>Receipt No: {order.receipt_no}</div>
          <div>{order.created_at}</div>
          <div>Cashier: {order.created_by_name || '—'}</div>
        </div>

        <div
          style={{
            borderTop: '1px dashed #999',
            borderBottom: '1px dashed #999',
            margin: 'var(--space-3) 0',
            padding: 'var(--space-2) 0',
          }}
        >
          {items.map((item) => (
            <React.Fragment key={item.id}>
              <div>
                {item.item_name} × {item.quantity}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span></span>
                <span>₱{parseFloat(item.line_total).toFixed(2)}</span>
              </div>
              {item.addons?.map((addon) => (
                <div key={addon.id} style={{ marginLeft: '12px' }}>
                  + {addon.addon_name}{' '}
                  <span style={{ float: 'right' }}>₱{parseFloat(addon.price).toFixed(2)}</span>
                </div>
              ))}
              {item.notes && <div style={{ marginLeft: '12px' }}>({item.notes})</div>}
            </React.Fragment>
          ))}
        </div>

        <div style={{ marginBottom: 'var(--space-2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Subtotal</span>
            <span>₱{parseFloat(order.subtotal).toFixed(2)}</span>
          </div>

          {parseFloat(order.discount_amount) > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>
                Discount ({order.discount_type_display}
                {order.discount_ref ? ` ${order.discount_ref}` : ''})
              </span>
              <span>-₱{parseFloat(order.discount_amount).toFixed(2)}</span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>VATable Sales</span>
            <span>₱{parseFloat(order.vatable_sales).toFixed(2)}</span>
          </div>

          {order.vat_exempt_sales && parseFloat(order.vat_exempt_sales) > 0 && (
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>VAT-exempt Sales</span>
              <span>₱{parseFloat(order.vat_exempt_sales).toFixed(2)}</span>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>VAT (12%)</span>
            <span>₱{parseFloat(order.vat_amount).toFixed(2)}</span>
          </div>

          <div
            style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '16px',
                fontWeight: 700,
                borderTop: '1px dashed #999',
                marginTop: 'var(--space-2)',
                paddingTop: 'var(--space-2)',
            }}
            >
            <span>TOTAL</span>
            <span>₱{parseFloat(order.total).toFixed(2)}</span>
            </div>
        </div>

        <div style={{ borderTop: '1px dashed #999', paddingTop: 'var(--space-2)' }}>
          {payments.map((payment) => (
            <React.Fragment key={payment.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>
                  {payment.method_display}
                  {payment.reference_no ? ` (${payment.reference_no})` : ''}
                </span>
                <span>₱{parseFloat(payment.amount).toFixed(2)}</span>
              </div>
              {payment.change_given && parseFloat(payment.change_given) > 0 && (
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Change</span>
                  <span>₱{parseFloat(payment.change_given).toFixed(2)}</span>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>

        {restaurant.receipt_footer && (
          <div style={{ textAlign: 'center', marginTop: 'var(--space-3)' }}>
            {restaurant.receipt_footer}
          </div>
        )}
      </div>
    </>
  );
};

export default Receipt;