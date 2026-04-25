import { useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'Developer';

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  };

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">AI coding workspace</p>
        <h1 className="topbar-title">AI Code Editor</h1>
      </div>
      <div className="topbar-actions">
        <div className="profile-chip">
          <span className="profile-chip__label">Signed in as</span>
          <strong>{username}</strong>
        </div>
        <button className="ghost-btn ghost-btn--danger" type="button" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
