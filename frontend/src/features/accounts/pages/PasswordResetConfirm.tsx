import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { confirmPasswordReset } from '../api/accounts';
import type { ApiErrorResponse } from '../types/accounts.types';

export const PasswordResetConfirm: React.FC = () => {
  const { uid, token } = useParams<{ uid: string; token: string }>();
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

  // Check if link tokens are present in URL route params
  const isValidLink = Boolean(uid && token);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!uid || !token) {
      setError('Invalid URL parameters. Request a new password reset link.');
      return;
    }

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
      await confirmPasswordReset({
        uid,
        token,
        new_password: formData.newPassword,
        confirm_password: formData.confirmPassword,
      });

      // Navigate to login with success state
      navigate('/login', {
        state: { message: 'Password has been reset successfully. You can now log in.' },
      });
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};

      if (apiErr.detail) {
        setError(apiErr.detail);
      } else {
        setFieldErrors({
          newPassword: Array.isArray(apiErr.new_password) ? apiErr.new_password[0] : undefined,
          confirmPassword: Array.isArray(apiErr.confirm_password) ? apiErr.confirm_password[0] : undefined,
        });
        if (!apiErr.new_password && !apiErr.confirm_password) {
          setError('This reset link is invalid or has expired. Request a new one.');
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Choose a new password</h1>

      {!isValidLink ? (
        <div className="alert alert-error">
          <p>
            This reset link is invalid or has expired.{' '}
            <Link to="/password-reset">Request a new one</Link>.
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate>
          {error && (
            <div className="alert alert-danger" role="alert">
              {error}
            </div>
          )}

          <div className="field">
            <label htmlFor="newPassword">New password</label>
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
            <label htmlFor="confirmPassword">Confirm new password</label>
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
            {loading ? 'Resetting...' : 'Reset password'}
          </button>
        </form>
      )}
    </section>
  );
};

export default PasswordResetConfirm;