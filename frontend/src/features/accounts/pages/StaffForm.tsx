import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createStaffMember, getRestaurantSettings } from '../api/accounts';
import type { CreateStaffPayload } from '../types/accounts.types';

export const StaffForm: React.FC = () => {
  const navigate = useNavigate();

  const [restaurantName, setRestaurantName] = useState<string>('your restaurant');
  const [formData, setFormData] = useState<CreateStaffPayload>({
    first_name: '',
    last_name: '',
    email: '',
    role: 'CASHIER', // Match exact Django backend role choices (e.g., OWNER, MANAGER, CASHIER, STAFF)
  });

  const [creating, setCreating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchRestaurantName = async () => {
      try {
        const settings = await getRestaurantSettings();
        if (settings?.name) {
          setRestaurantName(settings.name);
        }
      } catch (err) {
        console.error('Could not fetch restaurant settings name:', err);
      }
    };

    fetchRestaurantName();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrorMessage(null);
    setFieldErrors((prev) => ({ ...prev, [name]: '' }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      await createStaffMember(formData);
      navigate('/accounts/staff', {
        state: { message: `Invitation email sent to ${formData.email}.` },
      });
    } catch (err: any) {
      const responseData = err.response?.data || {};
      
      // Handle Django DRF field errors and general details properly
      if (typeof responseData === 'object' && responseData !== null) {
        const newFieldErrors: Record<string, string> = {};
        let generalError = '';

        Object.keys(responseData).forEach((key) => {
          const val = responseData[key];
          if (key === 'detail') {
            generalError = typeof val === 'string' ? val : JSON.stringify(val);
          } else if (Array.isArray(val)) {
            newFieldErrors[key] = val[0];
          } else if (typeof val === 'string') {
            newFieldErrors[key] = val;
          }
        });

        setFieldErrors(newFieldErrors);
        setErrorMessage(generalError || 'Failed to create staff account. Please review the errors below.');
      } else {
        setErrorMessage('An unexpected error occurred.');
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
        <div className="alert alert-danger" role="alert" style={{ marginBottom: 'var(--space-4)' }}>
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
            className="input"
            value={formData.first_name}
            onChange={handleChange}
            required
            disabled={creating}
            placeholder="John"
          />
          {fieldErrors.first_name && <span className="error-message" style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>{fieldErrors.first_name}</span>}
        </div>

        <div className="field">
          <label htmlFor="last_name">Last Name</label>
          <input
            type="text"
            id="last_name"
            name="last_name"
            className="input"
            value={formData.last_name}
            onChange={handleChange}
            required
            disabled={creating}
            placeholder="Doe"
          />
          {fieldErrors.last_name && <span className="error-message" style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>{fieldErrors.last_name}</span>}
        </div>

        <div className="field">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            name="email"
            className="input"
            value={formData.email}
            onChange={handleChange}
            required
            disabled={creating}
            placeholder="staff@restaurant.com"
          />
          <small style={{ display: 'block', color: 'var(--gray-500)', marginTop: '2px' }}>An initial temporary password will be generated for the user.</small>
          {fieldErrors.email && <span className="error-message" style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>{fieldErrors.email}</span>}
        </div>

        <div className="field">
          <label htmlFor="role">Role</label>
          <select
            id="role"
            name="role"
            className="input"
            value={formData.role}
            onChange={handleChange}
            disabled={creating}
          >
            <option value="CASHIER">Cashier</option>
            <option value="MANAGER">Manager</option>
            <option value="KITCHEN">Kitchen</option>
            <option value="OWNER">Owner</option>
          </select>
          {fieldErrors.role && <span className="error-message" style={{ color: 'var(--color-error)', fontSize: 'var(--font-size-xs)' }}>{fieldErrors.role}</span>}
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