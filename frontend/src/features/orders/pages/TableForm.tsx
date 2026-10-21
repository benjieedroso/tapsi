import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { ordersApi } from '../api/orders';
import type { TableStatus } from '../types/orders.types';

export const TableForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const action = isEdit ? 'Edit' : 'Add';

  const [name, setName] = useState<string>('');
  const [seatingCapacity, setSeatingCapacity] = useState<number | ''>(4);
  const [status, setStatus] = useState<TableStatus>('AVAILABLE');

  const [loading, setLoading] = useState<boolean>(isEdit);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!id) return;
    const fetchTable = async () => {
      try {
        const table = await ordersApi.getTableDetail(Number(id));
        setName(table.name);
        setSeatingCapacity(table.seating_capacity);
        if (table.status) {
          setStatus(table.status as TableStatus);
        }
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load table details.']);
      } finally {
        setLoading(false);
      }
    };
    fetchTable();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload = {
      name,
      seating_capacity: Number(seatingCapacity),
      status,
    };

    try {
      if (isEdit && id) {
        await ordersApi.updateTable(Number(id), payload);
      } else {
        await ordersApi.createTable(payload);
      }
      navigate('/tables');
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setNonFieldErrors(data.non_field_errors);
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
    return <div style={{ padding: 'var(--space-4)' }}>Loading table data...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{action} Table</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Configure table name, capacity, and operational status (FR-090..091).
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '480px' }}>
        <form onSubmit={handleSubmit} noValidate>
          {nonFieldErrors.length > 0 && (
            <ul className="errorlist">
              {nonFieldErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}

          <div className="field">
            <label htmlFor="id_name">Table name</label>
            <input
              type="text"
              id="id_name"
              name="name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Table 1 or Patio A"
              required
            />
            {fieldErrors.name && (
              <ul className="errorlist">
                <li>{fieldErrors.name}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_seating_capacity">Seating capacity</label>
            <input
              type="number"
              id="id_seating_capacity"
              name="seating_capacity"
              className="input"
              value={seatingCapacity}
              onChange={(e) => setSeatingCapacity(e.target.value === '' ? '' : Number(e.target.value))}
              min={1}
              required
            />
            {fieldErrors.seating_capacity && (
              <ul className="errorlist">
                <li>{fieldErrors.seating_capacity}</li>
              </ul>
            )}
          </div>

          <div className="field" style={{ marginTop: 'var(--space-3)' }}>
            <label htmlFor="id_status">Table status</label>
            <select
              id="id_status"
              name="status"
              className="input"
              value={status}
              onChange={(e) => setStatus(e.target.value as TableStatus)}
            >
              <option value="AVAILABLE">Available</option>
              <option value="OCCUPIED">Occupied</option>
              <option value="RESERVED">Reserved</option>
              <option value="CLEANING">Cleaning</option>
            </select>
            {fieldErrors.status && (
              <ul className="errorlist">
                <li>{fieldErrors.status}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : `${action} Table`}
            </button>
            <Link to="/tables" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default TableForm;