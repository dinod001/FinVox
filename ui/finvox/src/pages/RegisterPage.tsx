import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { TrendingUp, Mail, Lock, User, ShieldCheck, Zap, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { authApi } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';
import './Auth.css';

const RegisterPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMsg('');
    
    try {
      const response = await authApi.register(username, email, password);
      // Save token and user id via context
      login(response.access_token, response.user_id);
      
      // Navigate to chat
      navigate('/chat');
    } catch (err: any) {
      console.error('Registration failed:', err);
      setErrorMsg(err.message || 'Registration failed. Please try again.');
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
          Join FinVox<br />
          Intelligence <span className="text-crimson">for SMEs</span>
        </h1>
        <p className="auth-left-subtitle">
          Create an account to access your financial dashboard, real-time insights, cash flow analysis, and AI-powered recommendations to grow your business.
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
      </div>

      {/* Right Side - Register Form Card */}
      <div className="auth-right-content">
        <div className="auth-card">
          <div className="auth-header">
            <div className="auth-logo-circle">
              <img src="/logo.png" alt="FinVox Logo" className="brand-logo-img" style={{ height: '32px' }} />
            </div>
            <h2>Create Account</h2>
            <p className="text-muted">Start your AI financial journey</p>
          </div>

          <form className="auth-form" onSubmit={handleRegister}>
            {errorMsg && (
              <div style={{ padding: '0.75rem', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertCircle size={16} /> {errorMsg}
              </div>
            )}
            
            <div className="input-group">
              <label>Full Name</label>
              <div className="input-wrapper">
                <User className="input-icon" size={18} />
                <input
                  type="text"
                  className="input-field with-icon"
                  placeholder="John Doe"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="input-group">
              <label>Email Address</label>
              <div className="input-wrapper">
                <Mail className="input-icon" size={18} />
                <input
                  type="email"
                  className="input-field with-icon"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
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
                  placeholder="Create a strong password"
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

            <button type="submit" className="btn-primary w-full sign-in-btn" disabled={isLoading} style={{ marginTop: '1rem' }}>
              {isLoading ? 'Creating account...' : 'Sign Up →'}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account? <Link to="/login" className="text-crimson">Log in</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
