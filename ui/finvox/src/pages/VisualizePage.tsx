import React, { useState } from 'react';
import AppLayout from '../components/AppLayout';
import { LineChart, BarChart2, Download, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const VisualizePage: React.FC = () => {
  const navigate = useNavigate();
  const powerbiUrl = localStorage.getItem('powerbi_embed_url') || "";

  const [showPrintModal, setShowPrintModal] = useState(false);
  
  const handleExportPDF = () => {
    if (powerbiUrl) {
      setShowPrintModal(true);
    }
  };

  return (
    <AppLayout>
      <div style={{ padding: '0', width: '100%', height: '100vh', display: 'flex', flexDirection: 'column', background: '#fafbfc' }}>
        
        {/* Header (Minimal) */}
        <div style={{ padding: '1.5rem 2.5rem', background: 'white', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ background: '#ecfdf5', padding: '0.6rem', borderRadius: '10px', color: '#10b981' }}>
              <BarChart2 size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#111827', margin: 0, letterSpacing: '-0.5px' }}>
                Visualize Data
              </h1>
              <p style={{ color: '#6b7280', fontSize: '0.9rem', margin: 0 }}>
                Interactive BI reporting & visualizations
              </p>
            </div>
          </div>
          
          {powerbiUrl && (
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                onClick={() => navigate('/ingest')}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'transparent', border: '1px solid #e5e7eb', padding: '0.5rem 1rem', borderRadius: '8px', color: '#374151', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' }}
                title="Configure Connection"
              >
                <Settings size={16} /> Configure
              </button>
              <button 
                onClick={handleExportPDF}
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: '#111827', border: 'none', padding: '0.5rem 1.25rem', borderRadius: '8px', color: 'white', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}
              >
                <Download size={16} /> Export as PDF
              </button>
            </div>
          )}
        </div>

        {/* Dashboard Area */}
        <div style={{ flex: 1, padding: '1.5rem 2.5rem', overflow: 'hidden' }}>
          <div style={{ width: '100%', height: '100%', background: 'white', borderRadius: '16px', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {powerbiUrl ? (
              <iframe 
                title="FinVox Power BI Dashboard" 
                width="100%" 
                height="100%" 
                src={powerbiUrl} 
                frameBorder="0" 
                allowFullScreen={true}
                style={{ border: 'none' }}
              ></iframe>
            ) : (
              <div style={{ margin: 'auto', textAlign: 'center', color: '#6b7280' }}>
                <LineChart size={64} style={{ margin: '0 auto 1.5rem', opacity: 0.3 }} />
                <h3 style={{ marginBottom: '0.5rem', color: '#374151', fontSize: '1.5rem' }}>Power BI Not Connected</h3>
                <p style={{ marginBottom: '2rem', fontSize: '1.1rem' }}>You need to configure your Power BI Publish to Web URL first.</p>
                <button 
                  onClick={() => navigate('/ingest')}
                  style={{ background: '#111827', color: 'white', border: 'none', padding: '0.75rem 2rem', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', fontSize: '1rem' }}
                >
                  Go to Data Ingest
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Print Instruction Modal */}
        {showPrintModal && (
          <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}>
            <div style={{ background: 'white', borderRadius: '16px', padding: '2rem', width: '90%', maxWidth: '450px', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', color: '#1e293b' }}>
                <div style={{ background: '#f1f5f9', padding: '0.5rem', borderRadius: '50%' }}><Download size={24} /></div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Export Dashboard</h3>
              </div>
              <p style={{ color: '#475569', fontSize: '0.95rem', lineHeight: 1.5, marginBottom: '1.5rem' }}>
                Since you are using the free "Publish to Web" version of Power BI, automatic PDF export is not supported by Microsoft.
              </p>
              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem' }}>
                <p style={{ margin: 0, color: '#334155', fontSize: '0.9rem', fontWeight: 600 }}>How to save as PDF:</p>
                <ol style={{ margin: '0.5rem 0 0 0', paddingLeft: '1.25rem', color: '#475569', fontSize: '0.85rem', lineHeight: 1.6 }}>
                  <li>Click <strong>Open Dashboard</strong> below.</li>
                  <li>When the new tab opens, press <kbd style={{ background: '#e2e8f0', padding: '0.1rem 0.4rem', borderRadius: '4px', fontFamily: 'monospace' }}>Ctrl + P</kbd> (Windows) or <kbd style={{ background: '#e2e8f0', padding: '0.1rem 0.4rem', borderRadius: '4px', fontFamily: 'monospace' }}>Cmd + P</kbd> (Mac).</li>
                  <li>Save as PDF.</li>
                </ol>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button 
                  onClick={() => setShowPrintModal(false)}
                  style={{ background: 'transparent', border: '1px solid #cbd5e1', padding: '0.5rem 1rem', borderRadius: '8px', color: '#475569', fontWeight: 600, cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button 
                  onClick={() => {
                    window.open(powerbiUrl, '_blank');
                    setShowPrintModal(false);
                  }}
                  style={{ background: '#111827', border: 'none', padding: '0.5rem 1.25rem', borderRadius: '8px', color: 'white', fontWeight: 600, cursor: 'pointer' }}
                >
                  Open Dashboard
                </button>
              </div>
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  );
};

export default VisualizePage;
