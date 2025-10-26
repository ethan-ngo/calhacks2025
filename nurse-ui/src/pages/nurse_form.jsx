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
  const [triageResult, setTriageResult] = useState(null)
  const [isOverriding, setIsOverriding] = useState(false)
  const [overrideScore, setOverrideScore] = useState(null)
  const [finalDecision, setFinalDecision] = useState(null)
  
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
        setTriageResult(result)
        setOverrideScore(null)
        setIsOverriding(false)
        setFinalDecision(null)
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

  const handleAccept = () => {
    setFinalDecision({
      score: triageResult.triage_score,
      level: triageResult.triage_level,
      wasOverridden: false
    })
    alert(`ESI Level ${triageResult.triage_score} Accepted`)
  }

  const handleOverride = () => {
    if (!overrideScore) {
      alert('Please select an ESI level to override to')
      return
    }
    
    const levels = {
      1: 'RESUSCITATION',
      2: 'EMERGENT', 
      3: 'URGENT',
      4: 'LESS URGENT',
      5: 'NON-URGENT'
    }
    
    setFinalDecision({
      score: overrideScore,
      level: levels[overrideScore],
      wasOverridden: true,
      originalScore: triageResult.triage_score
    })
    alert(`ESI Level overridden from ${triageResult.triage_score} to ${overrideScore}`)
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

        {triageResult && !finalDecision && (
          <div style={styles.dashboardCard}>
            <h2 style={styles.dashboardTitle}>🏥 Triage Assessment Dashboard</h2>
            
            {/* ESI Score Display */}
            <div style={styles.esiSection}>
              <div style={styles.esiScoreDisplay}>
                <div style={styles.esiLabel}>Recommended ESI Level</div>
                <div style={styles.esiScore}>{triageResult.triage_score}</div>
                <div style={styles.esiLevel}>{triageResult.triage_level}</div>
                <div style={styles.acuity}>Acuity: {triageResult.acuity}</div>
              </div>
            </div>

            {/* Accept/Override Buttons */}
            <div style={styles.decisionSection}>
              <button 
                onClick={handleAccept}
                style={styles.acceptButton}
              >
                ✓ Accept Recommendation
              </button>
              <button 
                onClick={() => setIsOverriding(!isOverriding)}
                style={{
                  ...styles.overrideButton,
                  ...(isOverriding ? styles.overrideButtonActive : {})
                }}
              >
                ⚠ Override Score
              </button>
            </div>

            {/* Override Selection */}
            {isOverriding && (
              <div style={styles.overridePanel}>
                <div style={styles.overrideTitle}>Select New ESI Level:</div>
                <div style={styles.esiButtons}>
                  {[1, 2, 3, 4, 5].map(score => (
                    <button
                      key={score}
                      onClick={() => setOverrideScore(score)}
                      style={{
                        ...styles.esiButton,
                        ...(overrideScore === score ? styles.esiButtonActive : {}),
                        ...(score === triageResult.triage_score ? styles.esiButtonDisabled : {})
                      }}
                      disabled={score === triageResult.triage_score}
                    >
                      {score}
                    </button>
                  ))}
                </div>
                {overrideScore && (
                  <button
                    onClick={handleOverride}
                    style={styles.confirmOverrideButton}
                  >
                    Confirm Override to Level {overrideScore}
                  </button>
                )}
              </div>
            )}

            {/* Primary Concern */}
            <div style={styles.section}>
              <div style={styles.sectionTitle}>📋 Primary Concern</div>
              <div style={styles.sectionContent}>
                {triageResult.assessment_summary?.primary_concern}
              </div>
              <div style={styles.urgencyBadge}>
                {triageResult.assessment_summary?.immediate_action_required ? (
                  <span style={styles.urgentBadge}>⚠️ IMMEDIATE ACTION REQUIRED</span>
                ) : (
                  <span style={styles.stableBadge}>✅ Can Wait</span>
                )}
                <span style={styles.waitTime}>
                  Est. Wait: {triageResult.assessment_summary?.estimated_wait_time}
                </span>
              </div>
            </div>

            {/* Clinical Findings */}
            <div style={styles.section}>
              <div style={styles.sectionTitle}>🩺 Clinical Findings</div>
              <div style={styles.subsection}>
                <strong>Symptoms:</strong>
                <ul style={styles.list}>
                  {triageResult.clinical_findings?.presenting_symptoms?.map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
              {triageResult.clinical_findings?.red_flags?.length > 0 && (
                <div style={styles.redFlagsBox}>
                  <strong>🚨 Red Flags:</strong>
                  <ul style={styles.list}>
                    {triageResult.clinical_findings.red_flags.map((flag, i) => (
                      <li key={i}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Recommendations */}
            <div style={styles.section}>
              <div style={styles.sectionTitle}>💊 Recommendations</div>
              <div style={styles.subsection}>
                <strong>Resources Needed:</strong>
                <ul style={styles.list}>
                  {triageResult.recommended_resources?.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
              <div style={styles.subsection}>
                <strong>Clinical Actions:</strong>
                <ul style={styles.list}>
                  {triageResult.clinical_recommendations?.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Nursing Notes */}
            <div style={styles.section}>
              <div style={styles.sectionTitle}>📝 Nursing Notes</div>
              <ul style={styles.list}>
                {triageResult.nursing_notes?.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Final Decision Display */}
        {finalDecision && (
          <div style={styles.finalDecisionCard}>
            <h2 style={styles.finalDecisionTitle}>
              ✅ Final ESI Level: {finalDecision.score}
            </h2>
            <div style={styles.finalDecisionContent}>
              <div>Level: {finalDecision.level}</div>
              {finalDecision.wasOverridden && (
                <div style={styles.overrideNotice}>
                  ⚠️ Overridden from Level {finalDecision.originalScore}
                </div>
              )}
            </div>
          </div>
        )}

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
  dashboardCard: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '24px',
    marginTop: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  dashboardTitle: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#2c3e50',
    marginTop: 0,
    marginBottom: '20px',
  },
  esiSection: {
    display: 'flex',
    justifyContent: 'center',
    padding: '20px',
    backgroundColor: '#f8f9fa',
    borderRadius: '12px',
    marginBottom: '20px',
  },
  esiScoreDisplay: {
    textAlign: 'center',
  },
  esiLabel: {
    fontSize: '14px',
    color: '#6c757d',
    marginBottom: '8px',
  },
  esiScore: {
    fontSize: '64px',
    fontWeight: 'bold',
    color: '#3b9dff',
    lineHeight: 1,
  },
  esiLevel: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#2c3e50',
    marginTop: '8px',
  },
  acuity: {
    fontSize: '14px',
    color: '#6c757d',
    marginTop: '4px',
  },
  decisionSection: {
    display: 'flex',
    gap: '12px',
    marginBottom: '20px',
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '10px',
    padding: '16px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  overrideButton: {
    flex: 1,
    backgroundColor: '#ffc107',
    color: '#000',
    border: 'none',
    borderRadius: '10px',
    padding: '16px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  overrideButtonActive: {
    backgroundColor: '#ff9800',
  },
  overridePanel: {
    backgroundColor: '#fff3cd',
    borderRadius: '10px',
    padding: '20px',
    marginBottom: '20px',
  },
  overrideTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#856404',
    marginBottom: '12px',
    textAlign: 'center',
  },
  esiButtons: {
    display: 'flex',
    gap: '8px',
    justifyContent: 'center',
    marginBottom: '12px',
  },
  esiButton: {
    width: '48px',
    height: '48px',
    borderRadius: '8px',
    border: '2px solid #dee2e6',
    backgroundColor: '#fff',
    fontSize: '20px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  esiButtonActive: {
    backgroundColor: '#3b9dff',
    color: '#fff',
    borderColor: '#3b9dff',
  },
  esiButtonDisabled: {
    opacity: 0.3,
    cursor: 'not-allowed',
  },
  confirmOverrideButton: {
    width: '100%',
    backgroundColor: '#dc3545',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '12px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
    marginTop: '8px',
  },
  finalDecisionCard: {
    backgroundColor: '#d4edda',
    borderRadius: '12px',
    padding: '20px',
    marginTop: '20px',
    border: '2px solid #28a745',
  },
  finalDecisionTitle: {
    fontSize: '22px',
    fontWeight: '600',
    color: '#155724',
    marginTop: 0,
    marginBottom: '12px',
  },
  finalDecisionContent: {
    fontSize: '16px',
    color: '#155724',
  },
  overrideNotice: {
    marginTop: '8px',
    padding: '8px',
    backgroundColor: '#fff3cd',
    color: '#856404',
    borderRadius: '6px',
    fontSize: '14px',
  },
  section: {
    marginTop: '20px',
    padding: '16px',
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
  },
  sectionTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: '12px',
  },
  sectionContent: {
    fontSize: '14px',
    color: '#495057',
    lineHeight: 1.6,
  },
  urgencyBadge: {
    marginTop: '12px',
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  urgentBadge: {
    backgroundColor: '#dc3545',
    color: '#fff',
    padding: '6px 12px',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: '600',
  },
  stableBadge: {
    backgroundColor: '#28a745',
    color: '#fff',
    padding: '6px 12px',
    borderRadius: '6px',
    fontSize: '13px',
    fontWeight: '600',
  },
  waitTime: {
    fontSize: '13px',
    color: '#6c757d',
  },
  subsection: {
    marginTop: '12px',
  },
  list: {
    margin: '8px 0',
    paddingLeft: '20px',
  },
  redFlagsBox: {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: '#f8d7da',
    borderLeft: '4px solid #dc3545',
    borderRadius: '4px',
  },
}