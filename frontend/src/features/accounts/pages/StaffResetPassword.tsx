import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { getStaffMember, resetStaffPassword } from '../api/accounts';
import type { StaffMember, ResetStaffPasswordPayload } from '../types/accounts.types';

export const StaffResetPassword: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [targetUser, setTargetUser] = useState<StaffMember | null>(null);
  const [formData, setFormData] = useState<ResetStaffPasswordPayload>({
    new_password: '',
    confirm_password: '',
  });

  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    new_password?: string;
    confirm_password?: string;
  }>({});

  useEffect(() => {
    if (!id) return;

    const fetchTargetStaff = async () => {
      try {
        setLoading(true);
        const data = await getStaffMember(id);
        setTargetUser(data);
      } catch (err: any) {
        setErrorMessage(
          err.response?.data?.detail || 'Failed to load staff details.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTargetStaff();
  }, [id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name as keyof typeof fieldErrors]) {
      setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!id) return;

    // Client-side validation
    const errors: { new_password?: string; confirm_password?: string } = {};
    if (!formData.new_password) {
      errors.new_password = 'This field is required.';
    }
    if (!formData.confirm_password) {
      errors.confirm_password = 'This field is required.';
    } else if (formData.new_password !== formData.confirm_password) {
      errors.confirm_password = 'Passwords do not match.';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    try {
      setSubmitting(true);
      setErrorMessage(null);
      setFieldErrors({});

      await resetStaffPassword(id, formData);

      navigate('/accounts/staff', {
        state: {
          message: `Password reset successfully for ${
            targetUser?.display_name || 'staff member'
          }.`,
        },
      });
    } catch (err: any) {
      const apiErr = err.response?.data || {};

      if (apiErr.detail && typeof apiErr.detail === 'string') {
        setErrorMessage(apiErr.detail);
      } else if (apiErr.non_field_errors) {
        setErrorMessage(
          Array.isArray(apiErr.non_field_errors)
            ? apiErr.non_field_errors[0]
            : apiErr.non_field_errors
        );
      } else {
        setFieldErrors({
          new_password: Array.isArray(apiErr.new_password)
            ? apiErr.new_password[0]
            : undefined,
          confirm_password: Array.isArray(apiErr.confirm_password)
            ? apiErr.confirm_password[0]
            : undefined,
        });
        setErrorMessage('Please correct the errors below.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="loading-state">Loading staff account...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Reset Staff Password</h1>
          <p
            style={{
              color: 'var(--gray-500)',
              fontSize: 'var(--font-size-sm)',
              marginTop: 'var(--space-1)',
            }}
          >
            Set a new password for {targetUser?.display_name || 'staff member'}.
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '500px' }}>
        {errorMessage && (
          <div
            className="alert alert-danger"
            role="alert"
            style={{ marginBottom: 'var(--space-4)' }}
          >
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="id_new_password">New Password</label>
            <input
              type="password"
              id="id_new_password"
              name="new_password"
              value={formData.new_password}
              onChange={handleChange}
              className={fieldErrors.new_password ? 'input-error' : ''}
              disabled={submitting}
            />
            {fieldErrors.new_password && (
              <span className="field-error">{fieldErrors.new_password}</span>
            )}
          </div>

          <div className="field" style={{ marginTop: 'var(--space-4)' }}>
            <label htmlFor="id_confirm_password">Confirm New Password</label>
            <input
              type="password"
              id="id_confirm_password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              className={fieldErrors.confirm_password ? 'input-error' : ''}
              disabled={submitting}
            />
            {fieldErrors.confirm_password && (
              <span className="field-error">{fieldErrors.confirm_password}</span>
            )}
          </div>

          <div
            style={{
              display: 'flex',
              gap: 'var(--space-3)',
              marginTop: 'var(--space-6)',
            }}
          >
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Resetting...' : 'Reset Password'}
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

export default StaffResetPassword;