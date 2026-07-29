import React, { useEffect, useState } from 'react';

const PrintDashboardPage: React.FC = () => {
  const powerbiUrl = localStorage.getItem('powerbi_embed_url') || "";
  const [isPrinting, setIsPrinting] = useState(true);

  useEffect(() => {
    if (powerbiUrl) {
      // Wait 3.5 seconds to allow Power BI to fully render before opening the print dialog
      const timer = setTimeout(() => {
        window.print();
        setIsPrinting(false);
      }, 3500);
      
      return () => clearTimeout(timer);
    }
  }, [powerbiUrl]);

  if (!powerbiUrl) {
    return <div style={{ padding: '2rem', textAlign: 'center', fontFamily: 'sans-serif' }}>No Power BI Dashboard configured.</div>;
  }

  return (
    <>
      <style>
        {`
          @page { size: landscape; margin: 0; }
          body, html { margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }
          .print-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(255,255,255,0.9);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            font-family: sans-serif;
          }
          @media print {
            .print-overlay { display: none !important; }
          }
        `}
      </style>
      
      {isPrinting && (
        <div className="print-overlay">
          <div style={{ width: '40px', height: '40px', border: '4px solid #f3f3f3', borderTop: '4px solid #10b981', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <h2 style={{ color: '#111827', marginTop: '1rem' }}>Preparing Dashboard for Export...</h2>
          <p style={{ color: '#6b7280' }}>Please wait while the report loads. The print dialog will open automatically.</p>
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      <iframe 
        title="Print Power BI"
        src={powerbiUrl}
        style={{ width: '100vw', height: '100vh', border: 'none' }}
      />
    </>
  );
};

export default PrintDashboardPage;
