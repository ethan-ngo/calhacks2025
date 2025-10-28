import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { API_BASE_URL } from '../config'
import PatientInfoCard from '../components/PatientInfoCard'
import PainSeverityCard from '../components/PainSeverityCard'
import KeyVitalsCard from '../components/KeyVitalsCard'
import CommentsCard from '../components/CommentsCard'
import ChatInterface from '../components/ChatInterface'

export default function NurseForm() {
  const navigate = useNavigate()
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const [patientData, setPatientData] = useState({
    name: 'John Doe',
    age: '21',
    gender: 'Male',
    weight: '70kgs',
    phoneNumber: '',
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

  const patients = {
    "Allen Stoltenberg": "073290f9-73e6-8842-bddc-b568bfcb84b0",
    "Carline Gibson": "40021a9e-eeb3-4fd0-1d5a-2cd56a0bff73",
    "Gregorio Batz": "12bee8ac-7bce-f218-179e-0c2cabade79f",
    "Selena Turner": "1c026fd4-568f-5bc5-32f3-eb801c69ebd2",
    "Kori Hermann": "e369df4d-e272-e40a-8bf0-964b9bbe949c",
    "Andra Cruickshank": "fcc2ce58-4808-f223-9902-107143303d1a",
    "Enrique Konopelski": "8f76e2d9-92a3-0a2a-72a6-a042566a4cb0",
    "Fonda Hettinger": "e431384f-3578-ab67-d439-e5f55ff22a0d",
    "Phyliss Marks": "e36a2f5b-a5ac-db0b-bfdf-5c130dad1161",
    "Terri Wolff": "f9df9434-2057-1a21-bee6-791ed3f9d97b"
  }


  // Voice recognition states
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const recognitionRef = useRef(null)
  const transcriptionBuffer = useRef('')
  const processTimeoutRef = useRef(null)

  const handleInputChange = (e) => {
    setPatientData({
      ...patientData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    
    const heartRate = parseInt(patientData.heartRate.split('/')[0])
    const temperature = parseFloat(patientData.temperature.split(' ')[0])
    const respiratoryRate = parseInt(patientData.respiratoryRate.split('/')[0])
    const bloodPressure = patientData.bloodPressure
    
    
    //breaks the output with JSON Parse Error at line 1, column 1 Error: Expecting value
    //const symptoms = chatMessages[chatMessages.length - 1]?.text || patientData.comments || 'No symptoms reported'
    // Combine all chat messages and the comments, fixes all the issues with the previous line that was commented out
    const chatLog = chatMessages.map(m => m.text).join(' \n');
    const symptoms = `Chat Transcript: \n${chatLog} \n\nNurse Comments: \n${patientData.comments}`;
    const patientID = patients[patientData.name] || patientData.name

    const payload = {
      userID: patientID,
      current_vitals: {
        heart_rate: heartRate,
        temperature: temperature,
        respiratory_rate: respiratoryRate,
        blood_pressure: bloodPressure
      },
      current_symptoms: symptoms,
      history: "",
      recall_history: ""
    }

    try {
      // Use Flask backend endpoint instead of calling agent directly
      const response = await fetch(`${API_BASE_URL}/nurse/triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      // Check if we got a triage_score
      if (result.triage_score) {
        console.log('✅ Triage result:', result)
        
        // Save patient data and send link via SMS
        const submitResponse = await fetch(`${API_BASE_URL}/nurse/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: patientData.name,
            age: patientData.age,
            gender: patientData.gender,
            weight: patientData.weight,
            phoneNumber: patientData.phoneNumber,
            heartRate: patientData.heartRate,
            temperature: patientData.temperature,
            respiratoryRate: patientData.respiratoryRate,
            bloodPressure: patientData.bloodPressure,
            painSeverity: patientData.painSeverity,
            symptoms: symptoms,
            triageScore: result.triage_score
          })
        })
        
        const submitData = await submitResponse.json()
        console.log('✅ Patient submitted:', submitData.success)
        
        if (submitData.success) {
          // Show simple confirmation without revealing patient info
          alert(
            `✅ Patient Successfully Registered\n\n` +
            `${submitData.sms_sent ? '📱 Portal link sent to patient\'s phone' : '⚠️ Unable to send SMS - please notify patient manually'}`
          )
          
          // Use the full assessment from result
          const triageResultForDashboard = result.assessment || {
            triage_score: result.triage_score,
            triage_level: result.triage_level,
            acuity: result.acuity,
            assessment_summary: {
              primary_concern: result.reasoning
            },
            clinical_recommendations: [],
            nursing_notes: []
          }
          
          // Navigate to dashboard with patient link
          navigate('/triage-dashboard', {
            state: {
              triageResult: triageResultForDashboard,
              patientData: patientData,
              patientLink: submitData.patient_link,
              patientId: submitData.patient_id
            }
          })
        } else {
          alert('Failed to register patient: ' + (submitData.error || 'Unknown error'))
        }
      } else {
        alert('Triage failed: ' + (result.error || 'No triage score returned'))
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to submit: ' + error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Process transcription with AI to extract structured data
  const processTranscription = async (text) => {
    if (!text || text.trim().length === 0) return
    
    setIsProcessing(true)
    console.log('🤖 Processing transcription with AI:', text)
    
    try {
      const response = await fetch(`${API_BASE_URL}/voice/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcription: text })
      })
      
      if (!response.ok) {
        throw new Error(`Failed to process transcription: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('✅ Received structured data from AI:', data)
      
      // Update form fields with extracted data
      if (data.name) setPatientData(prev => ({ ...prev, name: data.name }))
      if (data.age) setPatientData(prev => ({ ...prev, age: data.age.toString() }))
      if (data.gender) setPatientData(prev => ({ ...prev, gender: data.gender }))
      if (data.weight) setPatientData(prev => ({ ...prev, weight: `${data.weight}kgs` }))
      if (data.heart_rate) setPatientData(prev => ({ ...prev, heartRate: `${data.heart_rate}/min` }))
      if (data.temperature) setPatientData(prev => ({ ...prev, temperature: `${data.temperature} Cel` }))
      if (data.respiratory_rate) setPatientData(prev => ({ ...prev, respiratoryRate: `${data.respiratory_rate}/min` }))
      if (data.suggested_triage_level) setPatientData(prev => ({ ...prev, painSeverity: data.suggested_triage_level.toString() }))
      if (data.patient_notes) setPatientData(prev => ({ ...prev, comments: data.patient_notes }))
      
      setChatMessages(prev => [...prev, {
        sender: 'system',
        text: '✅ Form automatically filled with your information'
      }])
      
    } catch (error) {
      console.error('❌ Error processing transcription:', error)
      setChatMessages(prev => [...prev, {
        sender: 'system',
        text: '⚠️ Failed to process voice input. Please try again.'
      }])
    } finally {
      setIsProcessing(false)
    }
  }

  const toggleVoiceAgent = async () => {
    if (isVoiceActive) {
      // Stop voice recognition
      if (recognitionRef.current) {
        recognitionRef.current.stop()
        recognitionRef.current = null
      }
      
      if (processTimeoutRef.current) {
        clearTimeout(processTimeoutRef.current)
      }
      
      // Process any remaining transcription
      if (transcriptionBuffer.current.trim().length > 0) {
        await processTranscription(transcriptionBuffer.current)
        transcriptionBuffer.current = ''
      }
      
      setIsVoiceActive(false)
      setChatMessages(prev => [...prev, {
        sender: 'system',
        text: '🛑 Voice recognition stopped'
      }])
    } else {
      // Start voice recognition
      try {
        // Check if browser supports Web Speech API
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
        
        if (!SpeechRecognition) {
          alert('Voice recognition is not supported in your browser. Please use Chrome, Safari, or Edge.')
          return
        }
        
        const recognition = new SpeechRecognition()
        recognition.continuous = true
        recognition.interimResults = true
        recognition.lang = 'en-US'
        
        recognition.onstart = () => {
          console.log('🎤 Voice recognition started')
          setIsVoiceActive(true)
          transcriptionBuffer.current = ''
          setChatMessages(prev => [...prev, {
            sender: 'system',
            text: '🎤 Voice recognition active - Start speaking about your symptoms'
          }])
        }
        
        recognition.onresult = (event) => {
          let interimTranscript = ''
          let finalTranscript = ''
          
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript
            if (event.results[i].isFinal) {
              finalTranscript += transcript + ' '
            } else {
              interimTranscript += transcript
            }
          }
          
          if (finalTranscript) {
            console.log('📝 Final transcript:', finalTranscript)
            transcriptionBuffer.current += finalTranscript
            
            setChatMessages(prev => [...prev, {
              sender: 'user',
              text: finalTranscript.trim()
            }])
            
            // Clear existing timeout
            if (processTimeoutRef.current) {
              clearTimeout(processTimeoutRef.current)
            }
            
            // Process transcription after 2 seconds of silence
            processTimeoutRef.current = setTimeout(() => {
              if (transcriptionBuffer.current.trim().length > 0) {
                processTranscription(transcriptionBuffer.current)
                transcriptionBuffer.current = ''
              }
            }, 2000)
          }
        }
        
        recognition.onerror = (event) => {
          console.error('❌ Speech recognition error:', event.error)
          
          let errorMessage = 'Voice recognition error'
          if (event.error === 'not-allowed') {
            errorMessage = 'Microphone access denied. Please allow microphone access in your browser settings.'
          } else if (event.error === 'no-speech') {
            errorMessage = 'No speech detected. Please try speaking again.'
          } else if (event.error === 'network') {
            errorMessage = 'Network error. Please check your connection.'
          }
          
          setChatMessages(prev => [...prev, {
            sender: 'system',
            text: `⚠️ ${errorMessage}`
          }])
          
          setIsVoiceActive(false)
        }
        
        recognition.onend = () => {
          console.log('🛑 Voice recognition ended')
          if (isVoiceActive) {
            // Restart if it ended unexpectedly
            try {
              recognition.start()
            } catch (e) {
              console.log('Recognition already started or stopped by user')
            }
          }
        }
        
        recognitionRef.current = recognition
        recognition.start()
        
      } catch (error) {
        console.error('Failed to start voice recognition:', error)
        alert('Failed to start voice recognition: ' + error.message)
      }
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
      if (processTimeoutRef.current) {
        clearTimeout(processTimeoutRef.current)
      }
    }
  }, [])

  return (
    <div style={styles.container}>
      <div style={styles.header}>
          <h1 style={styles.headerTitle}>Triage Patient Report</h1>
        <div style={styles.headerButtons}>
          <button onClick={() => navigate('/')} style={styles.backButton}>
            ← Back
          </button>
          <button 
            onClick={handleSubmit} 
            style={{
              ...styles.submitButton,
              ...(isSubmitting ? styles.submitButtonLoading : {})
            }}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Calculating...' : 'Submit'}
          </button>
        </div>
      </div>

      <div style={styles.contentWrapper}>
        <div style={styles.leftPanel}>
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
        </div>

        <div style={styles.rightPanel}>
          <ChatInterface 
            chatMessages={chatMessages}
            toggleVoiceAgent={toggleVoiceAgent}
            isVoiceActive={isVoiceActive}
            isProcessing={isProcessing}
          />
        </div>
      </div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    width: '100vw',
    height: '100vh',
    margin: 0,
    padding: 0,
    background: 'linear-gradient(180deg,rgba(240, 240, 240, 1) 0%, rgba(161, 208, 255, 1) 100%)',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 40px',
    backgroundColor: '#fff',
    borderBottom: '1px solid #e0e0e0',
    flexShrink: 0,
  },
  headerTitle: {
    fontSize: '28px',
    fontWeight: '500',
    color: '#5a5a5a',
    margin: 0,
  },
  headerButtons: {
    display: 'flex',
    gap: '12px',
  },
  contentWrapper: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  },
  leftPanel: {
    width: '50%',
    padding: '24px',
    overflowY: 'auto',
    boxSizing: 'border-box',
  },
  rightPanel: {
    width: '50%',
    backgroundColor: '#fff',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    boxSizing: 'border-box',
    overflow: 'hidden',
  },
  topRow: {
    display: 'flex',
    gap: '16px',
    marginBottom: '16px',
    alignItems: 'right',
  },
  backButton: {
    backgroundColor: 'transparent',
    color: '#3b9dff',
    border: '2px solid #3b9dff',
    borderRadius: '8px',
    padding: '10px 32px',
    fontSize: '16px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  submitButton: {
    backgroundColor: '#3b9dff',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '10px 32px',
    fontSize: '16px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  submitButtonLoading: {
    backgroundColor: '#7ab8ff',
    cursor: 'not-allowed',
    opacity: 0.7,
  },
}