import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getErrorMessage, loginUser } from '../helpers/api';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      const response = await loginUser({ email, password });
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('username', response.data.username);
      navigate('/');
    } catch (err) {
      setError(getErrorMessage(err, 'Login failed.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-shell">
      <section className="auth-showcase">
        <p className="eyebrow">AI Code Editor</p>
        <h1>Pick up your coding flow right where you left it.</h1>
        <p>
          Use one workspace for smart completion, bug repair, code explanations,
          and recent session recall.
        </p>
        <div className="showcase-grid">
          <div className="showcase-card">
            <strong>Smart completion</strong>
            <span>Continue snippets without switching tabs.</span>
          </div>
          <div className="showcase-card">
            <strong>Bug repair</strong>
            <span>Spot issues and get corrected code faster.</span>
          </div>
          <div className="showcase-card">
            <strong>Explain mode</strong>
            <span>Turn dense code into plain language.</span>
          </div>
        </div>
      </section>

      <form className="auth-card" onSubmit={handleLogin}>
        <div>
          <p className="eyebrow">Welcome back</p>
          <h2>Sign in</h2>
          <p className="muted-text">Enter your account details to open the editor.</p>
        </div>

        {error && <p className="form-error">{error}</p>}

        <label className="field-group" htmlFor="login-email">
          <span className="field-label">Email</span>
          <input
            id="login-email"
            className="field-input"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="field-group" htmlFor="login-password">
          <span className="field-label">Password</span>
          <input
            id="login-password"
            className="field-input"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>

        <button className="primary-btn primary-btn--full" type="submit" disabled={submitting}>
          {submitting ? 'Signing in...' : 'Login'}
        </button>

        <p className="form-link">
          Don&apos;t have an account? <Link to="/register">Create one</Link>
        </p>
      </form>
    </div>
  );
}
