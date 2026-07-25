import React, { useState, useRef } from 'react';
import AppLayout from '../components/AppLayout';
import { UploadCloud, CheckCircle2, AlertCircle, Loader2, FileText } from 'lucide-react';
import { ingestApi } from '../api/ingest';
import type { IngestionResponse } from '../api/ingest';
import { useAuth } from '../contexts/AuthContext';

const IngestPage: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [response, setResponse] = useState<IngestionResponse | null>(null);
  const { userId } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setDescription('');
    setUploadError(null);
    setResponse(null);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !userId) return;
    setIsUploading(true);
    setUploadError(null);
    
    try {
      const res = await ingestApi.uploadFile(selectedFile, userId, description);
      setResponse(res);
      setSelectedFile(null); // Reset selection on success
      setDescription('');
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <AppLayout>
      <div style={{ padding: '3rem', width: '100%', height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '1rem' }}>
          Data Ingestion
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '3rem' }}>
          Upload your latest financial documents, CSV ledgers, or connect to your accounting software to keep FinVox up to date.
        </p>

        {/* Upload Dropzone */}
        {!isUploading && !response && (
          <div 
            className="upload-dropzone"
            style={{
              border: `2px dashed ${isDragging ? 'var(--crimson)' : 'var(--border-light)'}`,
              borderRadius: '16px',
              background: isDragging ? 'var(--crimson-light)' : 'white',
              padding: '5rem 2rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              marginBottom: '2rem'
            }}
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

            {!selectedFile ? (
              <>
                <UploadCloud size={64} style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }} />
                <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>Drag & Drop your files here</h2>
                <p style={{ color: 'var(--text-muted)' }}>Supports CSV, XLSX, and PDF invoices</p>
                
                <button 
                  onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                  style={{ 
                    marginTop: '2rem', 
                    background: 'var(--text-main)', 
                    color: 'white', 
                    border: 'none', 
                    padding: '1rem 2rem', 
                    borderRadius: '10px', 
                    fontWeight: 600, 
                    cursor: 'pointer' 
                  }}
                >
                  Browse Files
                </button>
              </>
            ) : (
              <div style={{ textAlign: 'center' }}>
                <FileText size={64} className="text-crimson" style={{ marginBottom: '1.5rem' }} />
                <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>{selectedFile.name}</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>{(selectedFile.size / 1024).toFixed(2)} KB</p>

                <div style={{ marginBottom: '2rem', width: '100%', maxWidth: '400px', margin: '0 auto 2rem auto' }}>
                  <input
                    type="text"
                    placeholder="Enter a brief description (e.g. 'January 2026 Cashflow')"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    style={{
                      width: '100%',
                      padding: '0.75rem 1rem',
                      borderRadius: '8px',
                      border: '1px solid var(--border-light)',
                      fontSize: '0.95rem',
                      outline: 'none',
                      color: 'var(--text-main)'
                    }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                    style={{ padding: '0.75rem 1.5rem', background: '#f1f5f9', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleUpload(); }}
                    style={{ padding: '0.75rem 2rem', background: 'var(--crimson)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
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
          <div style={{ background: 'white', padding: '4rem', borderRadius: '16px', border: '1px solid var(--border-light)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
            <Loader2 size={48} className="spin text-crimson" style={{ marginBottom: '1.5rem' }} />
            <h2 style={{ color: 'var(--text-main)' }}>Processing Document...</h2>
            <p style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>This might take a few seconds as we extract data and generate embeddings.</p>
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
          <div style={{ background: 'white', padding: '3rem', borderRadius: '16px', border: '1px solid var(--border-light)', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)', textAlign: 'center' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '64px', height: '64px', borderRadius: '50%', background: 'var(--green-light)', color: 'var(--green)', marginBottom: '1.5rem' }}>
              <CheckCircle2 size={32} />
            </div>
            <h2 style={{ color: 'var(--text-main)', marginBottom: '0.5rem' }}>Upload Successful!</h2>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem' }}>Your data has been securely ingested into the FinVox knowledge base.</p>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', textAlign: 'left', background: '#f8fafc', padding: '1.5rem', borderRadius: '12px', marginBottom: '2rem' }}>
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>File Name</span>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '0.25rem' }}>{response.file_name}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Processing Time</span>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginTop: '0.25rem' }}>{(response.time_taken_ms / 1000).toFixed(2)}s</div>
              </div>
              <div style={{ gridColumn: 'span 2' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status Details</span>
                <div style={{ fontWeight: 500, color: 'var(--text-main)', marginTop: '0.25rem' }}>{response.status} - {response.message || 'Completed'}</div>
              </div>
            </div>

            <button 
              onClick={() => { setResponse(null); setUploadError(null); }}
              style={{ padding: '0.75rem 2rem', background: 'var(--text-main)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
            >
              Upload Another File
            </button>
          </div>
        )}
      </div>
    </AppLayout>
  );
};

export default IngestPage;
