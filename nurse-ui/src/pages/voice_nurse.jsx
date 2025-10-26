import React, { useEffect, useState } from 'react';
import { LiveKitRoom, VideoConference, useRoomContext, useParticipants } from '@livekit/components-react';
import '@livekit/components-styles';

const serverUrl = 'https://triageagent-2aap4wyl.livekit.cloud';

export default function App() {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const getToken = async () => {
      try {
        const res = await fetch('http://127.0.0.1:5000/getToken', { method: 'POST' });
        if (!res.ok) throw new Error('Failed to get token');
        const token = await res.text();
        setToken(token);
      } catch (err) {
        console.error('Failed to get token:', err);
        setError('Could not connect to server. Make sure Flask is running on port 5000.');
      }
    };
    getToken();
  }, []);

  if (error) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: '#1a1a1a',
        color: '#ff4444',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div>
          <h2>Connection Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        backgroundColor: '#1a1a1a',
        color: '#fff',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '50px',
            height: '50px',
            border: '4px solid #333',
            borderTop: '4px solid #0066ff',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }} />
          <p>Connecting to room...</p>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    );
  }

  return (
    <div style={{ height: '100vh', backgroundColor: '#1a1a1a' }}>
      <LiveKitRoom
        video={true}
        audio={true}
        token={token}
        serverUrl={serverUrl}
        data-lk-theme="default"
        style={{ height: '100%' }}
        onConnected={() => console.log('✅ Connected to room: my-room')}
        onDisconnected={() => console.log('❌ Disconnected from room')}
      >
        <TriageInterface />
      </LiveKitRoom>
    </div>
  );
}

function TriageInterface() {
  const participants = useParticipants();
  const room = useRoomContext();

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{
        padding: '20px',
        backgroundColor: '#2a2a2a',
        borderBottom: '1px solid #333',
        color: '#fff',
        fontFamily: 'system-ui, -apple-system, sans-serif'
      }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>
          🏥 Emergency Triage System
        </h1>
        <p style={{ margin: '8px 0 0', fontSize: '14px', color: '#999' }}>
          Connected participants: {participants.length}
          {participants.length > 1 && ' (Agent Apollo is listening)'}
        </p>
      </div>

      {/* Main Video Area */}
      <div style={{ flex: 1, position: 'relative' }}>
        <VideoConference />
      </div>

      {/* Instructions */}
      {participants.length === 1 && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: '30px',
          borderRadius: '12px',
          color: '#fff',
          textAlign: 'center',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          maxWidth: '500px',
          zIndex: 10
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
          <h2 style={{ margin: '0 0 10px', fontSize: '20px' }}>Waiting for Agent Apollo</h2>
          <p style={{ margin: 0, color: '#aaa', fontSize: '14px' }}>
            Make sure the agent is running with:<br/>
            <code style={{ 
              backgroundColor: '#1a1a1a', 
              padding: '4px 8px', 
              borderRadius: '4px',
              display: 'inline-block',
              marginTop: '10px'
            }}>
              python nurse_agent.py connect --room my-room
            </code>
          </p>
        </div>
      )}

      {participants.length > 1 && (
        <div style={{
          position: 'absolute',
          bottom: '80px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(0, 150, 0, 0.9)',
          padding: '12px 24px',
          borderRadius: '8px',
          color: '#fff',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
          fontSize: '14px',
          fontWeight: 500,
          zIndex: 10,
          animation: 'fadeIn 0.5s'
        }}>
          ✅ Agent Apollo connected - Start speaking to begin triage assessment
          <style>{`
            @keyframes fadeIn {
              from { opacity: 0; transform: translateX(-50%) translateY(10px); }
              to { opacity: 1; transform: translateX(-50%) translateY(0); }
            }
          `}</style>
        </div>
      )}
    </div>
  );
}