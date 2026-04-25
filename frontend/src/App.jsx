import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import './App.css';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';

const hasStoredSession = () => Boolean(localStorage.getItem('token'));

function PrivateRoute({ children }) {
  return hasStoredSession() ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  return hasStoredSession() ? <Navigate to="/" replace /> : children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={(
            <PublicRoute>
              <Login />
            </PublicRoute>
          )}
        />
        <Route
          path="/register"
          element={(
            <PublicRoute>
              <Register />
            </PublicRoute>
          )}
        />
        <Route
          path="/"
          element={(
            <PrivateRoute>
              <Home />
            </PrivateRoute>
          )}
        />
      </Routes>
    </BrowserRouter>
  );
}
