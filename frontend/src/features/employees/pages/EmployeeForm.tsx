import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { employeesApi } from '../api/employees';

export const EmployeeForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const action = isEdit ? 'Edit' : 'Add';

  const [fullName, setFullName] = useState<string>('');
  const [position, setPosition] = useState<string>('');
  const [salaryType, setSalaryType] = useState<'MONTHLY' | 'DAILY' | 'HOURLY'>('MONTHLY');
  const [rate, setRate] = useState<number | ''>('');
  const [isActive, setIsActive] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(isEdit);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!id) return;
    const fetchEmployee = async () => {
      try {
        const data = await employeesApi.getEmployeeDetail(Number(id));
        setFullName(data.full_name || '');
        setPosition(data.position || '');
        setSalaryType(data.salary_type || 'MONTHLY');
        setRate(data.rate ?? '');
        setIsActive(data.is_active ?? true);
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load employee details.']);
      } finally {
        setLoading(false);
      }
    };
    fetchEmployee();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload = {
      full_name: fullName,
      position,
      salary_type: salaryType,
      rate: Number(rate),
      is_active: isActive,
    };

    try {
      if (isEdit && id) {
        await employeesApi.updateEmployee(Number(id), payload);
      } else {
        await employeesApi.createEmployee(payload);
      }
      navigate('/employees');
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
    return <div style={{ padding: 'var(--space-4)' }}>Loading employee data...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{action} Employee</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Salary fields are visible to Owner/Manager only (FR-121).
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

          <div className="field">
            <label htmlFor="id_full_name">Full Name</label>
            <input
              type="text"
              id="id_full_name"
              className="input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
            {fieldErrors.full_name && (
              <ul className="errorlist">
                <li>{fieldErrors.full_name}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_position">Position</label>
            <input
              type="text"
              id="id_position"
              className="input"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              required
            />
            {fieldErrors.position && (
              <ul className="errorlist">
                <li>{fieldErrors.position}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_salary_type">Salary Type</label>
            <select
              id="id_salary_type"
              className="input"
              value={salaryType}
              onChange={(e) => setSalaryType(e.target.value as any)}
              required
            >
              <option value="MONTHLY">Monthly</option>
              <option value="DAILY">Daily</option>
              <option value="HOURLY">Hourly</option>
            </select>
            {fieldErrors.salary_type && (
              <ul className="errorlist">
                <li>{fieldErrors.salary_type}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_rate">Rate (₱)</label>
            <input
              type="number"
              id="id_rate"
              className="input"
              value={rate}
              onChange={(e) => setRate(e.target.value === '' ? '' : Number(e.target.value))}
              min={0}
              step="0.01"
              required
            />
            {fieldErrors.rate && (
              <ul className="errorlist">
                <li>{fieldErrors.rate}</li>
              </ul>
            )}
          </div>

          <div className="field" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <input
              type="checkbox"
              id="id_is_active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <label htmlFor="id_is_active" style={{ margin: 0, cursor: 'pointer' }}>Active Employee</label>
            {fieldErrors.is_active && (
              <ul className="errorlist">
                <li>{fieldErrors.is_active}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : `${action} Employee`}
            </button>
            <Link to="/employees" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default EmployeeForm;