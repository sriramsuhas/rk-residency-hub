import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';
import RoleAvatar from './RoleAvatar';
import './TopNav.css';

export default function TopNav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="topnav">
      <Link to="/" className="topnav__brand">
        RK Residency Hub
      </Link>
      <nav className="topnav__actions">
        {user?.role === 'CUSTOMER' && (
          <>
            <Link to="/" className="topnav__link topnav__link--primary">
              Book a Room
            </Link>
            <Link to="/my-bookings" className="topnav__link">
              My Bookings
            </Link>
            <Link to="/my-requests" className="topnav__link">
              Maintenance
            </Link>
          </>
        )}
        {user?.role === 'RECEPTION' && (
          <>
            <Link to="/" className="topnav__link topnav__link--primary">
              Bookings
            </Link>
            <Link to="/reception/maintenance" className="topnav__link">
              Maintenance
            </Link>
            <Link to="/reports" className="topnav__link">
              Reports
            </Link>
          </>
        )}
        {user?.role === 'HOUSEKEEPING' && (
          <Link to="/" className="topnav__link topnav__link--primary">
            My Tasks
          </Link>
        )}
        {user?.role === 'OWNER' && (
          <>
            <Link to="/" className="topnav__link topnav__link--primary">
              Dashboard
            </Link>
            <Link to="/manage-rooms" className="topnav__link">
              Rooms
            </Link>
            <Link to="/manage-users" className="topnav__link">
              Users
            </Link>
            <Link to="/reports" className="topnav__link">
              Reports
            </Link>
            <Link to="/audit-log" className="topnav__link">
              Audit Log
            </Link>
          </>
        )}
        {user && <NotificationBell />}
        {user && (
          <>
            <Link to="/profile" className="topnav__profile">
              <RoleAvatar role={user.role} className="topnav__avatar" />
              <span>{user.full_name}</span>
              <span className="topnav__role">{user.role}</span>
            </Link>
            <button className="topnav__logout" onClick={handleLogout}>
              Sign out
            </button>
          </>
        )}
        {!user && (
          <>
            <Link to="/login" className="topnav__link">
              Login
            </Link>
            <Link to="/register" className="topnav__link topnav__link--primary">
              Book a Room
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}
