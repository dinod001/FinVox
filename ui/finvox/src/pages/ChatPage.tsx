import React, { useState, useRef, useEffect } from 'react';
import {
  Send, TrendingUp, History, LogOut, CheckCircle2, Loader2, Play,
  ChevronDown, Bell, Crown, Wallet, PieChart, Target, Sparkles, Lock, Trash2
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
  let processed = text.replace(/\\\[/g, '$$$$').replace(/\\\]/g, '$$$$');
  processed = processed.replace(/\\\(/g, '$').replace(/\\\)/g, '$');
  processed = processed.replace(/^\[\s*\n/gm, '$$$$\n').replace(/\n\s*\]$/gm, '\n$$$$');
  return processed;
};

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const { userId } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Session State
  const [sessions, setSessions] = useState<ChatSessionMeta[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Real-time Clock State
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const formatted = now.toLocaleString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      });
      setCurrentTime(formatted);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

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
              {currentTime}
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
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm, remarkBreaks, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                        >
                          {preprocessMath(msg.content)}
                        </ReactMarkdown>
                      ) : (
                        <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                      )
                    ) : (msg.isStreaming && (
                      <div className="ai-thinking">
                        <Sparkles size={16} className="spin text-crimson" />
                        <span>FinVox is thinking...</span>
                      </div>
                    ))}

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
              <button
                className="btn-send-message"
                onClick={handleSend}
                disabled={!inputValue.trim() || isTyping}
              >
                {isTyping ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
              </button>
            </div>
          </div>
          <div className="chat-disclaimer">
            <Lock size={12} /> FinVox can make mistakes. Please verify important information.
          </div>
        </div>
      </div>
    </AppLayout>
  );
};

export default ChatPage;
