import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createStaffMember, getRestaurantSettings } from '../api/accounts';
import type { ApiErrorResponse, CreateStaffPayload } from '../types/accounts.types';

export const StaffForm: React.FC = () => {
  const navigate = useNavigate();

  const [restaurantName, setRestaurantName] = useState<string>('your restaurant');
  const [formData, setFormData] = useState<CreateStaffPayload>({
    first_name: '',
    last_name: '',
    email: '',
    role: 'staff',
  });

  const [creating, setCreating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof CreateStaffPayload, string>>>({});

  useEffect(() => {
    const fetchRestaurantName = async () => {
      try {
        const settings = await getRestaurantSettings();
        if (settings.name) {
          setRestaurantName(settings.name);
        }
      } catch (err) {
        // Fall back gracefully to default string if settings fetch fails
        console.error('Could not fetch restaurant settings name:', err);
      }
    };

    fetchRestaurantName();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrorMessage(null);
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      await createStaffMember(formData);
      navigate('/accounts/staff', {
        state: { message: `Staff member ${formData.email} added successfully.` },
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
        setErrorMessage('Failed to create staff account. Please review the errors below.');
      }
    } finally {
      setCreating(false);
    }
  };

  return (
    <section className="form-card">
      <h1>Add staff member</h1>
      <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-6)' }}>
        The new account belongs only to {restaurantName}.
      </p>

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
            required
            disabled={creating}
            placeholder="John"
          />
          {fieldErrors.first_name && <span className="error-message">{fieldErrors.first_name}</span>}
        </div>

        <div className="field">
          <label htmlFor="last_name">Last Name</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            required
            disabled={creating}
            placeholder="Doe"
          />
          {fieldErrors.last_name && <span className="error-message">{fieldErrors.last_name}</span>}
        </div>

        <div className="field">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            disabled={creating}
            placeholder="staff@restaurant.com"
          />
          <small>An initial temporary password will be generated for the user.</small>
          {fieldErrors.email && <span className="error-message">{fieldErrors.email}</span>}
        </div>

        <div className="field">
          <label htmlFor="role">Role</label>
          <select
            id="role"
            name="role"
            value={formData.role}
            onChange={handleChange}
            disabled={creating}
          >
            <option value="staff">Staff</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
          {fieldErrors.role && <span className="error-message">{fieldErrors.role}</span>}
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
          <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={creating}>
            {creating ? 'Creating...' : 'Create account'}
          </button>
          <Link to="/accounts/staff" className="btn btn-secondary" style={{ flex: 1, textAlign: 'center' }}>
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
};

export default StaffForm;