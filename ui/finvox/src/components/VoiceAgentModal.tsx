import React, { useState, useEffect } from 'react';
import { 
  LiveKitRoom, 
  RoomAudioRenderer, 
  useVoiceAssistant,
  useTrackVolume,
  TrackToggle
} from '@livekit/components-react';
import { Track } from 'livekit-client';
import { X, Loader2, PhoneOff } from 'lucide-react';
import { apiClient } from '../api/client';
import '@livekit/components-styles';

interface VoiceAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId?: string;
  roomName?: string;
}

const OrbVisualizer = ({ state, trackRef }: { state: string, trackRef: any }) => {
  const volume = useTrackVolume(trackRef); 
  const scale = 1 + (volume * 0.7);
  
  let color = 'rgba(255, 255, 255, 0.1)';
  let solidColor = 'var(--text-muted)';
  
  if (state === 'listening') {
    color = 'rgba(59, 130, 246, 0.4)';
    solidColor = '#3b82f6';
  } else if (state === 'thinking') {
    color = 'rgba(16, 185, 129, 0.4)';
    solidColor = '#10b981';
  } else if (state === 'speaking') {
    color = 'rgba(220, 20, 60, 0.5)';
    solidColor = 'var(--crimson)';
  }

  return (
    <div style={{
      width: '120px',
      height: '120px',
      borderRadius: '50%',
      backgroundColor: state === 'speaking' ? color : 'transparent',
      transform: `scale(${state === 'speaking' ? scale : 1})`,
      transition: state === 'speaking' ? 'transform 0.05s ease-out' : 'all 0.5s ease',
      boxShadow: `0 0 ${40 * scale}px ${color}, inset 0 0 ${20 * scale}px ${color}`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      margin: '20px auto'
    }}>
      <div style={{
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        background: `linear-gradient(135deg, ${solidColor}, ${solidColor}88)`,
        boxShadow: `0 4px 15px ${color}`,
        animation: state === 'thinking' ? 'pulse-orb 1.5s infinite alternate' : 
                   state === 'listening' ? 'pulse-orb 2s infinite alternate' : 'none',
        transition: 'all 0.3s ease'
      }}>
        <style>
          {`
            @keyframes pulse-orb {
              0% { transform: scale(1); opacity: 0.8; }
              100% { transform: scale(1.15); opacity: 1; }
            }
          `}
        </style>
      </div>
    </div>
  );
};

