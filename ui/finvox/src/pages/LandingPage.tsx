import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, TrendingUp, ShieldCheck, Zap, PlayCircle, 
  CheckCircle2, Users, Star, DollarSign, Clock,
  FileText, BrainCircuit, LineChart, Lock,
  Cloud, Cpu, Lightbulb, ArrowRight, Loader2,
  MessageSquare, FileSpreadsheet
} from 'lucide-react';
import './LandingPage.css';

const LandingPage: React.FC = () => {
  const [typedText, setTypedText] = useState("");
  const fullText = "Based on current projections, your Q1 cash flow is forecasted at +$245K. I recommend shifting $50K to high-yield bonds.";
  
  useEffect(() => {
    let i = 0;
    const typingInterval = setInterval(() => {
      if (i < fullText.length) {
        setTypedText(fullText.slice(0, i + 1));
        i++;
      } else {
        clearInterval(typingInterval);
      }
    }, 40); // typing speed
    
    return () => clearInterval(typingInterval);
  }, []);

  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="nav-brand">
          <img src="/logo.png" alt="FinVox Logo" className="brand-logo-img" />
        </div>
        <div className="nav-links-center">
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#reviews">Reviews</a>
          <a href="#pricing">Pricing</a>
        </div>
        <div className="nav-actions">
          <Link to="/login" className="nav-link-login">Log in</Link>
          <Link to="/register" className="btn-primary">Get Started Free →</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="hero-section">
        {/* Decorative Background Elements */}
        <div className="hero-bg-grid"></div>
        <div className="hero-blob-1"></div>
        <div className="hero-blob-2"></div>
        
        <div className="hero-content-left">
          <div className="hero-badge text-crimson">
            <Zap size={14} />
            <span>AI-Powered Financial Intelligence</span>
          </div>
          <h1 className="hero-title">
            The AI Financial Advisor<br />
            <span className="text-crimson">Built for Modern SMEs</span>
          </h1>
          <p className="hero-subtitle">
            No need for a human accountant. FinVox AI handles your payments, automates bookkeeping, and forecasts cash flow—putting your business finances on autopilot.
          </p>
          <div className="hero-cta-group">
            <Link to="/register" className="btn-primary btn-large">Get Started Free →</Link>
            <Link to="/chat" className="btn-outline btn-large watch-demo-btn" style={{ textDecoration: 'none' }}>
              <PlayCircle size={20} /> Watch Demo
            </Link>
          </div>
          <div className="hero-trust-marks">
            <span><CheckCircle2 size={16} className="text-crimson"/> No credit card required</span>
            <span><CheckCircle2 size={16} className="text-crimson"/> Bank-level security</span>
            <span><CheckCircle2 size={16} className="text-crimson"/> Setup in 2 minutes</span>
          </div>
        </div>
        
        <div className="hero-content-right">
          {/* Abstract Dashboard Mockup */}
          <div className="mockup-container">
            <div className="mockup-window glass-panel">
              <div className="mockup-header">
                <div className="mockup-brand"><TrendingUp size={16} className="text-crimson"/> FinVox</div>
                <div className="mockup-nav">Dashboard</div>
              </div>
              <div className="mockup-body">
                <div className="mockup-sidebar">
                   <div className="m-nav-item active"></div>
                   <div className="m-nav-item"></div>
                   <div className="m-nav-item"></div>
                   <div className="m-nav-item"></div>
                </div>
                <div className="mockup-main">
                  <div className="mockup-cards">
                    <div className="m-card">
                      <div className="m-card-title">Total Revenue</div>
                      <div className="m-card-value">$48,250</div>
                      <div className="m-card-change text-green">↑ 12.5%</div>
                    </div>
                    <div className="m-card">
                      <div className="m-card-title">Net Cash Flow</div>
                      <div className="m-card-value">$15,780</div>
                      <div className="m-card-change text-green">↑ 8.4%</div>
                    </div>
                    <div className="m-card">
                      <div className="m-card-title">Total Expenses</div>
                      <div className="m-card-value">$32,470</div>
                      <div className="m-card-change text-crimson">↓ 4.2%</div>
                    </div>
                  </div>
                  <div className="mockup-chart">
                    <div className="m-chart-header">Cash Flow Overview</div>
                    <div className="m-line-container">
                       <svg viewBox="0 0 400 100" className="m-svg-line" preserveAspectRatio="none">
                          <path d="M0,80 C50,70 100,90 150,50 C200,10 250,60 300,30 C350,0 400,20 400,20" fill="none" stroke="#e11d48" strokeWidth="3" strokeLinecap="round" />
                          <path d="M0,80 C50,70 100,90 150,50 C200,10 250,60 300,30 C350,0 400,20 400,20 L400,100 L0,100 Z" fill="url(#redGradient)" stroke="none" opacity="0.2" />
                          <defs>
                            <linearGradient id="redGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                              <stop offset="0%" stopColor="#e11d48" stopOpacity="1" />
                              <stop offset="100%" stopColor="#e11d48" stopOpacity="0" />
                            </linearGradient>
                          </defs>
                       </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Animated AI Chat Overlay */}
            <div className="floating-ai-chat glass-panel">
               <div className="ai-chat-header">
                  <div className="ai-avatar"><TrendingUp size={12} color="white"/></div>
                  <span>FinVox AI</span>
                  <Loader2 size={12} className="spin text-crimson ml-auto" />
               </div>
               <div className="ai-chat-body">
                  <p>{typedText}<span className="blinking-cursor">|</span></p>
               </div>
            </div>

            {/* Floating Elements */}
            <div className="floating-el el-1 glass-panel">
              <TrendingUp size={16} className="text-crimson"/>
              <div>
                <p className="el-title">+$12,400</p>
                <p className="el-sub">Revenue</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="stats-section">
        <div className="stat-item">
          <div className="stat-icon bg-red-light text-crimson"><Users size={24} /></div>
          <div>
            <h3>500+</h3>
            <p>SMEs Trust FinVox</p>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon bg-green-light text-green"><CheckCircle2 size={24} /></div>
          <div>
            <h3>98%</h3>
            <p>Customer Satisfaction</p>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon bg-blue-light text-blue"><DollarSign size={24} /></div>
          <div>
            <h3>$25M+</h3>
            <p>Transactions Processed</p>
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-icon bg-purple-light text-purple"><Clock size={24} /></div>
          <div>
            <h3>24/7</h3>
            <p>AI Assistance</p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <div className="features-section-wrapper">
        <section className="features-section" id="features">
          <div className="section-header">
            <h2>Everything you need to scale smarter</h2>
            <p>Powerful tools designed specifically for modern founders and finance teams.</p>
          </div>
        
        <div className="features-grid-6">
          <div className="f-card">
            <div className="f-icon bg-red-light text-crimson"><BarChart3 size={24} /></div>
            <h3>Cashflow Intelligence</h3>
            <p>Monitor cash flow in real-time and get AI-powered insights to stay ahead.</p>
            <a href="#" className="f-link text-crimson">Learn More →</a>
          </div>
          <div className="f-card">
            <div className="f-icon bg-green-light text-green"><MessageSquare size={24} /></div>
            <h3>Natural Language Queries</h3>
            <p>Talk to your database using plain English. No complex SQL required.</p>
            <a href="#" className="f-link text-crimson">Learn More →</a>
          </div>
          <div className="f-card">
            <div className="f-icon bg-blue-light text-blue"><BrainCircuit size={24} /></div>
            <h3>AI Insights</h3>
            <p>Get actionable recommendations to improve profitability.</p>
            <a href="#" className="f-link text-crimson">Learn More →</a>
          </div>
          <div className="f-card">
            <div className="f-icon bg-orange-light text-orange"><FileSpreadsheet size={24} /></div>
            <h3>Spreadsheet Intelligence</h3>
            <p>Upload CSVs & Excel files to instantly analyze your financial data.</p>
            <a href="#" className="f-link text-crimson">Learn More →</a>
          </div>
          <div className="f-card">
            <div className="f-icon bg-purple-light text-purple"><FileText size={24} /></div>
            <h3>PDF & Report Analysis</h3>
            <p>Upload financial PDFs and instantly get answers via our RAG engine.</p>
            <a href="#" className="f-link text-crimson">Learn More →</a>
          </div>
          <div className="f-card">
            <div className="f-icon bg-red-light text-crimson"><Lock size={24} /></div>
            <h3>Bank-grade Security</h3>
            <p>Your data is encrypted and protected with enterprise-level security.</p>
            <a href="#" className="f-link text-crimson">Learn More →</a>
          </div>
          </div>
        </section>
      </div>

      {/* Split Section */}
      <section className="split-section">
        <div className="split-left">
          <div className="small-badge text-crimson">Real-time Financial Overview</div>
          <h2>All Your Financials.<br/>All in <span className="text-crimson">One Place.</span></h2>
          <p>Get a 360° view of your business finances. Understand your performance, identify opportunities, and make data-driven decisions with confidence.</p>
          <ul className="feature-list">
            <li><CheckCircle2 size={16} className="text-crimson"/> Real-time dashboards & reports</li>
            <li><CheckCircle2 size={16} className="text-crimson"/> AI-powered trend analysis</li>
            <li><CheckCircle2 size={16} className="text-crimson"/> Custom alerts & notifications</li>
            <li><CheckCircle2 size={16} className="text-crimson"/> Multi-currency & multi-entity support</li>
          </ul>
          <Link to="/chat" className="btn-primary mt-4">Explore Dashboard →</Link>
        </div>
        <div className="split-right">
          <div className="mockup-panel glass-panel">
             <div className="m-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                   <h3 style={{ fontSize: '1rem', margin: 0 }}>Cash Flow Overview</h3>
                   <p style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, marginTop: '0.25rem' }}>$15,780 <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600}}>↑ 8.4% vs last month</span></p>
                </div>
                <div style={{ padding: '0.25rem 0.5rem', border: '1px solid #e2e8f0', borderRadius: '4px', fontSize: '0.75rem'}}>This Month</div>
             </div>
             
             <div className="m-chart-area" style={{ height: '120px', marginBottom: '2rem', position: 'relative' }}>
                <svg viewBox="0 0 400 100" className="m-svg-line" preserveAspectRatio="none">
                    <path d="M0,90 C40,80 80,95 120,60 C160,25 200,70 240,40 C280,10 320,50 360,10 C380,-5 400,20 400,20" fill="none" stroke="#e11d48" strokeWidth="2.5" strokeLinecap="round" />
                    <path d="M0,90 C40,80 80,95 120,60 C160,25 200,70 240,40 C280,10 320,50 360,10 C380,-5 400,20 400,20 L400,100 L0,100 Z" fill="url(#redGradient2)" stroke="none" opacity="0.15" />
                    <defs>
                      <linearGradient id="redGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#e11d48" stopOpacity="1" />
                        <stop offset="100%" stopColor="#e11d48" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                </svg>
             </div>
             
             <div className="m-bottom-split">
               <div style={{ flex: 1 }}>
                  <h4 style={{ fontSize: '0.8rem', marginBottom: '1rem', color: '#64748b' }}>Expenses by Category</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <div className="m-pie">
                       <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 800 }}>$32,470</span><br/>
                          <span style={{ fontSize: '0.5rem', color: '#64748b' }}>Total</span>
                       </div>
                    </div>
                    <ul style={{ listStyle: 'none', padding: 0, fontSize: '0.7rem', flex: 1 }}>
                       <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: '#3b82f6'}}>● Operations</span> <span>40%</span></li>
                       <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: '#e11d48'}}>● Marketing</span> <span>25%</span></li>
                       <li style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}><span style={{ color: '#10b981'}}>● Salaries</span> <span>20%</span></li>
                       <li style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#f97316'}}>● Software</span> <span>15%</span></li>
                    </ul>
                  </div>
               </div>
               
               <div className="m-stats">
                  <h4 style={{ fontSize: '0.8rem', marginBottom: '1rem', color: '#64748b' }}>Profit & Loss Summary</h4>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem', marginBottom: '0.5rem', fontSize: '0.8rem' }}>
                     <span style={{ fontWeight: 600 }}>Revenue</span>
                     <div style={{ textAlign: 'right' }}>
                        <span style={{ fontWeight: 800, display: 'block' }}>$48,250</span>
                        <span style={{ fontSize: '0.65rem', color: '#10b981' }}>↑ 12.5%</span>
                     </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f1f5f9', paddingBottom: '0.5rem', marginBottom: '0.5rem', fontSize: '0.8rem' }}>
                     <span style={{ fontWeight: 600 }}>Gross Profit</span>
                     <div style={{ textAlign: 'right' }}>
                        <span style={{ fontWeight: 800, display: 'block' }}>$20,890</span>
                        <span style={{ fontSize: '0.65rem', color: '#10b981' }}>↑ 18.2%</span>
                     </div>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                     <span style={{ fontWeight: 600 }}>Net Profit</span>
                     <div style={{ textAlign: 'right' }}>
                        <span style={{ fontWeight: 800, display: 'block' }}>$15,780</span>
                        <span style={{ fontSize: '0.65rem', color: '#10b981' }}>↑ 15.3%</span>
                     </div>
                  </div>
               </div>
             </div>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="steps-section" id="how-it-works">
        <div className="section-header">
          <h2>How FinVox Works</h2>
        </div>
        <div className="steps-container">
          <div className="step-box">
            <div className="step-icon text-crimson bg-red-light"><Cloud size={24}/></div>
            <h4>1. Upload Data</h4>
            <p>Upload your financial PDFs, CSVs, and Excel spreadsheets directly.</p>
          </div>
          <div className="step-arrow"><ArrowRight className="text-muted"/></div>
          <div className="step-box">
            <div className="step-icon text-green bg-green-light"><Cpu size={24}/></div>
            <h4>2. Analyze</h4>
            <p>Our AI analyzes your data in real-time and extracts meaningful insights.</p>
          </div>
          <div className="step-arrow"><ArrowRight className="text-muted"/></div>
          <div className="step-box">
            <div className="step-icon text-blue bg-blue-light"><BarChart3 size={24}/></div>
            <h4>3. Insight</h4>
            <p>Get AI-powered insights, forecasts and actionable recommendations.</p>
          </div>
          <div className="step-arrow"><ArrowRight className="text-muted"/></div>
          <div className="step-box">
            <div className="step-icon text-orange bg-orange-light"><Lightbulb size={24}/></div>
            <h4>4. Grow</h4>
            <p>Make smarter decisions, improve cash flow and grow your business.</p>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="testimonials-section" id="reviews">
        <div className="section-header">
          <h2>Loved by Business Owners</h2>
        </div>
        <div className="testimonials-grid">
          <div className="testimonial-card">
            <div className="stars">
              <Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/>
            </div>
            <p>"FinVox has transformed the way we manage our finances. The AI insights are spot on and save us hours every week."</p>
            <div className="t-author">
              <img src="https://randomuser.me/api/portraits/men/32.jpg" alt="Nimal Perera" className="t-avatar" />
              <div>
                <h5>Nimal Perera</h5>
                <span>CEO, TechSolutions (Pvt) Ltd.</span>
              </div>
            </div>
          </div>
          <div className="testimonial-card">
            <div className="stars">
              <Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/>
            </div>
            <p>"Cash flow forecasting is incredibly accurate. It helps us plan ahead and avoid surprises."</p>
            <div className="t-author">
              <img src="https://randomuser.me/api/portraits/women/44.jpg" alt="Kavindi Fernando" className="t-avatar" />
              <div>
                <h5>Kavindi Fernando</h5>
                <span>Founder, GreenLeaf Organics</span>
              </div>
            </div>
          </div>
          <div className="testimonial-card">
            <div className="stars">
              <Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/><Star size={16} className="text-yellow" fill="currentColor"/>
            </div>
            <p>"The document intelligence feature is a game changer. No more manual data entry!"</p>
            <div className="t-author">
              <img src="https://randomuser.me/api/portraits/men/46.jpg" alt="Tharindu Silva" className="t-avatar" />
              <div>
                <h5>Tharindu Silva</h5>
                <span>Finance Manager, BuildPro</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-banner" id="pricing">
        <div className="cta-content">
          <div>
            <h2>Ready to Transform Your Financial Future?</h2>
            <p>Join 500+ SMEs using FinVox to grow their business with AI.</p>
          </div>
          <Link to="/register" className="btn-primary btn-large">Start Free Trial →</Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-top">
          <div className="footer-brand">
            <div className="nav-brand mb-4">
              <img src="/logo.png" alt="FinVox Logo" className="brand-logo-img" />
            </div>
            <p>AI-powered financial intelligence platform for modern SMEs.</p>
          </div>
          
          <div className="footer-pricing">
             <div className="price-card">
                <div className="p-header"><Zap size={16}/> Product</div>
                <p>Perfect for small businesses</p>
                <h3>$19<span>/month</span></h3>
             </div>
             <div className="price-card popular">
                <div className="popular-badge">Most Popular</div>
                <div className="p-header text-crimson"><Star size={16}/> Professional</div>
                <p>Best for growing businesses</p>
                <h3>$49<span>/month</span></h3>
             </div>
             <div className="price-card">
                <div className="p-header"><ShieldCheck size={16}/> Enterprise</div>
                <p>For established businesses</p>
                <h3>Custom</h3>
             </div>
          </div>
          
          <div className="footer-newsletter">
            <h4>Newsletter</h4>
            <p>Get the latest updates and financial insights.</p>
            <div className="newsletter-form">
              <input type="email" placeholder="Enter your email" />
              <button className="btn-primary">Subscribe</button>
            </div>
          </div>
        </div>
        
        <div className="footer-bottom">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <p>© 2026 FinVox. All rights reserved.</p>
          </div>
          <div className="footer-links">
            <a href="#">Terms of Service</a>
            <a href="#">Privacy Policy</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
