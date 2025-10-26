import { useState, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

// Backend API endpoint
const API_ENDPOINT = 'http://127.0.0.1:5000/patient/chat'

export default function PatientChat() {
  const navigate = useNavigate()
  const { patientId } = useParams() // Get patientId from URL
  const [messages, setMessages] = useState([
    { id: 1, sender: 'assistant', text: 'Hello! How can I help you today? Please describe your symptoms.', timestamp: new Date() },
  ])
  const [inputText, setInputText] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    // Validate input
    const message = inputText.trim()
    if (!message || isLoading) return
    
    const userMessage = {
      id: messages.length + 1,
      sender: 'user',
      text: message,
      timestamp: new Date()
    }
    
    // Add user message immediately
    setMessages(prev => [...prev, userMessage])
    setInputText('')
    setIsLoading(true)
    
    try {
      console.log('📤 Sending to backend:', message)
      
      // POST request to Flask backend
      const response = await fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message,
          patientId: patientId || 'default_patient'
        })
      })
      
      const data = await response.json()
      console.log('📥 Received:', data)
      
      // Handle successful response
      if (data.success) {
        const assistantMessage = {
          id: messages.length + 2,
          sender: 'assistant',
          text: data.response,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, assistantMessage])
      } else {
        const errorMessage = {
          id: messages.length + 2,
          sender: 'assistant',
          text: data.response || 'Unable to process request.',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, errorMessage])
      }
      
    } catch (error) {
      console.error('❌ Error:', error)
      
      const errorMessage = {
        id: messages.length + 2,
        sender: 'assistant',
        text: 'Connection error. Please check if the backend is running.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={styles.container}>
      {/* Back Button */}
      <button onClick={() => navigate(patientId ? `/patientwait/${patientId}` : '/patientwait')} style={styles.backButton}>
        ← Back
      </button>
      
      {/* Title */}
      <div style={styles.titleContainer}>
        <h1 style={styles.title}>Have your symptoms changed?</h1>
      </div>

      {/* Messages Area */}
      <div style={styles.chatCard}>
        <div style={styles.messagesContainer}>
          {messages.map((message) => (
            <div 
              key={message.id} 
              style={{
                ...styles.messageWrapper,
                flexDirection: message.sender === 'user' ? 'row-reverse' : 'row'
              }}
            >
              <div style={styles.avatar}>
                <div style={styles.avatarIcon}>👤</div>
              </div>
              <div 
                style={{
                  ...styles.messageBubble,
                  ...(message.sender === 'user' ? styles.userBubble : styles.assistantBubble)
                }}
              >
                <div style={styles.messageText}>{message.text}</div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={styles.inputContainer}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isLoading ? "Sending..." : "I'm feeling..."}
            style={styles.input}
            disabled={isLoading}
          />
          <button 
            onClick={handleSend} 
            style={{
              ...styles.sendButton,
              opacity: isLoading ? 0.6 : 1,
              cursor: isLoading ? 'not-allowed' : 'pointer'
            }}
            disabled={isLoading}
          >
            {isLoading ? '...' : '→'}
          </button>
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    width: '100vw',
    backgroundColor: '#e8eef3',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    padding: '20px 20px 40px 20px',
    boxSizing: 'border-box',
  },
  backButton: {
    backgroundColor: 'transparent',
    color: '#3b9dff',
    border: 'none',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    padding: '8px',
    marginBottom: '30px',
    display: 'inline-flex',
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  titleContainer: {
    textAlign: 'center',
    marginBottom: '40px',
  },
  title: {
    fontSize: 'clamp(28px, 6vw, 42px)',
    fontWeight: '600',
    color: '#1f2937',
    margin: 0,
    lineHeight: 1.3,
  },
  chatCard: {
    backgroundColor: '#fff',
    borderRadius: '32px',
    boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    maxWidth: '700px',
    width: '100%',
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    minHeight: '600px',
    maxHeight: '70vh',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '32px 24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  messageWrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  avatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: '#e5e7eb',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  avatarIcon: {
    fontSize: '20px',
    opacity: 0.5,
  },
  messageBubble: {
    padding: '14px 20px',
    borderRadius: '20px',
    maxWidth: 'calc(100% - 52px)',
    wordWrap: 'break-word',
  },
  userBubble: {
    backgroundColor: '#0b7dff',
    color: '#fff',
    borderTopRightRadius: '20px',
    borderBottomRightRadius: '4px',
  },
  assistantBubble: {
    backgroundColor: '#f3f4f6',
    color: '#1f2937',
    borderTopLeftRadius: '20px',
    borderBottomLeftRadius: '4px',
  },
  messageText: {
    fontSize: '16px',
    lineHeight: '1.5',
    whiteSpace: 'pre-wrap',
  },
  inputContainer: {
    padding: '24px',
    borderTop: '1px solid #f3f4f6',
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    border: '1px solid #e5e7eb',
    borderRadius: '30px',
    padding: '14px 24px',
    fontSize: '16px',
    fontFamily: 'inherit',
    outline: 'none',
    backgroundColor: '#f9fafb',
    transition: 'all 0.2s ease',
  },
  sendButton: {
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: '#0b7dff',
    color: '#fff',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
    flexShrink: 0,
    fontWeight: '300',
  },
}

