import React from 'react';
import AppLayout from '../components/AppLayout';

const DashboardPage: React.FC = () => {
  return (
    <AppLayout>
      <div style={{ padding: '3rem', width: '100%', height: '100%', overflowY: 'auto' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '1rem' }}>
          Dashboard Overview
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '3rem' }}>
          Welcome to your financial command center. Here you will see high-level insights, metrics, and trends.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {/* Dummy Metric Cards */}
          <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)' }}>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Total Revenue</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-main)' }}>LKR 4.2M</div>
            <div style={{ color: 'var(--green)', fontSize: '0.9rem', marginTop: '0.5rem', fontWeight: 500 }}>+12% from last month</div>
          </div>
          <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)' }}>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Operating Expenses</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-main)' }}>LKR 1.8M</div>
            <div style={{ color: 'var(--crimson)', fontSize: '0.9rem', marginTop: '0.5rem', fontWeight: 500 }}>+4% from last month</div>
          </div>
          <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)' }}>
            <h3 style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '0.5rem' }}>Net Profit Margin</h3>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-main)' }}>24.5%</div>
            <div style={{ color: 'var(--green)', fontSize: '0.9rem', marginTop: '0.5rem', fontWeight: 500 }}>+1.2% from last month</div>
          </div>
        </div>
        
        <div style={{ marginTop: '3rem', background: 'white', padding: '3rem', borderRadius: '16px', border: '1px solid var(--border-light)', textAlign: 'center' }}>
          <h2 style={{ color: 'var(--text-main)', marginBottom: '1rem' }}>Advanced Analytics Coming Soon</h2>
          <p style={{ color: 'var(--text-muted)' }}>We are currently building the charting and deeper analysis capabilities.</p>
        </div>
      </div>
    </AppLayout>
  );
};

export default DashboardPage;
