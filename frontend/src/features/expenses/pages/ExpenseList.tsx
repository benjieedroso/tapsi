import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { expensesApi } from '../api/expenses';
import type { ExpenseListItem, ExpenseListResponse } from '../types/expenses.types';

interface ExpenseListProps {
  userRole?: 'OWNER' | 'MANAGER' | 'CASHIER' | 'STAFF';
}

export const ExpenseList: React.FC<ExpenseListProps> = ({ userRole }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState<ExpenseListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [category, setCategory] = useState<string>(searchParams.get('category') || '');
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || '');
  const [dateFrom, setDateFrom] = useState<string>(searchParams.get('from') || '');
  const [dateTo, setDateTo] = useState<string>(searchParams.get('to') || '');

  const [processingId, setProcessingId] = useState<number | null>(null);

  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      const catParam = searchParams.get('category');
      const statusParam = searchParams.get('status');
      const fromParam = searchParams.get('from');
      const toParam = searchParams.get('to');

      if (catParam) params.category = catParam;
      if (statusParam) params.status = statusParam;
      if (fromParam) params.from = fromParam;
      if (toParam) params.to = toParam;

      const res = await expensesApi.getExpenseList(params);
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load expenses.');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchExpenses();
  }, [fetchExpenses]);

  const updateFilters = (newParams: Record<string, string>) => {
    const updated = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([key, val]) => {
      if (val) {
        updated.set(key, val);
      } else {
        updated.delete(key);
      }
    });
    setSearchParams(updated);
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateFilters({
      category,
      status: statusFilter,
      from: dateFrom,
      to: dateTo,
    });
  };

  const handleApprove = async (id: number) => {
    setProcessingId(id);
    try {
      await expensesApi.approveExpense(id);
      await fetchExpenses();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve expense.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this expense?')) return;
    setProcessingId(id);
    try {
      await expensesApi.deleteExpense(id);
      await fetchExpenses();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete expense.');
    } finally {
      setProcessingId(null);
    }
  };

  const isOwnerOrManager = userRole === 'OWNER' || userRole === 'MANAGER';
  const expenses = data?.expenses || [];
  const categories = data?.categories || [];
  const statuses = data?.statuses || [];

  if (loading && !data) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading expenses...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Expenses</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Operating expenses for accurate profit reporting.
          </p>
        </div>
        <Link className="btn btn-primary" to="/expenses/create">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New expense
        </Link>
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

      <form
        onSubmit={handleFilterSubmit}
        style={{
          marginBottom: 'var(--space-4)',
          display: 'flex',
          gap: 'var(--space-3)',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <select
          name="category"
          className="input"
          style={{ width: 'auto' }}
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            updateFilters({ category: e.target.value, status: statusFilter, from: dateFrom, to: dateTo });
          }}
        >
          <option value="">All categories</option>
          {categories.map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </select>

        <select
          name="status"
          className="input"
          style={{ width: 'auto' }}
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            updateFilters({ category, status: e.target.value, from: dateFrom, to: dateTo });
          }}
        >
          <option value="">All statuses</option>
          {statuses.map(([val, label]) => (
            <option key={val} value={val}>
              {label}
            </option>
          ))}
        </select>

        <input
          type="date"
          name="from"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="input"
          style={{ width: 'auto' }}
        />

        <input
          type="date"
          name="to"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="input"
          style={{ width: 'auto' }}
        />

        <button type="submit" className="btn btn-secondary btn-sm">
          Filter
        </button>
      </form>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Payee</th>
              <th style={{ textAlign: 'right' }}>Amount</th>
              <th>Status</th>
              <th>By</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {expenses.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-state">
                  <h3>No expenses yet</h3>
                  <p>Record operating costs to see true profit.</p>
                  <Link to="/expenses/create" className="btn btn-primary" style={{ marginTop: 'var(--space-3)' }}>
                    New expense
                  </Link>
                </td>
              </tr>
            ) : (
              expenses.map((expense: ExpenseListItem) => (
                <tr key={expense.id}>
                  <td>{new Date(expense.expense_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
                  <td>{expense.category_display}</td>
                  <td>{expense.payee || '—'}</td>
                  <td style={{ textAlign: 'right' }}>₱{Number(expense.amount ?? 0).toFixed(2)}</td>
                  <td>
                    {expense.status === 'APPROVED' ? (
                      <span className="badge badge-success">{expense.status_display}</span>
                    ) : (
                      <span className="badge badge-warning">{expense.status_display}</span>
                    )}
                  </td>
                  <td>{expense.created_by_display || '—'}</td>
                  <td style={{ textAlign: 'right' }}>
                    {expense.status === 'PENDING' && isOwnerOrManager && (
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleApprove(expense.id)}
                        disabled={processingId === expense.id}
                      >
                        Approve
                      </button>
                    )}

                    {isOwnerOrManager && (
                      <>
                        <Link to={`/expenses/${expense.id}/edit`} className="btn btn-ghost btn-sm">
                          Edit
                        </Link>
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          style={{ color: 'var(--color-error)' }}
                          onClick={() => handleDelete(expense.id)}
                          disabled={processingId === expense.id}
                        >
                          Delete
                        </button>
                      </>
                    )}
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

export default ExpenseList;