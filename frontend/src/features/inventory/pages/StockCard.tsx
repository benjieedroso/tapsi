import React, { useEffect, useState, useCallback } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { inventoryApi } from '../api/inventory';
import type { StockCardResponse, StockCardTransaction } from '../types/inventory.types';

export const StockCard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<StockCardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Form filter state
  const [txnType, setTxnType] = useState<string>(searchParams.get('type') || '');
  const [dateFrom, setDateFrom] = useState<string>(searchParams.get('from') || '');
  const [dateTo, setDateTo] = useState<string>(searchParams.get('to') || '');

  const fetchStockCard = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const params: { type?: string; from?: string; to?: string } = {};
      const typeParam = searchParams.get('type');
      const fromParam = searchParams.get('from');
      const toParam = searchParams.get('to');

      if (typeParam) params.type = typeParam;
      if (fromParam) params.from = fromParam;
      if (toParam) params.to = toParam;

      const response = await inventoryApi.getStockCard(Number(id), params);
      setData(response);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load stock card data.');
    } finally {
      setLoading(false);
    }
  }, [id, searchParams]);

  useEffect(() => {
    fetchStockCard();
  }, [fetchStockCard]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (txnType) params.type = txnType;
    if (dateFrom) params.from = dateFrom;
    if (dateTo) params.to = dateTo;
    setSearchParams(params);
  };

  const handleClear = () => {
    setTxnType('');
    setDateFrom('');
    setDateTo('');
    setSearchParams({});
  };

  if (loading && !data) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading stock card...</div>;
  }

  if (error) {
    return <div className="alert alert-danger" style={{ margin: 'var(--space-4)' }}>{error}</div>;
  }

  const ingredient = data?.ingredient;
  const transactions = data?.transactions || [];
  const types = data?.types || [];

  // Safe numeric baseline casting for ingredient stats
  const currentStock = Number(ingredient?.current_stock ?? 0);
  const minStock = Number(ingredient?.minimum_stock ?? 0);
  const avgCost = Number(ingredient?.average_unit_cost ?? 0);

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Stock Card — {ingredient?.name}</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Balance: <strong>{currentStock.toFixed(2)} {ingredient?.unit_of_measure}</strong>
            {' · '}Min: {minStock.toFixed(2)}
            {' · '}Avg cost: ₱{avgCost.toFixed(2)}
          </p>
        </div>
        <Link className="btn btn-primary" to="/inventory/transactions/create">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Stock movement
        </Link>
      </div>

      <form
        onSubmit={handleFilterSubmit}
        style={{
          marginBottom: 'var(--space-4)',
          display: 'flex',
          gap: 'var(--space-3)',
          flexWrap: 'wrap',
          alignItems: 'flex-end',
        }}
      >
        <div className="field" style={{ margin: 0 }}>
          <label htmlFor="id_type" style={{ fontSize: 'var(--font-size-sm)' }}>
            Type
          </label>
          <select
            name="type"
            id="id_type"
            className="input"
            style={{ width: 'auto' }}
            value={txnType}
            onChange={(e) => setTxnType(e.target.value)}
          >
            <option value="">All types</option>
            {types.map(([val, lbl]) => (
              <option key={val} value={val}>
                {lbl}
              </option>
            ))}
          </select>
        </div>

        <div className="field" style={{ margin: 0 }}>
          <label htmlFor="id_from" style={{ fontSize: 'var(--font-size-sm)' }}>
            From
          </label>
          <input
            type="date"
            name="from"
            id="id_from"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="input"
            style={{ width: 'auto' }}
          />
        </div>

        <div className="field" style={{ margin: 0 }}>
          <label htmlFor="id_to" style={{ fontSize: 'var(--font-size-sm)' }}>
            To
          </label>
          <input
            type="date"
            name="to"
            id="id_to"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="input"
            style={{ width: 'auto' }}
          />
        </div>

        <button type="submit" className="btn btn-secondary btn-sm">
          Filter
        </button>
        <button type="button" onClick={handleClear} className="btn btn-ghost btn-sm">
          Clear
        </button>
      </form>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th style={{ textAlign: 'right' }}>Qty</th>
              <th style={{ textAlign: 'right' }}>Unit Cost</th>
              <th style={{ textAlign: 'right' }}>Balance</th>
              <th>Reference</th>
              <th>Reason</th>
              <th>User</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-state">
                  <h3>No transactions yet</h3>
                  <p>Record a stock movement to start this ledger.</p>
                </td>
              </tr>
            ) : (
              transactions.map((txn: StockCardTransaction | any) => {
                const qty = Number(txn.quantity ?? 0);
                const unitCost = txn.unit_cost !== null && txn.unit_cost !== undefined ? Number(txn.unit_cost) : null;
                const resultingBal = Number(txn.resulting_balance ?? txn.running_balance ?? 0);
                const isNegative = qty < 0;

                return (
                  <tr key={txn.id}>
                    <td>{txn.created_at ? new Date(txn.created_at).toLocaleString() : '—'}</td>
                    <td>{txn.transaction_type_display || txn.transaction_type || '—'}</td>
                    <td
                      style={{
                        textAlign: 'right',
                        color: isNegative ? 'var(--color-error)' : 'var(--tapsi-700)',
                      }}
                    >
                      {qty.toFixed(2)}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      {unitCost !== null && !isNaN(unitCost) ? `₱${unitCost.toFixed(2)}` : '—'}
                    </td>
                    <td style={{ textAlign: 'right' }}>{resultingBal.toFixed(2)}</td>
                    <td>{txn.reference || '—'}</td>
                    <td>{txn.reason || '—'}</td>
                    <td>{txn.user_display || (typeof txn.user === 'object' ? txn.user?.username : txn.user) || '—'}</td>
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

export default StockCard;