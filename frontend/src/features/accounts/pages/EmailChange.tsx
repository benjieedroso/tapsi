import React, { useState } from 'react';
import { requestEmailChange } from '../api/accounts';
import type { ApiErrorResponse } from '../types/accounts.types';

export const EmailChange: React.FC = () => {
  const [newEmail, setNewEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | undefined>(undefined);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewEmail(e.target.value);
    setErrorMessage(null);
    setFieldError(undefined);
    setSuccessMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newEmail.trim()) {
      setFieldError('Email address is required.');
      return;
    }

    setLoading(true);

    try {
      const res = await requestEmailChange({ new_email: newEmail.trim() });
      setSuccessMessage(
        res.detail ||
          'Confirmation email sent! Please check your new inbox to complete the verification.'
      );
      setNewEmail('');
    } catch (err: any) {
        const apiErr: ApiErrorResponse = err.response?.data || {};

        if (apiErr.detail) {
            setErrorMessage(apiErr.detail);
        } else if (Array.isArray(apiErr.new_email)) {
            setFieldError(apiErr.new_email[0]);
        } else {
            setErrorMessage('Failed to send confirmation. Please try again.');
        }
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-card">
      <h1>Change email address</h1>
      <p>
        We'll email a confirmation link to your new address. Your existing email
        remains active until it is verified.
      </p>

      {successMessage && (
        <div className="alert alert-success" role="alert">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="alert alert-danger" role="alert">
          {errorMessage}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="newEmail">New Email Address</label>
          <input
            type="email"
            id="newEmail"
            name="newEmail"
            value={newEmail}
            onChange={handleEmailChange}
            required
            disabled={loading}
            placeholder="name@company.com"
          />
          {fieldError && <span className="error-message">{fieldError}</span>}
        </div>

        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? 'Sending...' : 'Send confirmation'}
        </button>
      </form>
    </section>
  );
};

export default EmailChange;