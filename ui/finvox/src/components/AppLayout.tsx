import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Database, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './AppLayout.css';

interface AppLayoutProps {
  children: React.ReactNode;
  sidebarContent?: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children, sidebarContent }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-layout">
      {/* Global Sidebar */}
      <aside className="global-sidebar">
        <div className="sidebar-header">
          <img src="/logo.png" alt="FinVox Logo" className="brand-logo-img" />
          <span className="sidebar-brand-text">FinVox</span>
        </div>

        {/* Primary Navigation */}
        <nav className="primary-nav">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/chat" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <MessageSquare size={20} />
            <span>Chat</span>
          </NavLink>
          <NavLink to="/ingest" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Database size={20} />
            <span>Data Ingest</span>
          </NavLink>
        </nav>

        {/* Dynamic Sidebar Content (e.g. Recent Sessions for ChatPage) */}
        {sidebarContent && (
          <div className="dynamic-sidebar-content">
            {sidebarContent}
          </div>
        )}

        <div className="sidebar-footer">
          <button className="btn-logout" onClick={handleLogout}>
            <LogOut size={16} /> Log out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content-area">
        {children}
      </main>
    </div>
  );
};

export default AppLayout;
