import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { requestPasswordReset } from '../api/accounts';
import type { ApiErrorResponse } from '../types/accounts.types';

export const PasswordReset: React.FC = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | undefined>(undefined);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setError(null);
    setFieldError(undefined);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      setFieldError('Email address is required.');
      return;
    }

    setLoading(true);

    try {
      await requestPasswordReset({ email: email.trim() });
      
      // Navigate to the success confirmation page
      navigate('/password-reset/done');
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};

      if (apiErr.detail) {
        setError(apiErr.detail);
      } else if (Array.isArray(apiErr.email)) {
        setFieldError(apiErr.email[0]);
      } else {
        // Standard security practice: navigate to done screen anyway or show error depending on backend logic
        navigate('/password-reset/done');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Reset password</h1>
      <p>Enter your email and we'll send a reset link if an active account exists.</p>

      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="email">Email address</label>
          <input
            type="email"
            id="email"
            name="email"
            value={email}
            onChange={handleChange}
            required
            disabled={loading}
            placeholder="name@company.com"
          />
          {fieldError && <span className="error-message">{fieldError}</span>}
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Sending...' : 'Send reset link'}
        </button>
      </form>
    </section>
  );
};

export default PasswordReset;