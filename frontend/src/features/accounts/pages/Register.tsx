import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authApi } from '../api/accounts';
import type { RegisterPayload } from '../api/accounts';

export const Register: React.FC = () => {
  const [formData, setFormData] = useState<RegisterPayload>({
    restaurant_name: '',
    username: '',
    email: '',
    password: '',
    password_confirm: '',
  });

  const [errors, setErrors] = useState<Record<string, string[]>>({});
  const [generalError, setGeneralError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    
    // Keep username in sync with email automatically
    if (name === 'email') {
      setFormData((prev) => ({ ...prev, email: value, username: value }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }

    // Clear field error on edit
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: [] }));
    }
  };

  const handleSubmit = async (e: React.SubmitEvent) => {
    e.preventDefault();
    setErrors({});
    setGeneralError('');

    if (formData.password !== formData.password_confirm) {
      setErrors({ password_confirm: ['Passwords do not match.'] });
      return;
    }

    setIsSubmitting(true);
    try {
      // Ensure payload contains email as username
      const payload: RegisterPayload = {
        ...formData,
        username: formData.email,
      };

      await authApi.register(payload);
      navigate('/login', {
        state: { message: 'Restaurant registered successfully! Please log in.' },
      });
    } catch (err: any) {
      if (err.response?.data) {
        if (typeof err.response.data === 'object' && !Array.isArray(err.response.data)) {
          setErrors(err.response.data);
          if (err.response.data.detail) {
            setGeneralError(err.response.data.detail);
          } else if (err.response.data.non_field_errors) {
            setGeneralError(err.response.data.non_field_errors[0]);
          }
        } else {
          setGeneralError('Registration failed. Please verify your details.');
        }
      } else {
        setGeneralError('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8">
      <section className="auth-card wide max-w-lg w-full bg-white rounded-lg shadow-md p-8 border border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Set up your restaurant</h1>
        <p className="text-sm text-gray-600 mb-6">
          Create your Owner account. You can add staff after you sign in.
        </p>

        {generalError && (
          <div className="alert alert-error mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded-md text-sm">
            <p>{generalError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div className="field">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Restaurant Name
            </label>
            <input
              type="text"
              name="restaurant_name"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.restaurant_name}
              onChange={handleChange}
            />
            {errors.restaurant_name && (
              <p className="text-xs text-red-600 mt-1">{errors.restaurant_name[0]}</p>
            )}
          </div>

          <div className="field">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              name="email"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.email}
              onChange={handleChange}
            />
            {errors.email && (
              <p className="text-xs text-red-600 mt-1">{errors.email[0]}</p>
            )}
          </div>

          <div className="field">
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.password}
              onChange={handleChange}
            />
            <small className="text-xs text-gray-500 block mt-1">Must be at least 8 characters.</small>
            {errors.password && (
              <p className="text-xs text-red-600 mt-1">{errors.password[0]}</p>
            )}
          </div>

          <div className="field">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <input
              type="password"
              name="password_confirm"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formData.password_confirm}
              onChange={handleChange}
            />
            {errors.password_confirm && (
              <p className="text-xs text-red-600 mt-1">{errors.password_confirm[0]}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="btn btn-primary w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Creating restaurant...' : 'Create restaurant'}
          </button>
        </form>

        <p className="mt-6 text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 hover:underline">
            Log in
          </Link>
          .
        </p>
      </section>
    </div>
  );
};