import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { Navigate } from 'react-router-dom';
import { authApi } from '../api/client';
import { setAccessToken } from '../api/client';

export function Layout() {
  const [user, setUser] = useState<{ email: string; full_name: string | null } | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setAccessToken(token);
      authApi.getMe()
        .then((res) => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('access_token');
          setAccessToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setAccessToken(null);
    setUser(null);
    navigate('/login');
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="loading-spinner" />
      </div>
    );
  }

  const isPublicRoute = ['/login', '/register'].includes(location.pathname);

  if (isPublicRoute && user) {
    return <Outlet />;
  }

  if (!isPublicRoute && !user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <NavLink to="/" className="font-bold text-xl text-blue-600">
              Prism Station
            </NavLink>
            <nav className="flex items-center gap-6">
              <NavLink
                to="/skills"
                className={({ isActive }) =>
                  `font-medium text-sm transition-colors ${isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600'}`
                }
              >
                Skills
              </NavLink>
              <NavLink
                to="/skills/new"
                className={({ isActive }) =>
                  `font-medium text-sm transition-colors ${isActive ? 'text-blue-600' : 'text-gray-600 hover:text-blue-600'}`
                }
              >
                New Skill
              </NavLink>
              {user && (
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600">{user.full_name || user.email}</span>
                  <button onClick={handleLogout} className="btn btn-ghost btn-sm">
                    Logout
                  </button>
                </div>
              )}
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-8 w-full">
        <Outlet />
      </main>
      <footer className="border-t border-gray-200 bg-white py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500">
          Prism Station - AI Agent Skill Management Platform
        </div>
      </footer>
    </div>
  );
}