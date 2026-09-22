import React from 'react';
import { Link } from 'react-router-dom';

export const PasswordResetDone: React.FC = () => {
  return (
    <section className="auth-card">
      <h1>Check your email</h1>
      <p>
        If an active account matches the address entered, a password-reset link has
        been sent.
      </p>
      <div style={{ textAlign: 'center', marginTop: 'var(--space-6, 1.5rem)' }}>
        <Link to="/login" className="btn btn-secondary">
          Back to login
        </Link>
      </div>
    </section>
  );
};

export default PasswordResetDone;