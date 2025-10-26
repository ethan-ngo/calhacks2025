import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

export default function TriageDashboard() {
  const navigate = useNavigate()
  const location = useLocation()
  const triageResult = location.state?.triageResult
  const patientData = location.state?.patientData

  const [isOverriding, setIsOverriding] = useState(false)
  const [overrideScore, setOverrideScore] = useState(null)
  const [finalDecision, setFinalDecision] = useState(null)

  if (!triageResult) {
    return (
      <div style={styles.container}>
        <div style={styles.errorCard}>
          <h2>No Triage Data</h2>
          <p>Please submit a triage assessment first.</p>
          <button onClick={() => navigate('/nurseform')} style={styles.backButton}>
            ← Back to Form
          </button>
        </div>
      </div>
    )
  }

  const handleAccept = () => {
    setFinalDecision({
      score: triageResult.triage_score,
      level: triageResult.triage_level,
      wasOverridden: false
    })
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
  }

  const handleFinalize = () => {
    // Create patient object for queue
    const newPatient = {
      id: Date.now(), // Generate unique ID
      name: patientData.name,
      age: patientData.age,
      gender: patientData.gender,
      triageLevel: finalDecision.score,
      triageLabel: finalDecision.level,
      symptoms: triageResult.assessment_summary?.primary_concern || 'See clinical findings',
      vitals: {
        heartRate: patientData.heartRate,
        bloodPressure: patientData.bloodPressure,
        temperature: patientData.temperature,
        respiratoryRate: patientData.respiratoryRate
      },
      comments: triageResult.clinical_recommendations?.join('; ') || '',
      wasOverridden: finalDecision.wasOverridden,
      originalScore: finalDecision.originalScore,
      timestamp: new Date().toISOString(),
      clinicalFindings: triageResult.clinical_findings,
      recommendations: triageResult.clinical_recommendations,
      nursingNotes: triageResult.nursing_notes
    }

    // Get existing queue from localStorage
    const existingQueue = JSON.parse(localStorage.getItem('erQueue') || '[]')
    
    // Add new patient
    existingQueue.push(newPatient)
    
    // Save back to localStorage
    localStorage.setItem('erQueue', JSON.stringify(existingQueue))
    
    // Dispatch event to notify Queue component
    window.dispatchEvent(new Event('queueUpdated'))
    
    console.log('Patient added to queue:', newPatient)
    
    // Navigate back to queue
    navigate('/')
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <button onClick={() => navigate('/nurseform')} style={styles.backButton}>
          ← Back
        </button>
        <h1 style={styles.title}>Triage Assessment Dashboard</h1>
      </div>

      <div style={styles.content}>
        {/* Patient Info Summary */}
        <div style={styles.patientCard}>
          <h2 style={styles.patientName}>Patient: {patientData?.name}</h2>
          <div style={styles.patientInfo}>
            <span>Age: {patientData?.age}</span>
            <span>Gender: {patientData?.gender}</span>
            <span>HR: {patientData?.heartRate}</span>
            <span>BP: {patientData?.bloodPressure}</span>
            <span>Temp: {patientData?.temperature}</span>
            <span>RR: {patientData?.respiratoryRate}</span>
          </div>
        </div>

        {!finalDecision ? (
          <div style={styles.dashboardCard}>
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
        ) : (
          <div style={styles.finalDecisionCard}>
            <h2 style={styles.finalDecisionTitle}>
              ✅ Final ESI Level: {finalDecision.score}
            </h2>
            <div style={styles.finalDecisionContent}>
              <div style={styles.finalLevel}>Level: {finalDecision.level}</div>
              {finalDecision.wasOverridden && (
                <div style={styles.overrideNotice}>
                  ⚠️ Overridden from Level {finalDecision.originalScore}
                </div>
              )}
            </div>
            <button onClick={handleFinalize} style={styles.finalizeButton}>
              Add to Queue & Return
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#e8eef3',
    padding: '40px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '20px',
    marginBottom: '30px',
  },
  title: {
    fontSize: '42px',
    fontWeight: '500',
    color: '#5a5a5a',
    margin: 0,
  },
  backButton: {
    backgroundColor: 'transparent',
    color: '#3b9dff',
    border: '2px solid #3b9dff',
    borderRadius: '12px',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  content: {
    maxWidth: '1200px',
    margin: '0 auto',
  },
  patientCard: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '20px',
    marginBottom: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  patientName: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#2c3e50',
    marginTop: 0,
    marginBottom: '12px',
  },
  patientInfo: {
    display: 'flex',
    gap: '20px',
    fontSize: '14px',
    color: '#6c757d',
    flexWrap: 'wrap',
  },
  dashboardCard: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '30px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
  },
  esiSection: {
    display: 'flex',
    justifyContent: 'center',
    padding: '30px',
    backgroundColor: '#f8f9fa',
    borderRadius: '12px',
    marginBottom: '30px',
  },
  esiScoreDisplay: {
    textAlign: 'center',
  },
  esiLabel: {
    fontSize: '16px',
    color: '#6c757d',
    marginBottom: '12px',
  },
  esiScore: {
    fontSize: '80px',
    fontWeight: 'bold',
    color: '#3b9dff',
    lineHeight: 1,
  },
  esiLevel: {
    fontSize: '22px',
    fontWeight: '600',
    color: '#2c3e50',
    marginTop: '12px',
  },
  acuity: {
    fontSize: '16px',
    color: '#6c757d',
    marginTop: '8px',
  },
  decisionSection: {
    display: 'flex',
    gap: '16px',
    marginBottom: '30px',
  },
  acceptButton: {
    flex: 1,
    backgroundColor: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    padding: '20px',
    fontSize: '18px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  overrideButton: {
    flex: 1,
    backgroundColor: '#ffc107',
    color: '#000',
    border: 'none',
    borderRadius: '12px',
    padding: '20px',
    fontSize: '18px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  overrideButtonActive: {
    backgroundColor: '#ff9800',
  },
  overridePanel: {
    backgroundColor: '#fff3cd',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '30px',
  },
  overrideTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#856404',
    marginBottom: '16px',
    textAlign: 'center',
  },
  esiButtons: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    marginBottom: '16px',
  },
  esiButton: {
    width: '60px',
    height: '60px',
    borderRadius: '10px',
    border: '2px solid #dee2e6',
    backgroundColor: '#fff',
    fontSize: '24px',
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
    borderRadius: '10px',
    padding: '16px',
    fontSize: '17px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  section: {
    marginTop: '24px',
    padding: '20px',
    backgroundColor: '#f8f9fa',
    borderRadius: '10px',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: '16px',
  },
  sectionContent: {
    fontSize: '15px',
    color: '#495057',
    lineHeight: 1.6,
  },
  urgencyBadge: {
    marginTop: '16px',
    display: 'flex',
    gap: '16px',
    alignItems: 'center',
  },
  urgentBadge: {
    backgroundColor: '#dc3545',
    color: '#fff',
    padding: '8px 16px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
  },
  stableBadge: {
    backgroundColor: '#28a745',
    color: '#fff',
    padding: '8px 16px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '600',
  },
  waitTime: {
    fontSize: '14px',
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
    marginTop: '16px',
    padding: '16px',
    backgroundColor: '#f8d7da',
    borderLeft: '4px solid #dc3545',
    borderRadius: '6px',
  },
  finalDecisionCard: {
    backgroundColor: '#d4edda',
    borderRadius: '16px',
    padding: '40px',
    textAlign: 'center',
    border: '3px solid #28a745',
  },
  finalDecisionTitle: {
    fontSize: '32px',
    fontWeight: '600',
    color: '#155724',
    marginTop: 0,
    marginBottom: '20px',
  },
  finalDecisionContent: {
    fontSize: '20px',
    color: '#155724',
    marginBottom: '24px',
  },
  finalLevel: {
    marginBottom: '12px',
  },
  overrideNotice: {
    padding: '12px',
    backgroundColor: '#fff3cd',
    color: '#856404',
    borderRadius: '8px',
    fontSize: '16px',
    display: 'inline-block',
  },
  finalizeButton: {
    backgroundColor: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    padding: '16px 48px',
    fontSize: '18px',
    fontWeight: '600',
    cursor: 'pointer',
  },
  errorCard: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '40px',
    textAlign: 'center',
    maxWidth: '500px',
    margin: '100px auto',
  },
}