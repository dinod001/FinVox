import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AppLayout from '../components/AppLayout';
import { Database, HardDrive, Activity, Server, Loader2, Calendar, RefreshCw, TrendingUp, Plus, FileSpreadsheet, FileText, Check, MoreHorizontal, Trash2 } from 'lucide-react';

interface Metrics {
  qdrant: { status: string; points_count: number; collection?: string };
  supabase: { status: string; tables_count: number; rows_count: number; table_names?: string[] };
}

const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/health/metrics');
      const data = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error("Failed to fetch metrics", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000); // refresh every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <AppLayout>
      <div style={{ padding: '3rem', width: '100%', height: '100%', overflowY: 'auto', background: '#fafbfc' }}>
        
        {/* Header Section */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '3rem' }}>
          <div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: '#111827', marginBottom: '0.5rem', letterSpacing: '-0.5px' }}>
              System Dashboard
            </h1>
            <p style={{ color: '#6b7280', fontSize: '1.1rem' }}>
              Live usage metrics and storage capacity across FinVox cloud infrastructure.
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button style={{ 
              display: 'flex', alignItems: 'center', gap: '0.5rem', 
              background: 'white', border: '1px solid #e5e7eb', 
              padding: '0.75rem 1.25rem', borderRadius: '8px', 
              color: '#374151', fontWeight: 600, fontSize: '0.9rem',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
              cursor: 'default'
            }}>
              <Calendar size={18} color="#6b7280" />
              {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date())}
            </button>
            <button 
              onClick={fetchMetrics}
              style={{ 
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'white', border: '1px solid #e5e7eb', 
              padding: '0.75rem', borderRadius: '8px', 
              color: '#6b7280', cursor: 'pointer',
              boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)'
            }}>
              <RefreshCw size={18} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {/* Metric Cards */}
        {loading && !metrics ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '150px' }}>
            <Loader2 size={40} className="spin text-crimson" />
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            
            {/* AI Memory Card */}
            <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#8b5cf6' }}></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <h3 style={{ color: '#6b7280', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700 }}>Total AI Memories</h3>
                <div style={{ padding: '0.6rem', background: '#f5f3ff', color: '#8b5cf6', borderRadius: '12px' }}><HardDrive size={22} /></div>
              </div>
              <div style={{ fontSize: '3rem', fontWeight: 800, color: '#111827', lineHeight: 1, marginBottom: '0.5rem' }}>
                {metrics?.qdrant.points_count.toLocaleString() || '0'}
              </div>
              <div style={{ color: '#6b7280', fontSize: '0.95rem' }}>Memories across all clouds</div>
            </div>

            {/* Structured Datasets Card */}
            <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#3b82f6' }}></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
                <h3 style={{ color: '#6b7280', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700 }}>Structured Datasets</h3>
                <div style={{ padding: '0.6rem', background: '#eff6ff', color: '#3b82f6', borderRadius: '12px' }}><Database size={22} /></div>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                <div style={{ fontSize: '3rem', fontWeight: 800, color: '#111827', lineHeight: 1 }}>
                  {metrics?.supabase.rows_count.toLocaleString() || '0'}
                </div>
                <div style={{ color: '#6b7280', fontSize: '1.2rem', fontWeight: 500 }}>rows</div>
              </div>
            </div>

            {/* Active Connections Card */}
            <div style={{ background: 'white', padding: '2rem', borderRadius: '16px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, width: '4px', height: '100%', background: '#10b981' }}></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
                <h3 style={{ color: '#6b7280', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', fontWeight: 700 }}>Active Connections</h3>
                <div style={{ padding: '0.6rem', background: '#ecfdf5', color: '#10b981', borderRadius: '12px' }}><Activity size={22} /></div>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#111827', fontWeight: 600, fontSize: '1.05rem' }}>
                    <Server size={18} color="#6b7280" /> Qdrant Cloud
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: metrics?.qdrant.status === 'healthy' ? '#059669' : '#ef4444', fontSize: '0.75rem', fontWeight: 700, background: metrics?.qdrant.status === 'healthy' ? '#d1fae5' : '#fee2e2', padding: '0.25rem 0.6rem', borderRadius: '20px', letterSpacing: '0.5px' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'currentColor' }}></div> {metrics?.qdrant.status === 'healthy' ? 'LIVE' : 'DOWN'}
                  </div>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#111827', fontWeight: 600, fontSize: '1.05rem' }}>
                    <Database size={18} color="#6b7280" /> Supabase PostgreSQL
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: metrics?.supabase.status === 'healthy' ? '#059669' : '#ef4444', fontSize: '0.75rem', fontWeight: 700, background: metrics?.supabase.status === 'healthy' ? '#d1fae5' : '#fee2e2', padding: '0.25rem 0.6rem', borderRadius: '20px', letterSpacing: '0.5px' }}>
                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'currentColor' }}></div> {metrics?.supabase.status === 'healthy' ? 'LIVE' : 'DOWN'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Data Management Section */}
        <div style={{ marginTop: '3rem', background: 'white', borderRadius: '16px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', overflow: 'hidden' }}>
          <DatasetManager onUpdate={fetchMetrics} />
        </div>
      </div>
    </AppLayout>
  );
};

