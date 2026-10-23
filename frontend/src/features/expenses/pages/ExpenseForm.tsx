import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { expensesApi } from '../api/expenses';
import type { ExpenseCategory } from '../types/expenses.types';

export const ExpenseForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const action = isEdit ? 'Edit' : 'Add';

  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [category, setCategory] = useState<string>('');
  const [amount, setAmount] = useState<number | ''>('');
  const [description, setDescription] = useState<string>('');
  const [expenseDate, setExpenseDate] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [existingReceiptUrl, setExistingReceiptUrl] = useState<string | null>(null);
  const [isLocked, setIsLocked] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const initData = async () => {
      try {
        const cats = await expensesApi.getCategories();
        setCategories(Array.isArray(cats) ? cats : []);

        if (id) {
          const detail = await expensesApi.getExpenseDetail(Number(id));
          setCategory(String(detail.category));
          setAmount(detail.amount);
          setDescription(detail.description || '');
          setExpenseDate(detail.expense_date);
          setExistingReceiptUrl(detail.receipt_image || null);
          setIsLocked(Boolean(detail.is_locked));
        }
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load form data.']);
      } finally {
        setLoading(false);
      }
    };
    initData();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const formData = new FormData();
    formData.append('category', category);
    formData.append('amount', String(amount));
    formData.append('description', description);
    formData.append('expense_date', expenseDate);
    if (receiptFile) {
      formData.append('receipt_image', receiptFile);
    }

    try {
      if (isEdit && id) {
        await expensesApi.updateExpense(Number(id), formData);
      } else {
        await expensesApi.createExpense(formData);
      }
      navigate('/expenses');
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setNonFieldErrors(data.non_field_errors);
        }
        if (data.detail) {
          setNonFieldErrors([data.detail]);
        }
        setFieldErrors(data);
      } else {
        setNonFieldErrors(['An unexpected error occurred. Please try again.']);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading expense form...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{action} Expense</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Expenses on a closed business day are locked (FR-113).
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        {isLocked && (
          <div className="alert alert-warning" style={{ marginBottom: 'var(--space-4)' }}>
            This expense occurred on a closed business day and cannot be modified.
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          {nonFieldErrors.length > 0 && (
            <ul className="errorlist">
              {nonFieldErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}

          {/* Category */}
          <div className="field">
            <label htmlFor="id_category">Category</label>
            <select
              id="id_category"
              className="input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={isLocked}
              required
            >
              <option value="">---------</option>
              {Array.isArray(categories) &&
                categories.map((cat, index) => (
                  <option key={cat.value || index} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
            </select>
            {fieldErrors.category && (
              <ul className="errorlist">
                <li>{fieldErrors.category}</li>
              </ul>
            )}
          </div>

          {/* Amount */}
          <div className="field">
            <label htmlFor="id_amount">Amount (₱)</label>
            <input
              type="number"
              id="id_amount"
              className="input"
              value={amount}
              onChange={(e) => setAmount(e.target.value === '' ? '' : Number(e.target.value))}
              min={0}
              step="0.01"
              disabled={isLocked}
              required
            />
            {fieldErrors.amount && (
              <ul className="errorlist">
                <li>{fieldErrors.amount}</li>
              </ul>
            )}
          </div>

          {/* Expense Date */}
          <div className="field">
            <label htmlFor="id_expense_date">Date</label>
            <input
              type="date"
              id="id_expense_date"
              className="input"
              value={expenseDate}
              onChange={(e) => setExpenseDate(e.target.value)}
              disabled={isLocked}
              required
            />
            {fieldErrors.expense_date && (
              <ul className="errorlist">
                <li>{fieldErrors.expense_date}</li>
              </ul>
            )}
          </div>

          {/* Description */}
          <div className="field">
            <label htmlFor="id_description">Description</label>
            <textarea
              id="id_description"
              className="input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              disabled={isLocked}
            />
            {fieldErrors.description && (
              <ul className="errorlist">
                <li>{fieldErrors.description}</li>
              </ul>
            )}
          </div>

          {/* Receipt Image Upload */}
          <div className="field">
            <label htmlFor="id_receipt_image">Receipt Image</label>
            <input
              type="file"
              id="id_receipt_image"
              className="input"
              accept="image/*"
              onChange={(e) => setReceiptFile(e.target.files?.[0] || null)}
              disabled={isLocked}
            />
            {fieldErrors.receipt_image && (
              <ul className="errorlist">
                <li>{fieldErrors.receipt_image}</li>
              </ul>
            )}
          </div>

          {/* Existing Image Preview */}
          {existingReceiptUrl && !receiptFile && (
            <div style={{ marginTop: 'var(--space-2)' }}>
              <img
                src={existingReceiptUrl}
                alt="Receipt"
                style={{
                  maxWidth: '200px',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--gray-200)',
                }}
              />
            </div>
          )}

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting || isLocked}>
              {submitting ? 'Saving...' : `${action} Expense`}
            </button>
            <Link to="/expenses" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default ExpenseForm;