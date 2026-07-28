import React, { useState, useRef, useEffect } from 'react';
import AppLayout from '../components/AppLayout';
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, FileText } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useIngestion } from '../contexts/IngestionContext';
import './IngestPage.css';

const IngestPage: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  
  const { isUploading, uploadError, response, startUpload, resetState } = useIngestion();
  const { userId } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setDescription('');
    resetState();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !userId || !description.trim()) return;
    await startUpload(selectedFile, userId, description.trim());
    // Only reset file selection if we succeeded
  };

  // When response arrives, we can reset the file so it shows the success state
  useEffect(() => {
    if (response) {
      setSelectedFile(null);
      setDescription('');
    }
  }, [response]);

  return (
    <AppLayout>
      <div className="ingest-container">
        
        {/* Header */}
        <div className="ingest-header-row">
          <div>
            <h1 className="ingest-title">Data Ingestion</h1>
            <p className="ingest-subtitle">
              Upload your latest financial documents, CSV ledgers, or connect to<br/>
              your accounting software to keep FinVox up to date.
            </p>
          </div>
          <button className="btn-learn-more">
            <AlertCircle size={16} /> Learn more
          </button>
        </div>

        {/* Main Upload Card */}
        <div className="card-container">
          {!isUploading && !response && (
            <div 
              className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => !selectedFile && fileInputRef.current?.click()}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                style={{ display: 'none' }} 
                onChange={(e) => {
                  if (e.target.files && e.target.files.length > 0) {
                    handleFileSelect(e.target.files[0]);
                  }
                }}
                accept=".csv,.xlsx,.pdf"
              />

              <img 
                src="/pink_folder.png" 
                alt="Folder Illustration" 
                className="illustration-right" 
                onError={(e) => e.currentTarget.style.display = 'none'}
              />

              {!selectedFile ? (
                <>
                  <div className="upload-icon-circle">
                    <UploadCloud size={28} />
                  </div>
                  <h2>Drag & drop your files here</h2>
                  <p>Supports CSV, XLSX, and PDF invoices up to 50MB</p>
                  
                  <button 
                    className="btn-upload"
                    onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                  >
                    <UploadCloud size={18} /> Browse Files
                  </button>

                  <div className="secure-badge">
                    <CheckCircle2 size={14} /> Your data is secure and encrypted
                  </div>
                </>
              ) : (
                <div style={{ textAlign: 'center', zIndex: 10 }}>
                  <div className="upload-icon-circle" style={{ margin: '0 auto 1rem auto' }}>
                    <FileText size={28} />
                  </div>
                  <h2>{selectedFile.name}</h2>
                  <p>{(selectedFile.size / 1024).toFixed(2)} KB</p>

                  <div style={{ marginBottom: '1.5rem', marginTop: '1rem' }}>
                    <input
                      type="text"
                      placeholder="Enter a brief description (e.g. 'January 2026 Cashflow')"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      style={{
                        width: '100%',
                        minWidth: '300px',
                        padding: '0.75rem 1rem',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        fontSize: '0.9rem',
                        outline: 'none',
                        color: '#1e293b'
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                    <button 
                      className="btn-learn-more"
                      onClick={(e) => { e.stopPropagation(); setSelectedFile(null); resetState(); }}
                    >
                      Cancel
                    </button>
                    <button 
                      className="btn-upload"
                      onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                      disabled={!description.trim()}
                      style={{ 
                        opacity: description.trim() ? 1 : 0.5, 
                        cursor: description.trim() ? 'pointer' : 'not-allowed' 
                      }}
                    >
                      Upload & Process
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Loading State */}
          {isUploading && (
            <div className="upload-dropzone" style={{ border: 'none', background: '#fdf2f8' }}>
              <Loader2 size={48} className="spin text-crimson" style={{ marginBottom: '1.5rem' }} />
              <h2>Processing Document...</h2>
              <p>Extracting data and generating embeddings securely.</p>
            </div>
          )}

          {/* Error State */}
          {uploadError && !isUploading && (
            <div style={{ background: '#fff1f2', padding: '1.5rem', borderRadius: '12px', border: '1px solid #fda4af', display: 'flex', alignItems: 'flex-start', gap: '1rem', marginBottom: '2rem' }}>
              <AlertCircle size={24} color="#e11d48" style={{ flexShrink: 0 }} />
              <div>
                <h3 style={{ color: '#be123c', marginBottom: '0.25rem' }}>Upload Failed</h3>
                <p style={{ color: '#9f1239', fontSize: '0.9rem' }}>{uploadError}</p>
              </div>
            </div>
          )}

          {/* Success State */}
          {response && !isUploading && (
            <div className="upload-dropzone" style={{ border: 'none', background: '#f0fdf4', padding: '3rem 2rem' }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '64px', height: '64px', borderRadius: '50%', background: '#dcfce7', color: '#166534', marginBottom: '1.5rem' }}>
                <CheckCircle2 size={32} />
              </div>
              <h2 style={{ color: '#166534' }}>Upload Successful!</h2>
              <p style={{ color: '#15803d', marginBottom: '2rem' }}>Your data has been securely ingested.</p>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.5rem', textAlign: 'left', background: 'white', padding: '1.5rem', borderRadius: '12px', border: '1px solid #bbf7d0', width: '100%', maxWidth: '500px', marginBottom: '2.5rem' }}>
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#166534', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>File Name</span>
                  <div style={{ fontWeight: 600, color: '#1e293b', marginTop: '0.25rem', wordBreak: 'break-all' }}>{response.file_name}</div>
                </div>
                <div>
                  <span style={{ fontSize: '0.8rem', color: '#166534', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Processing Time</span>
                  <div style={{ fontWeight: 600, color: '#1e293b', marginTop: '0.25rem' }}>{(response.time_taken_ms / 1000).toFixed(2)}s</div>
                </div>
                <div style={{ gridColumn: 'span 2' }}>
                  <span style={{ fontSize: '0.8rem', color: '#166534', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Details</span>
                  <div style={{ fontWeight: 500, color: '#1e293b', marginTop: '0.25rem' }}>{response.message || 'Completed'}</div>
                </div>
              </div>

              <button 
                className="btn-upload"
                style={{ background: '#166534' }}
                onClick={() => { resetState(); setSelectedFile(null); setDescription(''); }}
              >
                Upload Another File
              </button>
            </div>
          )}

          <h3 className="section-title">Or connect your accounting & BI software</h3>
          <div className="integrations-grid">
            <div className="integration-card">
              <div className="integration-logo" style={{ background: '#f2c811', color: 'black' }}>BI</div>
              <div className="integration-name">Power BI</div>
              <div className="integration-status">Connect</div>
            </div>
            <div className="integration-card">
              <div className="integration-logo" style={{ background: '#2ca01c' }}>qb</div>
              <div className="integration-name">QuickBooks</div>
              <div className="integration-status muted">Coming soon</div>
            </div>
            <div className="integration-card">
              <div className="integration-logo" style={{ background: '#13b5ea' }}>X</div>
              <div className="integration-name">Xero</div>
              <div className="integration-status muted">Coming soon</div>
            </div>
            <div className="integration-card">
              <div className="integration-logo" style={{ background: '#fce7f3', color: '#f472b6' }}>•••</div>
              <div className="integration-name">More</div>
              <div className="integration-status muted">Coming soon</div>
            </div>
          </div>
        </div>

      </div>
    </AppLayout>
  );
};

export default IngestPage;
