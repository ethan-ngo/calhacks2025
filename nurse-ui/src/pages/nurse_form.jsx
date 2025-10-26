import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PatientInfoCard from '../components/PatientInfoCard'
import PainSeverityCard from '../components/PainSeverityCard'
import KeyVitalsCard from '../components/KeyVitalsCard'
import CommentsCard from '../components/CommentsCard'
import ChatInterface from '../components/ChatInterface'

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

  const [chatMessages] = useState([
    { sender: 'patient', text: 'Hi I am your transcription voice assistant.' }
  ])

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
  },
}
