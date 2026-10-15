import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../../../api/client';

export const StaffSetPassword: React.FC = () => {
  const { uid, token } = useParams<{ uid: string; token: string }>();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await apiClient.post('/api/v1/auth/staff/set-password/', {
        uid,
        token,
        new_password: newPassword,
      });
      alert('Password set successfully! You can now log in.');
      navigate('/login');
    } catch (err: any) {
      const errorData = err.response?.data;
      let errorMessage = 'Failed to set password. The link may be invalid or expired.';

      if (errorData) {
        if (typeof errorData.detail === 'string') {
          errorMessage = errorData.detail;
        } else if (typeof errorData === 'object') {
          // Find the first array error message safely in TypeScript
          const firstKey = Object.keys(errorData)[0];
          if (firstKey) {
            const fieldErrors = errorData[firstKey];
            if (Array.isArray(fieldErrors) && typeof fieldErrors[0] === 'string') {
              errorMessage = `${firstKey}: ${fieldErrors[0]}`;
            } else if (typeof fieldErrors === 'string') {
              errorMessage = fieldErrors;
            }
          }
        }
      }

      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="form-card" style={{ maxWidth: '440px', margin: '80px auto', padding: 'var(--space-6)' }}>
      <h1>Set Your Password</h1>
      <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--space-5)' }}>
        Please choose a secure password to activate your staff account.
      </p>

      {error && (
        <div className="alert alert-danger" role="alert" style={{ marginBottom: 'var(--space-4)' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field" style={{ marginBottom: 'var(--space-4)' }}>
          <label htmlFor="new_password" style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>
            New Password
          </label>
          <input
            type="password"
            id="new_password"
            className="input"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            disabled={submitting}
            placeholder="At least 8 characters"
          />
        </div>

        <div className="field" style={{ marginBottom: 'var(--space-6)' }}>
          <label htmlFor="confirm_password" style={{ display: 'block', fontWeight: 500, marginBottom: 'var(--space-1)' }}>
            Confirm Password
          </label>
          <input
            type="password"
            id="confirm_password"
            className="input"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            disabled={submitting}
            placeholder="Re-enter password"
          />
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          style={{ width: '100%', textAlign: 'center' }}
          disabled={submitting}
        >
          {submitting ? 'Setting password...' : 'Set password'}
        </button>
      </form>
    </div>
  );
};

export default StaffSetPassword;