import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Room, RoomEvent } from 'livekit-client'
import PatientInfoCard from '../components/PatientInfoCard'
import PainSeverityCard from '../components/PainSeverityCard'
import KeyVitalsCard from '../components/KeyVitalsCard'
import CommentsCard from '../components/CommentsCard'
import ChatInterface from '../components/ChatInterface'

const LIVEKIT_URL = 'wss://triageagent-2aap4wyl.livekit.cloud'

export default function NurseForm() {
  const navigate = useNavigate()
  const [patientData, setPatientData] = useState({
    name: 'John Doe',
    age: '21',
    gender: 'Male',
    weight: '70kgs',
    heartRate: '71/min',
    temperature: '37.5 Cel',
    respiratoryRate: '13/min',
    bloodPressure: '120/80',
    painSeverity: '5',
    comments: ''
  })

  const [chatMessages, setChatMessages] = useState([
    { sender: 'patient', text: 'Hi I am your transcription voice assistant.' }
  ])

  // Voice agent states
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const roomRef = useRef(null)

  const handleInputChange = (e) => {
    setPatientData({
      ...patientData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async () => {
    const payload = {
      userID: patientData.name,
      current_vitals: [
        `HR: ${patientData.heartRate}`,
        `Temp: ${patientData.temperature}`,
        `RR: ${patientData.respiratoryRate}`,
        `BP: ${patientData.bloodPressure}`
      ],
      current_symptoms: [chatMessages[chatMessages.length - 1].text]
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/nurse/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const result = await response.json()
      
      setPatientData({
        ...patientData,
        comments: result.reasoning || 'Assessment complete'
      })
      
      alert(`Triage Score: ${result.triage_score}/5`)
    } catch (error) {
      alert('Failed to submit: ' + error.message)
    }
  }

  const toggleVoiceAgent = async () => {
    if (isVoiceActive) {
      // Disconnect
      if (roomRef.current) {
        roomRef.current.disconnect()
        roomRef.current = null
      }
      setIsVoiceActive(false)
      setChatMessages(prev => [...prev, { 
        sender: 'system', 
        text: 'Voice agent disconnected' 
      }])
    } else {
      // Connect
      setIsConnecting(true)
      try {
        // Get token from Flask backend
        const tokenRes = await fetch('http://127.0.0.1:5000/getToken', { 
          method: 'POST' 
        })
        const token = await tokenRes.text()

        // Create room and connect
        const room = new Room({
          adaptiveStream: true,
          dynacast: true,
        })

        // Set up event listeners
        room.on(RoomEvent.Connected, () => {
          console.log('Connected to room')
          setIsVoiceActive(true)
          setIsConnecting(false)
          setChatMessages(prev => [...prev, { 
            sender: 'system', 
            text: 'Voice agent connected - Start speaking' 
          }])
        })

        room.on(RoomEvent.Disconnected, () => {
          console.log('Disconnected from room')
          setIsVoiceActive(false)
        })

        // Listen for transcriptions from the agent
        room.on(RoomEvent.TranscriptionReceived, (transcription) => {
          if (transcription.participant && transcription.participant.identity !== room.localParticipant.identity) {
            // This is from the agent
            setChatMessages(prev => [...prev, { 
              sender: 'agent', 
              text: transcription.text 
            }])
          }
        })

        // Listen for data messages (structured output from agent)
        room.on(RoomEvent.DataReceived, (payload, participant) => {
          try {
            const data = JSON.parse(new TextDecoder().decode(payload))
            console.log('Received data from agent:', data)
            
            // Update patient data if agent sends structured info
            if (data.name) setPatientData(prev => ({ ...prev, name: data.name }))
            if (data.age) setPatientData(prev => ({ ...prev, age: data.age.toString() }))
            if (data.gender) setPatientData(prev => ({ ...prev, gender: data.gender }))
            if (data.weight) setPatientData(prev => ({ ...prev, weight: `${data.weight}kgs` }))
            if (data.heart_rate) setPatientData(prev => ({ ...prev, heartRate: `${data.heart_rate}/min` }))
            if (data.temperature) setPatientData(prev => ({ ...prev, temperature: `${data.temperature} Cel` }))
            if (data.respiratory_rate) setPatientData(prev => ({ ...prev, respiratoryRate: `${data.respiratory_rate}/min` }))
            if (data.suggested_triage_level) setPatientData(prev => ({ ...prev, painSeverity: data.suggested_triage_level.toString() }))
            if (data.patient_notes) setPatientData(prev => ({ ...prev, comments: data.patient_notes }))
          } catch (e) {
            console.error('Failed to parse agent data:', e)
          }
        })

        // Connect to room
        await room.connect(LIVEKIT_URL, token)
        
        // Enable microphone
        await room.localParticipant.setMicrophoneEnabled(true)

        roomRef.current = room

      } catch (error) {
        console.error('Failed to connect to voice agent:', error)
        setIsConnecting(false)
        setChatMessages(prev => [...prev, { 
          sender: 'system', 
          text: 'Failed to connect to voice agent: ' + error.message 
        }])
      }
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect()
      }
    }
  }, [])

  return (
    <div style={styles.container}>
      <div style={styles.leftPanel}>
        <h1 style={styles.title}>Triage Patient Report</h1>
        
        <div style={styles.topRow}>
          <PatientInfoCard 
            patientData={patientData} 
            handleInputChange={handleInputChange} 
          />
          <PainSeverityCard 
            painSeverity={patientData.painSeverity}
            handleInputChange={handleInputChange}
          />
        </div>

        <KeyVitalsCard 
          patientData={patientData}
          handleInputChange={handleInputChange}
        />

        <CommentsCard 
          comments={patientData.comments}
          handleInputChange={handleInputChange}
        />

        <div style={styles.buttonContainer}>
          <button onClick={() => navigate('/')} style={styles.backButton}>
            ← Back
          </button>
          <button onClick={handleSubmit} style={styles.submitButton}>
            Submit
          </button>
        </div>
      </div>

      <div style={styles.rightPanel}>
        <ChatInterface 
          chatMessages={chatMessages}
          onMicrophoneClick={toggleVoiceAgent}
          isVoiceActive={isVoiceActive}
          isConnecting={isConnecting}
        />
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    width: '100vw',
    height: '100vh',
    margin: 0,
    padding: 0,
    backgroundColor: '#e8eef3',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    overflow: 'hidden',
  },
  leftPanel: {
    width: '50%',
    padding: '40px',
    overflowY: 'auto',
    boxSizing: 'border-box',
  },
  rightPanel: {
    width: '50%',
    backgroundColor: '#fff',
    padding: '40px',
    display: 'flex',
    flexDirection: 'column',
    boxSizing: 'border-box',
    overflowY: 'auto',
  },
  title: {
    fontSize: '42px',
    fontWeight: '500',
    color: '#5a5a5a',
    marginBottom: '30px',
    marginTop: 0,
  },
  topRow: {
    display: 'flex',
    gap: '20px',
    marginBottom: '20px',
    alignItems: 'right',
  },
  buttonContainer: {
    display: 'flex',
    justifyContent: 'space-between',
    marginTop: '20px',
  },
  backButton: {
    backgroundColor: 'transparent',
    color: '#3b9dff',
    border: '2px solid #3b9dff',
    borderRadius: '12px',
    padding: '16px 48px',
    fontSize: '18px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  submitButton: {
    backgroundColor: '#3b9dff',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    padding: '16px 48px',
    fontSize: '18px',
    fontWeight: '500',
    cursor: 'pointer',
  },
}