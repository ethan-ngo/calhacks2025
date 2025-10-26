import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
    heartRate: '71/min',
    temperature: '37.5 Cel',
    respiratoryRate: '13/min',
    bloodPressure: '120/80',
    painSeverity: '5',
    comments: ''
  })

  const [chatMessages] = useState([
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
      const response = await fetch('http://127.0.0.1:8000/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      
      if (result.success) {
        // Navigate to dashboard with triage result
        navigate('/triage-dashboard', {
          state: {
            triageResult: result,
            patientData: patientData
          }
        })
      } else {
        alert('Triage failed: ' + (result.error || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to submit: ' + error.message)
    } finally {
      setIsSubmitting(false)
    }
  }

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

      <div style={styles.rightPanel}>
        <ChatInterface chatMessages={chatMessages} />
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
    transition: 'all 0.2s ease',
  },
  submitButtonLoading: {
    backgroundColor: '#7ab8ff',
    cursor: 'not-allowed',
    opacity: 0.7,
  },
}