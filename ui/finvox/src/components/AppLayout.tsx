import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Database, LogOut, PanelLeftClose, PanelLeft, TrendingUp, BarChart2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './AppLayout.css';

interface AppLayoutProps {
  children: React.ReactNode;
  sidebarContent?: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, sidebarContent }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      {/* Primary Sidebar - Thin, Icons Only */}
      <nav className="primary-sidebar">
        <div className="sidebar-header">
          <div style={{ background: 'linear-gradient(135deg, var(--crimson), #fb7185)', padding: '10px', borderRadius: '12px', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <TrendingUp size={24} strokeWidth={2.5} />
          </div>
        </div>

        <div className="primary-nav-links">
          <NavLink to="/dashboard" className={({ isActive }) => `primary-nav-link ${isActive ? 'active' : ''}`} title="Dashboard">
            <LayoutDashboard size={22} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/chat" className={({ isActive }) => `primary-nav-link ${isActive ? 'active' : ''}`} title="Chat">
            <MessageSquare size={22} />
            <span>Chat</span>
          </NavLink>
          <NavLink to="/ingest" className={({ isActive }) => `primary-nav-link ${isActive ? 'active' : ''}`} title="Data Ingest">
            <Database size={22} />
            <span>Ingest</span>
          </NavLink>
          <NavLink to="/visualize" className={({ isActive }) => `primary-nav-link ${isActive ? 'active' : ''}`} title="Visualize">
            <BarChart2 size={22} />
            <span>Visualize</span>
          </NavLink>
        </div>

        <div className="sidebar-footer">
          {sidebarContent && !isSidebarOpen && (
            <button
              className="btn-logout-icon"
              onClick={() => setIsSidebarOpen(true)}
              title="Open Sidebar"
              style={{ marginBottom: '0.5rem' }}
            >
              <PanelLeft size={22} />
              <span>Expand</span>
            </button>
          )}
          <button className="btn-logout-icon" onClick={handleLogout} title="Log out">
            <LogOut size={22} />
            <span>Logout</span>
          </button>
        </div>
      </nav>

      {/* Secondary Sidebar - Only renders if there is sidebarContent and it's open */}
      {sidebarContent && isSidebarOpen && (
        <aside className="secondary-sidebar">
          <div className="secondary-sidebar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="sidebar-brand-text">FinVox</span>
            <button
              onClick={() => setIsSidebarOpen(false)}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: '0.25rem', borderRadius: '6px' }}
              onMouseOver={(e) => e.currentTarget.style.color = 'var(--text-main)'}
              onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
            >
              <PanelLeftClose size={20} />
            </button>
          </div>
          <div className="secondary-sidebar-content">
            {sidebarContent}
          </div>
        </aside>
      )}

      {/* Main Content Area */}
      <main className="main-content-area">
        {children}
      </main>
    </div>
  );
};

export default AppLayout;
