import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getStaffMember, updateStaffMember } from '../api/accounts';
import type { ApiErrorResponse, UpdateStaffPayload } from '../types/accounts.types';

export const StaffEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState('');
  const [formData, setFormData] = useState<UpdateStaffPayload>({
    first_name: '',
    last_name: '',
    email: '',
    role: 'staff',
    is_active: true,
  });

  const [initialLoading, setInitialLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof UpdateStaffPayload, string>>>({});

  useEffect(() => {
    if (!id) return;

    const fetchStaff = async () => {
      try {
        const data = await getStaffMember(id);
        setFormData({
          first_name: data.first_name || '',
          last_name: data.last_name || '',
          email: data.email || '',
          role: data.role || 'staff',
          is_active: data.is_active ?? true,
        });
        
        const full = `${data.first_name} ${data.last_name}`.trim();
        setDisplayName(full || data.email);
      } catch (err) {
        setErrorMessage('Failed to load staff member details.');
      } finally {
        setInitialLoading(false);
      }
    };

    fetchStaff();
  }, [id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    setErrorMessage(null);
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    setSaving(true);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      await updateStaffMember(id, formData);
      navigate('/accounts/staff', {
        state: { message: `Successfully updated ${displayName}'s profile.` },
      });
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};

      if (apiErr.detail) {
        setErrorMessage(apiErr.detail);
      } else {
        setFieldErrors({
          first_name: Array.isArray(apiErr.first_name) ? apiErr.first_name[0] : undefined,
          last_name: Array.isArray(apiErr.last_name) ? apiErr.last_name[0] : undefined,
          email: Array.isArray(apiErr.email) ? apiErr.email[0] : undefined,
          role: Array.isArray(apiErr.role) ? apiErr.role[0] : undefined,
        });
        setErrorMessage('Failed to save changes. Please check the form errors below.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="form-card" style={{ maxWidth: '500px' }}>
        <p>Loading staff details...</p>
      </div>
    );
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Edit Staff Member</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Update {displayName}'s profile.
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '500px' }}>
        {errorMessage && (
          <div className="alert alert-danger" role="alert">
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="first_name">First Name</label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              disabled={saving}
            />
            {fieldErrors.first_name && <span className="field-error">{fieldErrors.first_name}</span>}
          </div>

          <div className="field">
            <label htmlFor="last_name">Last Name</label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              disabled={saving}
            />
            {fieldErrors.last_name && <span className="field-error">{fieldErrors.last_name}</span>}
          </div>

          <div className="field">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              disabled={saving}
            />
            {fieldErrors.email && <span className="field-error">{fieldErrors.email}</span>}
          </div>

          <div className="field">
            <label htmlFor="role">Role</label>
            <select
              id="role"
              name="role"
              value={formData.role}
              onChange={handleChange}
              disabled={saving}
            >
              <option value="staff">Staff</option>
              <option value="manager">Manager</option>
              <option value="admin">Admin</option>
            </select>
            {fieldErrors.role && <span className="field-error">{fieldErrors.role}</span>}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <Link to="/accounts/staff" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default StaffEdit;