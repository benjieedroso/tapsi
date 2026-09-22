import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';

interface UserProfile {
  role: 'OWNER' | 'MANAGER' | 'CASHIER' | 'STAFF';
  restaurant?: { name: string };
}

export const SidebarLayout: React.FC<{ user: UserProfile | null }> = ({ user }) => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  const isOwnerOrManager = user?.role === 'OWNER' || user?.role === 'MANAGER';
  const isOwner = user?.role === 'OWNER';
  const isFinancialRole = isOwnerOrManager || user?.role === 'CASHIER';

  return (
    <div className="app-container">
      <aside className="sidebar">
        <NavLink className="navbar-logo" to="/dashboard">
          <div className="navbar-logo-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>
          </div>
          <span className="navbar-logo-text">TAPSI</span>
        </NavLink>

        <div className="sidebar-restaurant">
          <span className="nav-restaurant-name">{user?.restaurant?.name || 'My Restaurant'}</span>
        </div>

        <nav className="sidebar-nav">
          <ul className="sidebar-links">
            <li><NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>Dashboard</NavLink></li>
            <li><NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : '')}>Profile</NavLink></li>

            {isOwnerOrManager && (
              <>
                <li><NavLink to="/staff" className={({ isActive }) => (isActive ? 'active' : '')}>Staff</NavLink></li>
                <li><NavLink to="/menu" className={({ isActive }) => (isActive ? 'active' : '')}>Menu</NavLink></li>
                <li><NavLink to="/suppliers" className={({ isActive }) => (isActive ? 'active' : '')}>Suppliers</NavLink></li>
                <li><NavLink to="/recipes" className={({ isActive }) => (isActive ? 'active' : '')}>Recipes</NavLink></li>
              </>
            )}

            <li><NavLink to="/inventory" className={({ isActive }) => (isActive ? 'active' : '')}>Inventory</NavLink></li>
            <li><NavLink to="/orders" className={({ isActive }) => (isActive ? 'active' : '')}>Orders</NavLink></li>
            <li><NavLink to="/tables" className={({ isActive }) => (isActive ? 'active' : '')}>Tables</NavLink></li>
            <li><NavLink to="/kitchen" className={({ isActive }) => (isActive ? 'active' : '')}>Kitchen</NavLink></li>

            {isFinancialRole && (
              <li><NavLink to="/expenses" className={({ isActive }) => (isActive ? 'active' : '')}>Expenses</NavLink></li>
            )}

            <li><NavLink to="/attendance" className={({ isActive }) => (isActive ? 'active' : '')}>Attendance</NavLink></li>

            {isOwnerOrManager && (
              <>
                <li><NavLink to="/reports" className={({ isActive }) => (isActive ? 'active' : '')}>Reports</NavLink></li>
                <li><NavLink to="/closing" className={({ isActive }) => (isActive ? 'active' : '')}>Closing</NavLink></li>
                <li><NavLink to="/audit" className={({ isActive }) => (isActive ? 'active' : '')}>Audit</NavLink></li>
              </>
            )}

            {isOwner && (
              <li><NavLink to="/settings" className={({ isActive }) => (isActive ? 'active' : '')}>Settings</NavLink></li>
            )}

            <li><NavLink to="/notifications" className={({ isActive }) => (isActive ? 'active' : '')}>Bell</NavLink></li>
          </ul>
        </nav>

        <div className="sidebar-footer">
          <button onClick={handleLogout} type="button" className="btn btn-ghost">Log out</button>
        </div>
      </aside>

      <main className="app-main">
        <div className="container">
          <Outlet />
        </div>
      </main>
    </div>
  );
};