const VoiceAssistantUI = ({ onClose }: { onClose: () => void }) => {
  const { state, audioTrack } = useVoiceAssistant();

  // Glow color based on state
  let glowColor = 'transparent';
  if (state === 'listening') glowColor = 'rgba(59, 130, 246, 0.2)'; // Blue
  else if (state === 'speaking') glowColor = 'rgba(220, 20, 60, 0.3)'; // Crimson
  else if (state === 'thinking') glowColor = 'rgba(16, 185, 129, 0.2)'; // Green

  return (
    <div style={{ 
      background: 'var(--bg-main)', 
      borderRadius: '24px', 
      padding: '40px 20px',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '10px',
      transition: 'all 0.4s ease',
      boxShadow: `0 0 40px ${glowColor}, inset 0 0 20px rgba(0,0,0,0.1)`,
      border: `1px solid ${state !== 'disconnected' && state !== 'initializing' ? glowColor : 'var(--border-light)'}`
    }}>
      
      <div style={{
        textAlign: 'center',
        color: state === 'speaking' ? 'var(--crimson)' : 'var(--text-muted)',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '2px',
        fontSize: '0.85rem',
        transition: 'color 0.3s',
        marginBottom: '10px'
      }}>
        {state === 'initializing' ? 'Connecting...' : 
         state === 'listening' ? 'Listening...' : 
         state === 'thinking' ? 'Thinking...' : 
         state === 'speaking' ? 'FinVox is speaking' : 'Ready'}
      </div>

      <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%' }}>
        <OrbVisualizer state={state} trackRef={audioTrack} />
      </div>
      
      <div style={{ display: 'flex', gap: '24px', marginTop: '10px' }}>
        <TrackToggle 
          source={Track.Source.Microphone} 
          className="custom-track-toggle"
        />
        
        <button 
          onClick={onClose}
          style={{
            background: 'var(--bg-card)',
            border: '1px solid rgba(220, 20, 60, 0.3)',
            borderRadius: '50%',
            width: '56px',
            height: '56px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--crimson)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: '0 4px 10px rgba(0,0,0,0.1)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--crimson)';
            e.currentTarget.style.color = 'white';
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--bg-card)';
            e.currentTarget.style.color = 'var(--crimson)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
          title="Disconnect"
        >
          <PhoneOff size={24} />
        </button>
      </div>

      <style>
        {`
          .custom-track-toggle {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-light) !important;
            border-radius: 50% !important;
            width: 56px !important;
            height: 56px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: var(--text-main) !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1) !important;
          }
          .custom-track-toggle:hover {
            background: var(--bg-hover) !important;
            transform: scale(1.05) !important;
          }
          .custom-track-toggle[data-state="disabled"] {
            color: var(--crimson) !important;
            border-color: rgba(220, 20, 60, 0.3) !important;
            background: rgba(220, 20, 60, 0.05) !important;
          }
          .custom-track-toggle svg {
            width: 24px !important;
            height: 24px !important;
          }
        `}
      </style>
    </div>
  );
};

const VoiceAgentModal: React.FC<VoiceAgentModalProps> = ({ 
  isOpen, 
  onClose, 
  userId = "guest", 
  roomName = "finvox-voice-room" 
}) => {
  const [token, setToken] = useState<string>("");
  const [url, setUrl] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isConnecting, setIsConnecting] = useState<boolean>(true);

  useEffect(() => {
    if (isOpen) {
      connectToVoice();
    } else {
      // Reset state when closed
      setToken("");
      setUrl("");
      setError("");
      setIsConnecting(true);
    }
  }, [isOpen]);

  const connectToVoice = async () => {
    setIsConnecting(true);
    setError("");
    try {
      const data = await apiClient.post("/voice/token", {
        user_id: userId,
        room_name: roomName
      });
      setToken(data.access_token);
      setUrl(data.url);
    } catch (err: any) {
      console.error("Failed to get voice token:", err);
      setError("Failed to connect to the Voice Server. Is the backend running?");
    } finally {
      setIsConnecting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}>
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-light)',
        borderRadius: '16px',
        width: '90%',
        maxWidth: '500px',
        padding: '24px',
        position: 'relative',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)'
      }}>
        <button 
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '16px', right: '16px',
            background: 'none', border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          <X size={20} />
        </button>

        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            FinVox Voice Assistant
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Speak naturally to your financial AI
          </p>
        </div>

        <div style={{ minHeight: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {isConnecting ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: 'var(--text-muted)' }}>
              <Loader2 className="spin text-crimson" size={32} />
              <span>Connecting to secure voice room...</span>
            </div>
          ) : error ? (
            <div style={{ color: 'var(--crimson)', textAlign: 'center', background: 'var(--bg-main)', padding: '16px', borderRadius: '8px' }}>
              <p>{error}</p>
              <button 
                onClick={connectToVoice}
                style={{
                  marginTop: '12px', background: 'var(--crimson)', color: 'white',
                  border: 'none', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer'
                }}
              >
                Try Again
              </button>
            </div>
          ) : token && url ? (
            <div style={{ width: '100%' }}>
              <LiveKitRoom
                serverUrl={url}
                token={token}
                connect={true}
                audio={true}
                video={false}
              >
                <RoomAudioRenderer />
                
                <VoiceAssistantUI onClose={onClose} />
              </LiveKitRoom>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default VoiceAgentModal;
