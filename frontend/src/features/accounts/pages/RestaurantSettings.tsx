import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getRestaurantSettings, updateRestaurantSettings } from '../api/accounts';
import type { ApiErrorResponse, RestaurantSettingsData } from '../types/accounts.types';

export const RestaurantSettings: React.FC = () => {
  const [formData, setFormData] = useState<RestaurantSettingsData>({
    name: '',
    address: '',
    contact_number: '',
    tin: '',
    receipt_footer: '',
    is_vat_registered: false,
  });

  const [initialLoading, setInitialLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof RestaurantSettingsData, string>>>({});

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const data = await getRestaurantSettings();
        setFormData(data);
      } catch (err) {
        setErrorMessage('Failed to load restaurant settings.');
      } finally {
        setInitialLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    setSuccessMessage(null);
    setErrorMessage(null);
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    setFieldErrors({});

    try {
      const updated = await updateRestaurantSettings(formData);
      setFormData(updated);
      setSuccessMessage('Restaurant settings saved successfully.');
    } catch (err: any) {
      const apiErr: ApiErrorResponse = err.response?.data || {};

      if (apiErr.detail) {
        setErrorMessage(apiErr.detail);
      } else {
        setFieldErrors({
          name: Array.isArray(apiErr.name) ? apiErr.name[0] : undefined,
          address: Array.isArray(apiErr.address) ? apiErr.address[0] : undefined,
          contact_number: Array.isArray(apiErr.contact_number) ? apiErr.contact_number[0] : undefined,
          tin: Array.isArray(apiErr.tin) ? apiErr.tin[0] : undefined,
          receipt_footer: Array.isArray(apiErr.receipt_footer) ? apiErr.receipt_footer[0] : undefined,
          is_vat_registered: Array.isArray(apiErr.is_vat_registered) ? apiErr.is_vat_registered[0] : undefined,
        });
        setErrorMessage('Failed to save settings. Please check the fields below.');
      }
    } finally {
      setSaving(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="form-card" style={{ maxWidth: '640px' }}>
        <p>Loading restaurant settings...</p>
      </div>
    );
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Restaurant Settings</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Manage your restaurant details and configuration.
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '640px' }}>
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
          <div className="settings-section">
            <h3 className="settings-section-title">Business Information</h3>

            <div className="field">
              <label htmlFor="name">Restaurant Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                disabled={saving}
              />
              {fieldErrors.name && <span className="error-message">{fieldErrors.name}</span>}
            </div>

            <div className="field">
              <label htmlFor="address">Address</label>
              <input
                type="text"
                id="address"
                name="address"
                value={formData.address}
                onChange={handleChange}
                disabled={saving}
              />
              {fieldErrors.address && <span className="error-message">{fieldErrors.address}</span>}
            </div>

            <div className="field-row">
              <div className="field">
                <label htmlFor="contact_number">Contact Number</label>
                <input
                  type="text"
                  id="contact_number"
                  name="contact_number"
                  value={formData.contact_number}
                  onChange={handleChange}
                  disabled={saving}
                />
                {fieldErrors.contact_number && (
                  <span className="error-message">{fieldErrors.contact_number}</span>
                )}
              </div>
              <div className="field">
                <label htmlFor="tin">TIN</label>
                <input
                  type="text"
                  id="tin"
                  name="tin"
                  value={formData.tin}
                  onChange={handleChange}
                  disabled={saving}
                />
                {fieldErrors.tin && <span className="error-message">{fieldErrors.tin}</span>}
              </div>
            </div>
          </div>

          <div className="settings-section">
            <h3 className="settings-section-title">Receipt Settings</h3>

            <div className="field">
              <label htmlFor="receipt_footer">Receipt Footer Message</label>
              <input
                type="text"
                id="receipt_footer"
                name="receipt_footer"
                value={formData.receipt_footer}
                onChange={handleChange}
                disabled={saving}
              />
              {fieldErrors.receipt_footer && (
                <span className="error-message">{fieldErrors.receipt_footer}</span>
              )}
              <small>Message displayed at the bottom of printed receipts.</small>
            </div>

            <div className="field">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="is_vat_registered"
                  checked={formData.is_vat_registered}
                  onChange={handleChange}
                  disabled={saving}
                />
                <span>VAT Registered</span>
              </label>
              {fieldErrors.is_vat_registered && (
                <span className="error-message">{fieldErrors.is_vat_registered}</span>
              )}
              <small>Check if your restaurant is registered for VAT (12% output tax).</small>
            </div>
          </div>

          <div className="settings-section">
            <h3 className="settings-section-title">System Settings</h3>

            <div className="field-row">
              <div className="field">
                <label>Currency</label>
                <input type="text" value="PHP (₱)" disabled />
                <small>Fixed for v1.0</small>
              </div>
              <div className="field">
                <label>Timezone</label>
                <input type="text" value="Asia/Manila" disabled />
                <small>Fixed for v1.0</small>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Saving...' : 'Save Settings'}
            </button>
            <Link to="/dashboard" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default RestaurantSettings;