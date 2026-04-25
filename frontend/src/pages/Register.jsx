import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getErrorMessage, registerUser } from '../helpers/api';

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleRegister = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const response = await registerUser(form);
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('username', response.data.username);
      navigate('/');
    } catch (err) {
      setError(getErrorMessage(err, 'Registration failed.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-shell">
      <section className="auth-showcase">
        <p className="eyebrow">New workspace setup</p>
        <h1>Create your account and start coding with AI support.</h1>
        <p>
          Register once, then use the editor to complete code, fix issues,
          explain unfamiliar logic, and keep a history of recent sessions.
        </p>
        <div className="showcase-grid">
          <div className="showcase-card">
            <strong>Multi-language editor</strong>
            <span>Python, JavaScript, TypeScript, Java, and C++ support.</span>
          </div>
          <div className="showcase-card">
            <strong>Session history</strong>
            <span>Reopen earlier AI requests directly from the dashboard.</span>
          </div>
          <div className="showcase-card">
            <strong>Simple setup</strong>
            <span>Connect your MongoDB and Gemini keys, then launch both apps.</span>
          </div>
        </div>
      </section>

      <form className="auth-card" onSubmit={handleRegister}>
        <div>
          <p className="eyebrow">Create account</p>
          <h2>Register</h2>
          <p className="muted-text">Set up your profile to unlock the editor.</p>
        </div>

        {error && <p className="form-error">{error}</p>}

        <label className="field-group" htmlFor="register-username">
          <span className="field-label">Username</span>
          <input
            id="register-username"
            className="field-input"
            placeholder="Choose a username"
            value={form.username}
            onChange={(event) => setForm({ ...form, username: event.target.value })}
            required
            minLength={3}
          />
        </label>

        <label className="field-group" htmlFor="register-email">
          <span className="field-label">Email</span>
          <input
            id="register-email"
            className="field-input"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
            required
          />
        </label>

        <label className="field-group" htmlFor="register-password">
          <span className="field-label">Password</span>
          <input
            id="register-password"
            className="field-input"
            type="password"
            placeholder="At least 6 characters"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
            required
            minLength={6}
          />
        </label>

        <button className="primary-btn primary-btn--full" type="submit" disabled={submitting}>
          {submitting ? 'Creating account...' : 'Register'}
        </button>

        <p className="form-link">
          Already have an account? <Link to="/login">Login</Link>
        </p>
      </form>
    </div>
  );
}
