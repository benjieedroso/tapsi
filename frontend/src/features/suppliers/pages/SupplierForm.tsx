import React, { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { suppliersApi } from '../api/suppliers';

export const SupplierForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const action = isEdit ? 'Edit' : 'Add';

  const [name, setName] = useState<string>('');
  const [contactPerson, setContactPerson] = useState<string>('');
  const [phone, setPhone] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [address, setAddress] = useState<string>('');
  // Updated state type to match backend choice values
  const [paymentTerms, setPaymentTerms] = useState<'7D' | '15D' | '30D' | 'COD'>('COD');
  const [isActive, setIsActive] = useState<boolean>(true);

  const [loading, setLoading] = useState<boolean>(isEdit);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [nonFieldErrors, setNonFieldErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!id) return;
    const fetchSupplier = async () => {
      try {
        const data = await suppliersApi.getSupplierDetail(Number(id));
        setName(data.name || '');
        setPhone(data.phone || '');
        setIsActive(data.is_active ?? true);
        if ('contact_person' in data) setContactPerson((data as any).contact_person || '');
        if ('email' in data) setEmail((data as any).email || '');
        if ('address' in data) setAddress((data as any).address || '');
        if ('payment_terms' in data) setPaymentTerms((data as any).payment_terms || 'COD');
      } catch (err: any) {
        setNonFieldErrors([err.response?.data?.detail || 'Failed to load supplier data.']);
      } finally {
        setLoading(false);
      }
    };
    fetchSupplier();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setNonFieldErrors([]);
    setFieldErrors({});

    const payload = {
      name,
      contact_person: contactPerson || undefined,
      phone: phone || undefined,
      email: email || undefined,
      address: address || undefined,
      payment_terms: paymentTerms,
      is_active: isActive,
    };

    try {
      if (isEdit && id) {
        await suppliersApi.updateSupplier(Number(id), payload);
      } else {
        await suppliersApi.createSupplier(payload);
      }
      navigate('/suppliers');
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data;
        if (data.non_field_errors) {
          setNonFieldErrors(data.non_field_errors);
        }
        setFieldErrors(data);
      } else {
        setNonFieldErrors(['An unexpected error occurred. Please try again.']);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 'var(--space-4)' }}>Loading supplier...</div>;
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <h1>{action} Supplier</h1>
          <p style={{ color: 'var(--gray-500)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--space-1)' }}>
            Vendor master data for purchases.
          </p>
        </div>
      </div>

      <div className="form-card" style={{ maxWidth: '560px' }}>
        <form onSubmit={handleSubmit} noValidate>
          {nonFieldErrors.length > 0 && (
            <ul className="errorlist">
              {nonFieldErrors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          )}

          <div className="field">
            <label htmlFor="id_name">Supplier Name</label>
            <input
              type="text"
              id="id_name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            {fieldErrors.name && (
              <ul className="errorlist">
                <li>{fieldErrors.name}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_contact_person">Contact Person</label>
            <input
              type="text"
              id="id_contact_person"
              className="input"
              value={contactPerson}
              onChange={(e) => setContactPerson(e.target.value)}
            />
            {fieldErrors.contact_person && (
              <ul className="errorlist">
                <li>{fieldErrors.contact_person}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_phone">Phone</label>
            <input
              type="text"
              id="id_phone"
              className="input"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
            {fieldErrors.phone && (
              <ul className="errorlist">
                <li>{fieldErrors.phone}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_email">Email</label>
            <input
              type="email"
              id="id_email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            {fieldErrors.email && (
              <ul className="errorlist">
                <li>{fieldErrors.email}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_address">Address</label>
            <textarea
              id="id_address"
              className="input"
              rows={3}
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
            {fieldErrors.address && (
              <ul className="errorlist">
                <li>{fieldErrors.address}</li>
              </ul>
            )}
          </div>

          <div className="field">
            <label htmlFor="id_payment_terms">Payment Terms</label>
            <select
              id="id_payment_terms"
              className="input"
              value={paymentTerms}
              onChange={(e) => setPaymentTerms(e.target.value as any)}
              required
            >
              <option value="COD">Cash on Delivery (COD)</option>
              <option value="7D">7 Days</option>
              <option value="15D">15 Days</option>
              <option value="30D">30 Days</option>
            </select>
            {fieldErrors.payment_terms && (
              <ul className="errorlist">
                <li>{fieldErrors.payment_terms}</li>
              </ul>
            )}
          </div>

          <div className="field" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <input
              type="checkbox"
              id="id_is_active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <label htmlFor="id_is_active" style={{ margin: 0, cursor: 'pointer' }}>
              Active Supplier
            </label>
            {fieldErrors.is_active && (
              <ul className="errorlist">
                <li>{fieldErrors.is_active}</li>
              </ul>
            )}
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-6)' }}>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? 'Saving...' : `${action} Supplier`}
            </button>
            <Link to="/suppliers" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </>
  );
};

export default SupplierForm;