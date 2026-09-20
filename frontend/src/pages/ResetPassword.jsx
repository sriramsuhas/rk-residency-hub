import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import AuthLayout from '../components/AuthLayout';
import { authApi } from '../api/auth';
import '../styles/forms.css';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    setSubmitting(true);
    try {
      await authApi.resetPassword(token, password);
      setDone(true);
      setTimeout(() => navigate('/login', { replace: true }), 1800);
    } catch (err) {
      setError(err.response?.data?.message || 'This reset link is invalid or has expired.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthLayout eyebrow="Account recovery" title="Choose a new password">
      {!token && <div className="alert alert-error">This link is missing a reset token.</div>}
      {error && <div className="alert alert-error">{error}</div>}
      {done && <div className="alert alert-success">Password updated. Redirecting to sign in…</div>}

      {!done && (
        <form onSubmit={handleSubmit} noValidate>
          <div className="form-field">
            <label htmlFor="password">New password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              required
              autoComplete="new-password"
            />
          </div>
          <button className="btn-primary" type="submit" disabled={submitting || !token}>
            {submitting ? 'Updating…' : 'Update password'}
          </button>
        </form>
      )}

      <p className="auth-footer-note">
        <Link to="/login" className="btn-link">
          Back to sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
