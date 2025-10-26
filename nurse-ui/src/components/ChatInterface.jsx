import { useState } from 'react'

export default function ChatInterface({ chatMessages }) {
  const [isRecording, setIsRecording] = useState(false)

  return (
    <div style={styles.chatContainer}>
      <div style={styles.chatMessages}>
        {chatMessages.map((msg, idx) => (
          <div 
            key={idx} 
            style={{
              ...styles.message,
              ...(msg.sender === 'nurse' ? styles.nurseMessage : styles.patientMessage)
            }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div style={styles.audioVisualization}>
        {[...Array(7)].map((_, i) => (
          <div 
            key={i} 
            style={{
              ...styles.audioBar,
              height: `${30 + Math.random() * 40}px`
            }}
          />
        ))}
      </div>

      <button 
        onClick={() => setIsRecording(!isRecording)}
        style={{
          ...styles.micButton,
          ...(isRecording ? styles.micButtonActive : {})
        }}
      >
        🎤
      </button>
    </div>
  )
}

const styles = {
  chatContainer: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    justifyContent: 'space-between',
  },
  chatMessages: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    marginBottom: '40px',
  },
  message: {
    padding: '20px 24px',
    borderRadius: '16px',
    fontSize: '18px',
    lineHeight: '1.5',
  },
  nurseMessage: {
    backgroundColor: '#f0f0f0',
    color: '#ccc',
    alignSelf: 'flex-start',
  },
  patientMessage: {
    backgroundColor: '#f0f0f0',
    color: '#333',
    alignSelf: 'flex-start',
  },
  audioVisualization: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '40px',
    height: '80px',
  },
  audioBar: {
    width: '8px',
    backgroundColor: '#ccc',
    borderRadius: '4px',
    transition: 'height 0.2s ease',
  },
  micButton: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    backgroundColor: '#3b9dff',
    border: 'none',
    fontSize: '32px',
    cursor: 'pointer',
    alignSelf: 'center',
    boxShadow: '0 4px 12px rgba(59, 157, 255, 0.3)',
    transition: 'transform 0.2s ease',
  },
  micButtonActive: {
    backgroundColor: '#ff3b3b',
    transform: 'scale(1.1)',
  },
}

