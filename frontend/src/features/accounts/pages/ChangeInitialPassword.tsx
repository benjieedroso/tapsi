import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { changeInitialPassword } from '../api/accounts';
import type { ApiErrorResponse } from '../types/accounts.types';

export const ChangeInitialPassword: React.FC = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    newPassword: '',
    confirmPassword: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    newPassword?: string;
    confirmPassword?: string;
  }>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.newPassword !== formData.confirmPassword) {
      setFieldErrors({ confirmPassword: "Passwords don't match." });
      return;
    }

    if (formData.newPassword.length < 8) {
      setFieldErrors({
        newPassword: 'Password must be at least 8 characters long.',
      });
      return;
    }

    setLoading(true);

    try {
      await changeInitialPassword({
        new_password: formData.newPassword,
        confirm_password: formData.confirmPassword,
      });

      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};

      if (apiErr.detail) {
        setError(apiErr.detail);
      } else {
        setFieldErrors({
          newPassword: apiErr.new_password?.[0],
          confirmPassword: apiErr.confirm_password?.[0],
        });
        if (!apiErr.new_password && !apiErr.confirm_password) {
          setError('An unexpected error occurred. Please try again.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Set your password</h1>
      <p>For security, choose a new password before continuing.</p>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="newPassword">New Password</label>
          <input
            type="password"
            id="newPassword"
            name="newPassword"
            value={formData.newPassword}
            onChange={handleChange}
            required
            disabled={loading}
            placeholder="Enter new password"
          />
          {fieldErrors.newPassword && (
            <span className="error-message">{fieldErrors.newPassword}</span>
          )}
        </div>

        <div className="field">
          <label htmlFor="confirmPassword">Confirm New Password</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            disabled={loading}
            placeholder="Confirm new password"
          />
          {fieldErrors.confirmPassword && (
            <span className="error-message">{fieldErrors.confirmPassword}</span>
          )}
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Saving...' : 'Save password'}
        </button>
      </form>
    </section>
  );
};

export default ChangeInitialPassword;