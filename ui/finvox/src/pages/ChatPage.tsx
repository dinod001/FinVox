import React, { useState, useRef, useEffect } from 'react';
import {
  Send, TrendingUp, History, LogOut, CheckCircle2, Loader2, Play,
  ChevronDown, Bell, Crown, Wallet, PieChart, Target, Sparkles, Lock, Trash2, Download, Mic
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { chatSessionsApi } from '../api/chat_sessions';
import type { ChatSessionMeta } from '../api/chat_sessions';
import { chatApi } from '../api/chat';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import AppLayout from '../components/AppLayout';
import DynamicChart from '../components/DynamicChart';
import type { ChartConfig } from '../components/DynamicChart';
import VoiceAgentModal from '../components/VoiceAgentModal';
import './ChatPage.css';

interface TimelineEvent {
  stage: string;
  label: string;
  status: 'pending' | 'active' | 'done' | 'error';
  ms?: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  timeline?: TimelineEvent[];
}

const preprocessMath = (text: string) => {
  if (!text) return text;
  
  // Protect all code blocks from math preprocessing to avoid corrupting JSON/code
  const codeBlocks: string[] = [];
  let processed = text.replace(/```[\s\S]*?```/g, (match) => {
    codeBlocks.push(match);
    return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
  });

  processed = processed.replace(/\\\[/g, '$$$$').replace(/\\\]/g, '$$$$');
  processed = processed.replace(/\\\(/g, '$').replace(/\\\)/g, '$');
  processed = processed.replace(/^\[\s*\n/gm, '$$$$\n').replace(/\n\s*\]$/gm, '\n$$$$');

  // Restore code blocks
  processed = processed.replace(/__CODE_BLOCK_(\d+)__/g, (_, idx) => codeBlocks[parseInt(idx)]);
  
  return processed;
};

const MarkdownTable = ({ children, ...props }: any) => {
  const tableRef = useRef<HTMLTableElement>(null);

  const downloadCSV = () => {
    if (!tableRef.current) return;
    const rows = Array.from(tableRef.current.querySelectorAll('tr'));
    const csv = rows.map(row => {
      const cols = Array.from(row.querySelectorAll('th, td'));
      return cols.map(c => `"${(c.textContent || '').replace(/"/g, '""')}"`).join(',');
    }).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'finvox_data.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.5rem' }}>
        <button 
          onClick={downloadCSV}
          title="Download Data as CSV"
          style={{
            background: 'var(--bg-card)',
            color: 'var(--text-main)',
            border: '1px solid var(--border-light)',
            padding: '4px 10px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 500,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            transition: 'all 0.2s ease',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--crimson)';
            e.currentTarget.style.color = 'white';
            e.currentTarget.style.borderColor = 'var(--crimson)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--bg-card)';
            e.currentTarget.style.color = 'var(--text-main)';
            e.currentTarget.style.borderColor = 'var(--border-light)';
          }}
        >
          <Download size={14} /> Export CSV
        </button>
      </div>
      <div style={{ overflowX: 'auto', border: '1px solid var(--border-light)', borderRadius: '8px' }}>
        <table ref={tableRef} {...props} style={{ width: '100%', borderCollapse: 'collapse', ...props.style }}>
          {children}
        </table>
      </div>
    </div>
  );
};