// --- Dataset Manager Component ---
const DatasetManager: React.FC<{ onUpdate: () => void }> = ({ onUpdate }) => {
  const [datasets, setDatasets] = useState<{ sql: any[], qdrant: any[] }>({ sql: [], qdrant: [] });
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchDatasets = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/management/datasets');
      setDatasets(await res.json());
    } catch (err) {
      console.error("Failed to fetch datasets", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleDelete = async (id: string, type: 'sql' | 'qdrant') => {
    if (!confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) return;
    
    setDeletingId(id);
    try {
      await fetch(`http://127.0.0.1:8000/management/${type}/${id}`, { method: 'DELETE' });
      await fetchDatasets();
      onUpdate();
    } catch (err) {
      alert('Failed to delete dataset');
    } finally {
      setDeletingId(null);
    }
  };

  const allDatasets = [...datasets.sql, ...datasets.qdrant].sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Just now';
    try {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }).format(date);
    } catch {
      return dateString;
    }
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2rem', borderBottom: '1px solid #e5e7eb' }}>
        <div>
          <h2 style={{ color: '#111827', fontSize: '1.4rem', fontWeight: 800, marginBottom: '0.25rem' }}>Manage Datasets</h2>
          <p style={{ color: '#6b7280', fontSize: '0.95rem' }}>View, manage and organize your datasets.</p>
        </div>
        <button 
          onClick={() => navigate('/ingest')}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            background: '#e11d48', color: 'white',
            padding: '0.75rem 1.25rem', borderRadius: '8px',
            fontWeight: 600, fontSize: '0.95rem', border: 'none',
            cursor: 'pointer', boxShadow: '0 4px 6px -1px rgba(225, 29, 72, 0.3)'
          }}
        >
          <Plus size={18} /> Add Dataset
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '4rem', textAlign: 'center' }}><Loader2 className="spin text-crimson" style={{ margin: '0 auto' }} /></div>
      ) : allDatasets.length === 0 ? (
        <div style={{ color: '#6b7280', textAlign: 'center', padding: '4rem', fontSize: '1.1rem' }}>No datasets uploaded yet.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb', background: '#f9fafb' }}>
                <th style={{ padding: '1rem 2rem', color: '#6b7280', fontWeight: 600, fontSize: '0.85rem' }}>Dataset Name</th>
                <th style={{ padding: '1rem', color: '#6b7280', fontWeight: 600, fontSize: '0.85rem' }}>Description</th>
                <th style={{ padding: '1rem', color: '#6b7280', fontWeight: 600, fontSize: '0.85rem' }}>Type</th>
                <th style={{ padding: '1rem', color: '#6b7280', fontWeight: 600, fontSize: '0.85rem' }}>Status</th>
                <th style={{ padding: '1rem 2rem', color: '#6b7280', fontWeight: 600, fontSize: '0.85rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {allDatasets.map((ds) => {
                const isSql = ds.type.includes('Structured');
                const isPdf = ds.name.toLowerCase().endsWith('.pdf');
                
                return (
                  <tr key={ds.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '1.5rem 2rem', width: '25%' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{ 
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          width: '40px', height: '40px', borderRadius: '10px',
                          background: isSql ? '#ecfdf5' : '#fef2f2',
                          color: isSql ? '#059669' : '#e11d48'
                        }}>
                          {isSql ? <FileSpreadsheet size={20} /> : <FileText size={20} />}
                        </div>
                        <span style={{ fontWeight: 700, color: '#111827', fontSize: '0.95rem' }}>{ds.name}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1.5rem 1rem', width: '30%', color: '#4b5563', fontSize: '0.9rem', lineHeight: 1.5 }}>
                      {ds.description || '-'}
                    </td>
                    <td style={{ padding: '1.5rem 1rem' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-start' }}>
                        <span style={{ 
                          background: isSql ? '#eff6ff' : '#f5f3ff', 
                          color: isSql ? '#2563eb' : '#7c3aed', 
                          padding: '0.2rem 0.6rem', 
                          borderRadius: '12px', 
                          fontSize: '0.75rem', 
                          fontWeight: 600 
                        }}>
                          {isSql ? 'Structured' : 'Unstructured'}
                        </span>
                        <span style={{ color: isSql ? '#2563eb' : '#7c3aed', fontSize: '0.75rem', fontWeight: 600, marginLeft: '0.2rem' }}>
                          {isSql ? '(CSV)' : '(PDF)'}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '1.5rem 1rem' }}>
                      <span style={{ 
                        display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
                        background: '#ecfdf5', color: '#059669', 
                        padding: '0.25rem 0.6rem', borderRadius: '12px', 
                        fontSize: '0.75rem', fontWeight: 600 
                      }}>
                        <Check size={12} /> Processed
                      </span>
                    </td>
                    <td style={{ padding: '1.5rem 2rem', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem' }}>
                        <button 
                          onClick={() => handleDelete(ds.id, isSql ? 'sql' : 'qdrant')}
                          disabled={deletingId === ds.id}
                          style={{
                            background: '#fef2f2', border: '1px solid #fecdd3',
                            color: '#e11d48', width: '36px', height: '36px',
                            borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            cursor: deletingId === ds.id ? 'not-allowed' : 'pointer'
                          }}
                        >
                          {deletingId === ds.id ? <Loader2 size={16} className="spin" /> : <Trash2 size={16} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem 2rem', borderTop: '1px solid #e5e7eb', background: '#f9fafb' }}>
            <div style={{ color: '#6b7280', fontSize: '0.85rem' }}>
              Showing 1 to {allDatasets.length} of {allDatasets.length} datasets
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', cursor: 'not-allowed' }}>&lt;</button>
              <button style={{ background: '#fdf2f8', border: '1px solid #fbcfe8', borderRadius: '6px', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#be185d', fontWeight: 600 }}>1</button>
              <button style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '6px', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', cursor: 'not-allowed' }}>&gt;</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DashboardPage;
