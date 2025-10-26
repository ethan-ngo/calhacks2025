export default function ChatInterface({ chatMessages, onMicrophoneClick, isVoiceActive, isConnecting }) {
  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Voice Assistant</h2>
      
      <div style={styles.messagesContainer}>
        {chatMessages.map((msg, idx) => (
          <div 
            key={idx} 
            style={{
              ...styles.message,
              alignSelf: msg.sender === 'patient' || msg.sender === 'system' ? 'flex-start' : 'flex-end',
              backgroundColor: msg.sender === 'agent' ? '#3b9dff' : msg.sender === 'system' ? '#ffa500' : '#e8eef3',
              color: msg.sender === 'agent' || msg.sender === 'system' ? '#fff' : '#333',
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div style={styles.controls}>
        <button 
          onClick={onMicrophoneClick}
          disabled={isConnecting}
          style={{
            ...styles.micButton,
            backgroundColor: isVoiceActive ? '#ff4444' : isConnecting ? '#999' : '#3b9dff',
            cursor: isConnecting ? 'not-allowed' : 'pointer',
          }}
        >
          {isConnecting ? '⏳ Connecting...' : isVoiceActive ? '🎤 Stop Recording' : '🎤 Start Voice Agent'}
        </button>
        
        {isVoiceActive && (
          <div style={styles.recordingIndicator}>
            <span style={styles.pulse}>●</span> Recording...
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  },
  title: {
    fontSize: '28px',
    fontWeight: '500',
    color: '#5a5a5a',
    marginBottom: '20px',
    marginTop: 0,
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    marginBottom: '20px',
    padding: '10px',
  },
  message: {
    padding: '12px 16px',
    borderRadius: '12px',
    maxWidth: '80%',
    fontSize: '15px',
    lineHeight: '1.5',
  },
  controls: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    alignItems: 'center',
  },
  micButton: {
    padding: '16px 32px',
    fontSize: '16px',
    fontWeight: '500',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    transition: 'all 0.2s ease',
    width: '100%',
  },
  recordingIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    color: '#ff4444',
    fontSize: '14px',
    fontWeight: '500',
  },
  pulse: {
    animation: 'pulse 1.5s ease-in-out infinite',
    fontSize: '20px',
  },
}