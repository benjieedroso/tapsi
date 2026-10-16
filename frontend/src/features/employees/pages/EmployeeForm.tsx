import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { employeesApi } from '../api/employees';
import type { EmployeeFormData } from '../types/employees.types';

export const EmployeeForm: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();

  const [formData, setFormData] = useState<EmployeeFormData>({
    full_name: '',
    nickname: '',
    phone: '',
    address: '',
    emergency_contact: '',
    position: '',
    employment_status: 'ACTIVE',
    date_hired: new Date().toISOString().split('T')[0],
    daily_rate: '',
    monthly_salary: '',
  });

  const [loading, setLoading] = useState<boolean>(isEdit);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEdit && id) {
      employeesApi.getEmployeeDetail(Number(id))
        .then((res) => {
          setFormData({
            full_name: res.full_name || '',
            nickname: res.nickname || '',
            phone: res.phone || '',
            address: res.address || '',
            emergency_contact: res.emergency_contact || '',
            position: res.position || '',
            employment_status: (res.employment_status || 'ACTIVE').toUpperCase(),
            date_hired: res.date_hired || '',
            daily_rate: res.daily_rate !== null && res.daily_rate !== undefined ? String(res.daily_rate) : '',
            monthly_salary: res.monthly_salary !== null && res.monthly_salary !== undefined ? String(res.monthly_salary) : '',
          });
        })
        .catch(() => setError('Failed to load employee details.'))
        .finally(() => setLoading(false));
    }
  }, [id, isEdit]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    let val: any = value;
    if (type === 'checkbox') {
      val = (e.target as HTMLInputElement).checked ? 'ACTIVE' : 'INACTIVE';
    }
    setFormData((prev) => ({ ...prev, [name]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.full_name.trim() || !formData.position.trim()) {
      alert('Full Name and Position are required.');
      return;
    }

    setSubmitting(true);
    setError(null);

    const payload = {
      ...formData,
      employment_status: (formData.employment_status || 'ACTIVE').toUpperCase(),
      daily_rate: formData.daily_rate === '' ? null : formData.daily_rate,
      monthly_salary: formData.monthly_salary === '' ? null : formData.monthly_salary,
    };

    try {
      if (isEdit && id) {
        await employeesApi.updateEmployee(Number(id), payload);
      } else {
        await employeesApi.createEmployee(payload);
      }
      navigate('/employees');
    } catch (err: any) {
      console.error("Employee creation failed:", err.response?.data);
      setError(JSON.stringify(err.response?.data) || 'Failed to save employee.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div style={{ padding: 'var(--space-6)' }}>Loading employee form...</div>;

  return (
    <div style={{ padding: 'var(--space-6)', maxWidth: '640px', margin: '0 auto' }}>
      <div className="page-heading" style={{ marginBottom: 'var(--space-4)' }}>
        <h1>{isEdit ? 'Edit Employee' : 'Add Employee'}</h1>
        <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
          Salary fields are visible to Owner/Manager only (FR-121).
        </p>
      </div>

      <div className="form-card" style={{ background: 'var(--bg-surface, #fff)', padding: 'var(--space-6)', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        {error && <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>{error}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Full Name</label>
            <input type="text" name="full_name" className="input" value={formData.full_name} onChange={handleChange} required placeholder="Juan Dela Cruz" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
            <div className="field">
              <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Nickname</label>
              <input type="text" name="nickname" className="input" value={formData.nickname} onChange={handleChange} placeholder="Juan" />
            </div>
            <div className="field">
              <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Phone Number</label>
              <input type="text" name="phone" className="input" value={formData.phone} onChange={handleChange} placeholder="09123456789" />
            </div>
          </div>

          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Position</label>
            <input type="text" name="position" className="input" value={formData.position} onChange={handleChange} required placeholder="Kitchen Staff / Cashier" />
          </div>

          <div className="field" style={{ marginBottom: 'var(--space-3)' }}>
            <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Address</label>
            <textarea name="address" className="input" rows={2} value={formData.address} onChange={handleChange} placeholder="Home address..." />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
            <div className="field">
              <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Emergency Contact</label>
              <input type="text" name="emergency_contact" className="input" value={formData.emergency_contact} onChange={handleChange} placeholder="Name & Number" />
            </div>
            <div className="field">
              <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Date Hired</label>
              <input type="date" name="date_hired" className="input" value={formData.date_hired} onChange={handleChange} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
            <div className="field">
              <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Daily Rate (₱)</label>
              <input type="number" step="any" name="daily_rate" className="input" value={formData.daily_rate ?? ''} onChange={handleChange} placeholder="0.00" />
            </div>
            <div className="field">
              <label style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>Monthly Salary (₱)</label>
              <input type="number" step="any" name="monthly_salary" className="input" value={formData.monthly_salary ?? ''} onChange={handleChange} placeholder="0.00" />
            </div>
          </div>

          {/* Fixed compact alignment for checkbox and label */}
          <div className="field" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '10px', margin: 'var(--space-4) 0' }}>
            <input
              type="checkbox"
              id="employment_status"
              name="employment_status"
              style={{ width: '18px', height: '18px', cursor: 'pointer', margin: 0 }}
              checked={formData.employment_status === 'ACTIVE'}
              onChange={(e) => setFormData((prev) => ({
                ...prev,
                employment_status: e.target.checked ? 'ACTIVE' : 'INACTIVE',
              }))}
            />
            <label htmlFor="employment_status" style={{ fontWeight: 500, cursor: 'pointer', margin: 0, whiteSpace: 'nowrap', }}>Active Employee</label>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : (isEdit ? 'Update Employee' : 'Add Employee')}
            </button>
            <Link to="/employees" className="btn btn-secondary">Cancel</Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EmployeeForm;