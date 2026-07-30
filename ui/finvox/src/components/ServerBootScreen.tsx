import React, { useEffect, useState } from 'react';

const ServerBootScreen: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isServerReady, setIsServerReady] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/health');
        if (response.ok) {
          setIsServerReady(true);
        } else {
          setTimeout(() => setRetryCount((prev) => prev + 1), 2000);
        }
      } catch (error) {
        setTimeout(() => setRetryCount((prev) => prev + 1), 2000);
      }
    };

    if (!isServerReady) {
      checkHealth();
    }
  }, [retryCount, isServerReady]);

  if (isServerReady) {
    return <>{children}</>;
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: '#0f172a', /* dark slate */
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, color: 'white', fontFamily: "'Inter', sans-serif"
    }}>
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes spin-reverse { 100% { transform: rotate(-360deg); } }
        .boot-spinner-outer {
          width: 64px; height: 64px; border-radius: 50%;
          border: 4px solid rgba(185, 28, 28, 0.2);
          border-top-color: #b91c1c; /* Crimson primary */
          animation: spin 1s linear infinite;
        }
        .boot-spinner-inner {
          width: 32px; height: 32px; border-radius: 50%;
          border: 4px solid rgba(239, 68, 68, 0.2);
          border-bottom-color: #ef4444;
          animation: spin-reverse 1.5s linear infinite;
          position: absolute; top: 16px; left: 16px;
        }
      `}</style>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px' }}>
        <div style={{ position: 'relative', width: '64px', height: '64px' }}>
          <div className="boot-spinner-outer"></div>
          <div className="boot-spinner-inner"></div>
        </div>
        
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 8px 0', color: '#ffffff' }}>
            FinVox AI is Starting...
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0, lineHeight: '1.5' }}>
            Warming up AI models and connecting to databases.<br />
            Please wait a moment.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ServerBootScreen;
