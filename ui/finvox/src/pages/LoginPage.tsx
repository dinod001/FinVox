import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { TrendingUp, Mail, Lock, ShieldCheck, Zap, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { authApi } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    
    try {
      const response = await authApi.login(username, password);
      // Save token and user id via Context
      login(response.access_token, response.user_id);
      
      // Navigate to chat
      navigate('/chat');
    } catch (err: any) {
      console.error('Login failed:', err);
      setErrorMsg(err.message || 'Invalid username or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      {/* Left Side - Marketing Info */}
      <div className="auth-left-content">
        <Link to="/" className="auth-brand-left">
          <img src="/logo.png" alt="FinVox Logo" className="brand-logo-img" style={{ height: '40px' }} />
        </Link>
        
        <h1 className="auth-left-title">
          AI-Powered Financial<br />
          Intelligence <span className="text-crimson">for SMEs</span>
        </h1>
        <p className="auth-left-subtitle">
          Welcome to FinVox. Log in to access your financial dashboard, real-time insights, cash flow analysis, and AI-powered recommendations to grow your business.
        </p>

        <div className="auth-features">
          <div className="a-feature">
            <div className="a-icon bg-red-light text-crimson"><TrendingUp size={20} /></div>
            <div>
              <h4>Real-time Insights</h4>
              <p>Monitor cash flow, revenue, expenses and more in real time.</p>
            </div>
          </div>
          <div className="a-feature">
            <div className="a-icon bg-red-light text-crimson"><ShieldCheck size={20} /></div>
            <div>
              <h4>Bank-level Security</h4>
              <p>Your data is encrypted and protected 24/7.</p>
            </div>
          </div>
          <div className="a-feature">
            <div className="a-icon bg-red-light text-crimson"><Zap size={20} /></div>
            <div>
              <h4>AI Recommendations</h4>
              <p>Get actionable suggestions to improve your business.</p>
            </div>
          </div>
        </div>

        {/* Dashboard Sidebar Mockup */}
        <div className="auth-mockup-app">
          <div className="ama-sidebar">
            <div className="ama-nav-item active" style={{ marginTop: '1rem'}}></div>
            <div className="ama-nav-item"></div>
            <div className="ama-nav-item"></div>
            <div className="ama-nav-item"></div>
            <div className="ama-nav-item"></div>
          </div>
          <div className="ama-main">
            <div className="ama-header">
              <div className="ama-header-line"></div>
              <div className="ama-header-line" style={{ width: '40px' }}></div>
            </div>
            <div className="ama-stats">
              <div className="ama-stat-card">
                <div className="ama-stat-title">Total Revenue</div>
                <div className="ama-stat-val">$48,250</div>
                <div className="ama-stat-change text-green">↑ 12.5%</div>
              </div>
              <div className="ama-stat-card">
                <div className="ama-stat-title">Net Cash Flow</div>
                <div className="ama-stat-val">$15,780</div>
                <div className="ama-stat-change text-green">↑ 8.4%</div>
              </div>
              <div className="ama-stat-card">
                <div className="ama-stat-title">Total Expenses</div>
                <div className="ama-stat-val">$32,470</div>
                <div className="ama-stat-change text-crimson">↓ 4.2%</div>
              </div>
            </div>
            <div className="ama-chart-area"></div>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form Card */}
      <div className="auth-right-content">
        <div className="auth-card">
          <div className="auth-header">
            <div className="auth-logo-circle">
              <img src="/logo.png" alt="FinVox Logo" className="brand-logo-img" style={{ height: '32px' }} />
            </div>
            <h2>Welcome Back</h2>
            <p className="text-muted">Log in to your FinVox account</p>
          </div>

          <form className="auth-form" onSubmit={handleLogin}>
            {errorMsg && (
              <div style={{ padding: '0.75rem', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} /> {errorMsg}
              </div>
            )}
            
            <div className="input-group">
              <label>Username or Email</label>
              <div className="input-wrapper">
                <Mail className="input-icon" size={18} />
                <input
                  type="text"
                  className="input-field with-icon"
                  placeholder="dinodimanjith206@gmail.com"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="input-group">
              <label>Password</label>
              <div className="input-wrapper">
                <Lock className="input-icon" size={18} />
                <input
                  type={showPassword ? "text" : "password"}
                  className="input-field with-icon"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button 
                  type="button" 
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div className="auth-options">
               <label className="remember-me">
                  <input type="checkbox" defaultChecked />
                  <span className="checkbox-custom"></span>
                  Remember me
               </label>
               <a href="#" className="forgot-password text-crimson">Forgot password?</a>
            </div>

            <button type="submit" className="btn-primary w-full sign-in-btn" disabled={isLoading}>
              {isLoading ? 'Signing in...' : 'Sign In →'}
            </button>
          </form>

          <div className="auth-footer">
            Don't have an account? <Link to="/register" className="text-crimson">Sign up</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