const RealtimeClock = () => {
  const [time, setTime] = useState<string>('');
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleString('en-US', { 
        year: 'numeric', month: 'short', day: 'numeric', 
        hour: '2-digit', minute: '2-digit', second: '2-digit' 
      }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);
  return <>{time}</>;
};

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const { userId } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);

  // Session State
  const [sessions, setSessions] = useState<ChatSessionMeta[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);


  const skipFetchRef = useRef(false);

  // Fetch initial sessions
  useEffect(() => {
    if (userId) {
      chatSessionsApi.listSessions(userId).then(res => {
        setSessions(res.sessions);
        if (res.sessions.length > 0 && !activeSessionId) {
          setActiveSessionId(res.sessions[0].id);
        }
      }).catch(console.error);
    }
  }, [userId]);

  // Fetch messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      if (skipFetchRef.current) {
        skipFetchRef.current = false;
        return;
      }
      chatSessionsApi.getMessages(activeSessionId)
        .then(history => {
          const loadedMsgs: Message[] = history.map((m: any) => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            timestamp: new Date(m.ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }));
          setMessages(loadedMsgs);
        })
        .catch(console.error);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  const handleNewChat = async () => {
    if (!userId) return;
    try {
      const newSession = await chatSessionsApi.createSession(userId);
      setSessions(prev => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]); // Clear chat window
    } catch (e) { console.error('Failed to create chat', e); }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    try {
      await chatSessionsApi.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch (e) { console.error('Failed to delete session', e); }
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');
    setIsTyping(true);

    // Dummy payload, now with dynamic user_id and session_id
    let targetSessionId = activeSessionId;
    if (!targetSessionId && userId) {
      // Auto-create session if none active
      try {
        const s = await chatSessionsApi.createSession(userId);
        setSessions(prev => [s, ...prev]);
        skipFetchRef.current = true;
        setActiveSessionId(s.id);
        targetSessionId = s.id;
      } catch (e) { console.error(e); }
    }

    const payload = {
      user_id: userId || "guest",
      session_id: targetSessionId || "temp-session",
      message: newUserMsg.content
    };

    const assistantMsgId = (Date.now() + 1).toString();
    setMessages(prev => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isStreaming: true,
        timeline: []
      }
    ]);

    let finalContent = "";

    await chatApi.sendMessageStream(
      payload.user_id,
      payload.session_id,
      payload.message,
      {
        onStageStart: (stage, label) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId ? {
              ...m,
              timeline: [...(m.timeline || []), { stage, label, status: 'active' }]
            } : m
          ));
        },
        onStageDone: (stage, ms) => {
          setMessages(prev => prev.map(m =>
            m.id === assistantMsgId ? {
              ...m,
              timeline: (m.timeline || []).map(item =>
                item.stage === stage ? { ...item, status: 'done', ms } : item
              )
            } : m
          ));
        },
        onToken: (token) => {
          finalContent += token;
          setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: finalContent } : m));
        },
        onDone: () => {
          setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, isStreaming: false } : m));
          setIsTyping(false);
        },
        onError: (error) => {
          console.error("Stream error:", error);
          setIsTyping(false);
          setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: "Sorry, I encountered an error connecting to the server.", isStreaming: false } : m));
        }
      }
    );
  };

  const sidebarContent = (
    <div style={{ padding: '0 1rem' }}>
      <button className="btn-new-chat" onClick={handleNewChat} style={{ marginBottom: '1.5rem', width: '100%' }}>
        <Sparkles size={16} /> New Chat
      </button>
      <div className="sidebar-nav">
        <div className="nav-section">
          <h4 className="section-title" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>RECENT SESSIONS</h4>
          <ul className="session-list" style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {sessions.map(session => (
              <li
                key={session.id}
                className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <div className="si-icon"><History size={16} /></div>
                <div className="si-content">
                  <span className="si-title">{session.title}</span>
                  <span className="si-time">{new Date(session.updated_at).toLocaleDateString()}</span>
                </div>
                <button
                  className="delete-session-btn"
                  onClick={(e) => handleDeleteSession(e, session.id)}
                  title="Delete Chat"
                >
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
            {sessions.length === 0 && (
              <div style={{ padding: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                No recent chats.
              </div>
            )}
          </ul>
        </div>
      </div>
    </div>
  );

  return (
    <AppLayout sidebarContent={sidebarContent}>
      {/* Main Chat Area */}
      <div className="chat-main" style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <header className="chat-header">
          <div className="ch-left">
            <h2>{sessions.find(s => s.id === activeSessionId)?.title || 'New Conversation'}</h2>
            <ChevronDown size={20} className="text-muted" />
          </div>
          <div className="ch-right">
            <div className="realtime-clock text-muted" style={{ fontSize: '0.9rem', marginRight: '1rem', fontWeight: 500 }}>
              <RealtimeClock />
            </div>
            <div className="status-badge">
              <span className="dot bg-green blink-light"></span> AI Connected
            </div>
            <button className="icon-btn"><Bell size={20} /></button>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginLeft: '1rem' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
                Welcome, {userId ? userId.split(' ')[0].charAt(0).toUpperCase() + userId.split(' ')[0].slice(1) : 'Guest'}
              </span>
              <div className="user-avatar">
                {userId ? userId.charAt(0).toUpperCase() : 'G'}
              </div>
            </div>
          </div>
        </header>

        {/* Chat Content area */}
        <div className="chat-content-area">
          {messages.length === 0 ? (
            <div className="empty-state-container">
              {/* Welcome Section */}
              <div className="welcome-header">
                <div className="welcome-icon">
                  <TrendingUp size={32} className="text-crimson" />
                  <Sparkles size={16} className="sparkle s-1" />
                  <Sparkles size={12} className="sparkle s-2" />
                  <Sparkles size={18} className="sparkle s-3" />
                </div>
                <h1>Welcome to FinVox</h1>
                <p>Your AI-powered financial advisor for smarter business decisions.<br />Ask me anything about your finances, cash flow, or investments.</p>
              </div>

              {/* Action Cards */}
              <div className="action-cards-grid">
                <div className="action-card">
                  <div className="ac-icon bg-red-light text-crimson"><Wallet size={20} /></div>
                  <div className="ac-text">
                    <h4>Cash Flow Overview</h4>
                    <p>Analyze my cash flow this month</p>
                  </div>
                </div>
                <div className="action-card">
                  <div className="ac-icon bg-green-light text-green"><TrendingUp size={20} /></div>
                  <div className="ac-text">
                    <h4>Profitability Analysis</h4>
                    <p>How is my business performing?</p>
                  </div>
                </div>
                <div className="action-card">
                  <div className="ac-icon bg-orange-light text-orange"><PieChart size={20} /></div>
                  <div className="ac-text">
                    <h4>Expense Insights</h4>
                    <p>Show me my top expenses</p>
                  </div>
                </div>
                <div className="action-card">
                  <div className="ac-icon bg-purple-light text-purple"><Target size={20} /></div>
                  <div className="ac-text">
                    <h4>Growth Opportunities</h4>
                    <p>Where can I invest or grow?</p>
                  </div>
                </div>
              </div>

              {/* Insights Widget removed as requested */}
            </div>
          ) : (
            <div className="chat-messages">
              {messages.map((msg) => (
                <div key={msg.id} className={`message-wrapper ${msg.role}`}>
                  <div className="message-content">
                    {msg.content ? (
                      msg.role === 'assistant' ? (
                        <div id={`report-${msg.id}`} style={{ width: '100%' }}>
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm, remarkBreaks, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={{
                            pre({ children, ...props }: any) {
                              // Check if the child is a <code class="language-chart"> block
                              const child = Array.isArray(children) ? children[0] : children;
                              if (child?.props?.className?.includes('language-chart')) {
                                const raw = String(child.props.children).replace(/\n$/, '');
                                try {
                                  const config = JSON.parse(raw) as ChartConfig;
                                  return <DynamicChart config={config} />;
                                } catch {
                                  return (
                                    <div style={{ color: '#e11d48', border: '1px solid #fca5a5', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                                      ⚠️ Failed to render chart. Raw data:<br />
                                      <pre style={{ fontSize: '11px', marginTop: '8px', overflowX: 'auto' }}>{raw}</pre>
                                    </div>
                                  );
                                }
                              }
                              return <pre {...props}>{children}</pre>;
                            },
                            table: MarkdownTable
                          }}
                        >
                          {preprocessMath(msg.content)}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                      )
                    ) : (msg.isStreaming && (
                      <div className="ai-thinking">
                        <Sparkles size={16} className="spin text-crimson" />
                        <span>FinVox is thinking...</span>
                      </div>
                    ))}

                    {/* Download Report Button */}
                    {msg.role === 'assistant' && !msg.isStreaming && msg.content && msg.content.length > 50 && (
                      <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-start' }}>
                        <button 
                          onClick={() => {
                            const element = document.getElementById(`report-${msg.id}`);
                            if (element) {
                              // @ts-ignore
                              import('html2pdf.js').then((module) => {
                                const html2pdf = module.default || module;
                                html2pdf().from(element).set({
                                  margin: 15,
                                  filename: `FinVox_Report_${new Date().toISOString().slice(0,10)}.pdf`,
                                  image: { type: 'jpeg', quality: 0.98 },
                                  html2canvas: { 
                                    scale: 2, 
                                    useCORS: true,
                                    onclone: (clonedDoc: Document) => {
                                      const clonedEl = clonedDoc.getElementById(`report-${msg.id}`);
                                      if (clonedEl) {
                                        clonedEl.style.width = '800px';
                                        clonedEl.style.padding = '20px';
                                        clonedEl.style.background = 'white';
                                        clonedEl.style.color = 'black';
                                        
                                        const style = clonedDoc.createElement('style');
                                        style.innerHTML = `
                                          * { color: black !important; font-family: sans-serif; }
                                          table { width: 100% !important; border-collapse: collapse; margin-bottom: 20px; overflow: visible !important; }
                                          th, td { border: 1px solid #ccc; padding: 10px; text-align: left; }
                                          th { background-color: #f5f5f5 !important; font-weight: bold; }
                                          pre { white-space: pre-wrap; word-wrap: break-word; background: #f8f9fa !important; padding: 15px; border-radius: 5px; border: 1px solid #ddd; }
                                          code { color: #d63384 !important; background: none !important; }
                                          h1, h2, h3, h4, h5 { color: #1a1a1a !important; border-bottom: 1px solid #eee; padding-bottom: 5px; margin-top: 25px; margin-bottom: 15px; }
                                          p, li { line-height: 1.6; margin-bottom: 10px; }
                                          
                                          /* CRITICAL: Prevent elements from slicing horizontally across pages */
                                          h1, h2, h3, h4, h5, p, li, tr, pre, img {
                                            page-break-inside: avoid !important;
                                            break-inside: avoid !important;
                                          }
                                        `;
                                        clonedEl.appendChild(style);
                                      }
                                    }
                                  },
                                  jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
                                  pagebreak: { mode: ['css', 'legacy'], avoid: ['tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'p', 'li', 'pre', 'strong'] }
                                }).save();
                              }).catch((err: any) => {
                                console.error("Failed to load html2pdf", err);
                              });
                            }
                          }}
                          style={{
                            background: 'var(--bg-main)',
                            border: '1px solid var(--border-light)',
                            borderRadius: '8px',
                            padding: '6px 14px',
                            fontSize: '0.8rem',
                            fontWeight: 500,
                            color: 'var(--text-main)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            boxShadow: '0 2px 5px rgba(0,0,0,0.05)'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = 'var(--crimson)';
                            e.currentTarget.style.color = 'var(--crimson)';
                            e.currentTarget.style.transform = 'translateY(-1px)';
                            e.currentTarget.style.boxShadow = '0 4px 8px rgba(220,20,60,0.1)';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = 'var(--border-light)';
                            e.currentTarget.style.color = 'var(--text-main)';
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 2px 5px rgba(0,0,0,0.05)';
                          }}
                          title="Download as Markdown"
                        >
                          <Download size={14} /> Download Report
                        </button>
                      </div>
                    )}


                    {/* Render Timeline (Hidden as per user request) 
                    {msg.timeline && msg.timeline.length > 0 && (
                      <div className="agent-timeline">
                        {msg.timeline.map((item, idx) => (
                          <div key={idx} className={`timeline-item ${item.status}`}>
                            {item.status === 'active' ? (
                              <Loader2 size={14} className="spin" />
                            ) : item.status === 'done' ? (
                              <CheckCircle2 size={14} className="text-crimson" />
                            ) : (
                              <Play size={14} />
                            )}
                            <span className="timeline-label">{item.label}</span>
                            {item.ms && <span className="timeline-ms">{item.ms}ms</span>}
                          </div>
                        ))}
                      </div>
                    )}
                    */}
                  </div>
                  <div className="message-time">{msg.timestamp}</div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="chat-bottom-area">
          <div className="chat-input-wrapper">
            <input
              type="text"
              className="chat-input-field"
              placeholder="Ask FinVox a financial question..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend();
              }}
              disabled={isTyping}
            />
            <div className="chat-input-actions">
              <button className="btn-smart-sugg">
                <Sparkles size={14} className="text-crimson" /> Smart Suggestions
              </button>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button 
                  className="btn-voice-chat"
                  onClick={() => setIsVoiceModalOpen(true)}
                  title="Start Voice Chat"
                  style={{
                    background: 'linear-gradient(135deg, var(--crimson), #ff4d6d)',
                    border: 'none', 
                    borderRadius: '50%', width: '42px', height: '42px', 
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', cursor: 'pointer', transition: 'all 0.3s ease',
                    boxShadow: '0 4px 12px rgba(220, 20, 60, 0.3)'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'scale(1.08)';
                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(220, 20, 60, 0.5)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(220, 20, 60, 0.3)';
                  }}
                >
                  <Mic size={20} />
                </button>
                <button
                  className="btn-send-message"
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isTyping}
                >
                  {isTyping ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
                </button>
              </div>
            </div>
          </div>
          <div className="chat-disclaimer">
            <Lock size={12} /> FinVox can make mistakes. Please verify important information.
          </div>
        </div>
      </div>

      <VoiceAgentModal 
        isOpen={isVoiceModalOpen} 
        onClose={() => setIsVoiceModalOpen(false)} 
        userId={userId || undefined}
        roomName={activeSessionId || undefined}
      />
    </AppLayout>
  );
};

export default ChatPage;
