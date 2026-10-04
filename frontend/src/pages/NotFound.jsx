import { Link } from 'react-router-dom';

export default function NotFound() {
  const destination = localStorage.getItem('token') ? '/' : '/login';
  const actionLabel = localStorage.getItem('token')
    ? 'Back to the editor'
    : 'Go to login';

  return (
    <div className="notfound-shell">
      <section className="auth-card notfound-card">
        <div>
          <p className="eyebrow">Error 404</p>
          <h2>This page does not exist.</h2>
          <p className="muted-text">
            The address you opened is not part of the workspace. It may have been
            renamed, or the link might be incomplete.
          </p>
        </div>

        <div className="editor-footer__actions">
          <Link className="primary-btn" to={destination}>
            {actionLabel}
          </Link>
          <Link className="ghost-btn" to="/register">
            Create an account
          </Link>
        </div>
      </section>
    </div>
  );
}
