import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

export default function Queue() {
  const navigate = useNavigate()
  
  // Load patients from localStorage
  const [patients, setPatients] = useState(() => {
    const saved = localStorage.getItem('erQueue')
    return saved ? JSON.parse(saved) : []
  })
  
  const [selectedPatient, setSelectedPatient] = useState(null)
  const [alerts, setAlerts] = useState({})
  const [selectedAlert, setSelectedAlert] = useState(null)

  // Fetch alerts from backend
  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/alerts')
      const data = await response.json()
      
      if (data.success) {
        setAlerts(data.alerts || {})
      }
    } catch (error) {
      console.error('Error fetching alerts:', error)
    }
  }

  // Listen for queue updates and fetch alerts
  useEffect(() => {
    const handleQueueUpdate = () => {
      const saved = localStorage.getItem('erQueue')
      setPatients(saved ? JSON.parse(saved) : [])
    }
    
    // Fetch alerts on mount and every 30 seconds
    fetchAlerts()
    const alertInterval = setInterval(fetchAlerts, 30000)
    
    window.addEventListener('queueUpdated', handleQueueUpdate)
    
    return () => {
      window.removeEventListener('queueUpdated', handleQueueUpdate)
      clearInterval(alertInterval)
    }
  }, [])

  const handleAddPatient = () => {
    navigate('/nurseform')
  }

  const handleRemovePatient = (id, e) => {
    e.stopPropagation()
    const updatedPatients = patients.filter(p => p.id !== id)
    setPatients(updatedPatients)
    localStorage.setItem('erQueue', JSON.stringify(updatedPatients))
  }

  const handleCardClick = (patient) => {
    setSelectedPatient(patient)
  }

  const closeModal = () => {
    setSelectedPatient(null)
  }

  const handleAlertClick = (patientId, e) => {
    e.stopPropagation()
    const alert = alerts[patientId]
    if (alert) {
      setSelectedAlert(alert)
    }
  }

  const closeAlertModal = () => {
    setSelectedAlert(null)
  }

  const handleAcceptAlert = async () => {
    if (!selectedAlert) return
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/alerts/${selectedAlert.patient_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'accept' })
      })
      
      const data = await response.json()
      
      if (data.success) {
        // Update patient in queue with new triage
        const updatedPatients = patients.map(p => 
          p.patientId === selectedAlert.patient_id 
            ? { ...p, triageLevel: selectedAlert.new_triage }
            : p
        )
        setPatients(updatedPatients)
        localStorage.setItem('erQueue', JSON.stringify(updatedPatients))
        
        // Refresh alerts
        await fetchAlerts()
        closeAlertModal()
        alert('✅ Triage level updated successfully')
      }
    } catch (error) {
      console.error('Error accepting alert:', error)
      alert('Failed to update triage')
    }
  }

  const handleRejectAlert = async () => {
    if (!selectedAlert) return
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/alerts/${selectedAlert.patient_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reject' })
      })
      
      const data = await response.json()
      
      if (data.success) {
        await fetchAlerts()
        closeAlertModal()
      }
    } catch (error) {
      console.error('Error rejecting alert:', error)
    }
  }

  const getTriageColor = (level) => {
    const colors = {
      1: '#ff3b3b', // Red - Immediate
      2: '#ff8c3b', // Orange - Emergent
      3: '#ffd93b', // Yellow - Urgent
      4: '#6bff3b', // Green - Less urgent
      5: '#3b9dff', // Blue - Non-urgent
    }
    return colors[level] || '#ccc'
  }

  const getTriageLabel = (level) => {
    const labels = {
      1: 'Immediate',
      2: 'Emergent',
      3: 'Urgent',
      4: 'Less Urgent',
      5: 'Non-Urgent',
    }
    return labels[level] || 'Unknown'
  }

  const calculateEstimatedWaitTime = () => {
    const processingTimes = {
      1: 5,   // Immediate
      2: 15,  // Emergent
      3: 30,  // Urgent
      4: 45,  // Less urgent
      5: 60,  // Non-urgent
    }
    
    const totalMinutes = patients.reduce((sum, patient) => {
      return sum + (processingTimes[patient.triageLevel] || 30)
    }, 0)
    
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  // Sort patients by triage level (lower = higher priority)
  const sortedPatients = [...patients].sort((a, b) => a.triageLevel - b.triageLevel)

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>ER Queue Dashboard</h1>
        <button onClick={handleAddPatient} style={styles.addButton}>
          + Add Patient
        </button>
      </div>

      <div style={styles.statsContainer}>
        <div style={styles.statItem}>
          <div style={styles.statNumber}>{patients.length}</div>
          <div style={styles.statLabel}>Total Patients</div>
        </div>
        <div style={styles.statDivider}></div>
        <div style={styles.statItem}>
          <div style={styles.statNumber}>
            {patients.filter(p => p.triageLevel <= 2).length}
          </div>
          <div style={styles.statLabel}>Critical</div>
        </div>
        <div style={styles.statDivider}></div>
        <div style={styles.statItem}>
          <div style={styles.statNumber}>{calculateEstimatedWaitTime()}</div>
          <div style={styles.statLabel}>Est. Wait Time</div>
        </div>
      </div>

      <div style={styles.queueContainer}>
        {sortedPatients.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>🏥</div>
            <div style={styles.emptyText}>No patients in queue</div>
            <button onClick={handleAddPatient} style={styles.emptyButton}>
              Add First Patient
            </button>
          </div>
        ) : (
          <div style={styles.linkedList}>
            {sortedPatients.map((patient, index) => (
              <div key={patient.id} style={styles.nodeWrapper}>
                <div 
                  style={styles.node} 
                  onClick={() => handleCardClick(patient)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)'
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(59, 157, 255, 0.15)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.06)'
                  }}
                >
                  <div style={styles.nodeHeader}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={styles.nodePosition}>#{index + 1}</span>
                      {alerts[patient.patientId] && (
                        <button
                          onClick={(e) => handleAlertClick(patient.patientId, e)}
                          style={styles.alertBadge}
                          title="Patient condition worsened - Click to review"
                        >
                          ⚠️
                        </button>
                      )}
                    </div>
                    <button
                      onClick={(e) => handleRemovePatient(patient.id, e)}
                      style={styles.removeButton}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.color = '#374151'
                        e.currentTarget.style.transform = 'scale(1.2)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.color = '#9ca3af'
                        e.currentTarget.style.transform = 'scale(1)'
                      }}
                    >
                      ✕
                    </button>
                  </div>
                  <div style={styles.nodeBody}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                      <div style={styles.nodeName}>
                        {patient.name}
                      </div>
                      <span 
                        style={{
                          ...styles.nodeTriageLevel,
                          backgroundColor: getTriageColor(patient.triageLevel),
                          color: '#fff'
                        }}
                      >
                        ESI {patient.triageLevel}
                      </span>
                    </div>
                    <div style={styles.nodeDetails}>
                      <div style={styles.nodeDetail}>
                        <span style={styles.nodeDetailLabel}>ID:</span> {patient.id}
                      </div>
                      <div style={styles.nodeDetail}>
                        <span style={styles.nodeDetailLabel}>Time:</span>{' '}
                        {new Date(patient.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
                {index < sortedPatients.length - 1 && (
                  <div style={styles.connector}>
                    <div style={styles.arrow}>→</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Patient Details Modal */}
      {selectedPatient && (
        <div style={styles.modalOverlay} onClick={closeModal}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>Patient Details</h2>
              <button onClick={closeModal} style={styles.closeButton}>✕</button>
            </div>
            <div style={styles.modalBody}>
              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Basic Information</h3>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Name:</span>
                  <span style={styles.detailValue}>{selectedPatient.name}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Age:</span>
                  <span style={styles.detailValue}>{selectedPatient.age}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Gender:</span>
                  <span style={styles.detailValue}>{selectedPatient.gender}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>ID:</span>
                  <span style={styles.detailValue}>{selectedPatient.id}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>ESI Level:</span>
                  <span 
                    style={{
                      ...styles.detailValue,
                      backgroundColor: getTriageColor(selectedPatient.triageLevel),
                      color: '#fff',
                      padding: '4px 12px',
                      borderRadius: '8px',
                      fontWeight: '600'
                    }}
                  >
                    {selectedPatient.triageLevel} - {getTriageLabel(selectedPatient.triageLevel)}
                  </span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Time In:</span>
                  <span style={styles.detailValue}>{new Date(selectedPatient.timestamp).toLocaleString()}</span>
                </div>
                {selectedPatient.wasOverridden && (
                  <div style={{ marginTop: '12px', padding: '10px', backgroundColor: '#fff3cd', borderRadius: '8px', fontSize: '14px', color: '#856404' }}>
                    ⚠️ ESI Level was overridden from {selectedPatient.originalScore} to {selectedPatient.triageLevel}
                  </div>
                )}
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Vitals</h3>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Heart Rate:</span>
                  <span style={styles.detailValue}>{selectedPatient.vitals?.heartRate || 'N/A'}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Blood Pressure:</span>
                  <span style={styles.detailValue}>{selectedPatient.vitals?.bloodPressure || 'N/A'}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Temperature:</span>
                  <span style={styles.detailValue}>{selectedPatient.vitals?.temperature || 'N/A'}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Respiratory Rate:</span>
                  <span style={styles.detailValue}>{selectedPatient.vitals?.respiratoryRate || 'N/A'}</span>
                </div>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Clinical Assessment</h3>
                <p style={styles.detailText}>{selectedPatient.symptoms || 'No symptoms recorded'}</p>
              </div>

              {selectedPatient.clinicalFindings?.red_flags?.length > 0 && (
                <div style={styles.detailSection}>
                  <h3 style={styles.sectionTitle}>🚨 Red Flags</h3>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px', color: '#dc3545' }}>
                    {selectedPatient.clinicalFindings.red_flags.map((flag, i) => (
                      <li key={i} style={{ marginBottom: '6px' }}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedPatient.recommendations?.length > 0 && (
                <div style={styles.detailSection}>
                  <h3 style={styles.sectionTitle}>Recommendations</h3>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    {selectedPatient.recommendations.map((rec, i) => (
                      <li key={i} style={{ marginBottom: '6px', color: '#4b5563' }}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Comments</h3>
                <p style={styles.detailText}>{selectedPatient.comments || 'No comments'}</p>
              </div>

              {selectedPatient.nursingNotes?.length > 0 && (
                <div style={styles.detailSection}>
                  <h3 style={styles.sectionTitle}>Nursing Notes</h3>
                  <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                    {selectedPatient.nursingNotes.map((note, i) => (
                      <li key={i} style={{ marginBottom: '6px', color: '#4b5563' }}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Alert Modal for Triage Updates */}
      {selectedAlert && (
        <div style={styles.modalOverlay} onClick={closeAlertModal}>
          <div style={styles.alertModalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.alertModalHeader}>
              <h2 style={styles.alertModalTitle}>⚠️ Triage Alert</h2>
              <button onClick={closeAlertModal} style={styles.closeButton}>✕</button>
            </div>
            <div style={styles.modalBody}>
              <div style={styles.alertWarning}>
                Patient condition has worsened. Review and update triage level.
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Patient Information</h3>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Name:</span>
                  <span style={styles.detailValue}>{selectedAlert.patient_name}</span>
                </div>
                <div style={styles.detailRow}>
                  <span style={styles.detailLabel}>Reported:</span>
                  <span style={styles.detailValue}>{new Date(selectedAlert.timestamp).toLocaleString()}</span>
                </div>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Triage Change</h3>
                <div style={styles.triageComparison}>
                  <div style={styles.triageBox}>
                    <div style={styles.triageBoxLabel}>Current ESI</div>
                    <div 
                      style={{
                        ...styles.triageBoxValue,
                        backgroundColor: getTriageColor(selectedAlert.original_triage)
                      }}
                    >
                      {selectedAlert.original_triage}
                    </div>
                  </div>
                  <div style={styles.triageArrow}>→</div>
                  <div style={styles.triageBox}>
                    <div style={styles.triageBoxLabel}>Suggested ESI</div>
                    <div 
                      style={{
                        ...styles.triageBoxValue,
                        backgroundColor: getTriageColor(selectedAlert.new_triage)
                      }}
                    >
                      {selectedAlert.new_triage}
                    </div>
                    <div style={styles.triageBoxLevel}>{selectedAlert.new_triage_level}</div>
                  </div>
                </div>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Recent Symptoms</h3>
                <p style={styles.detailText}>{selectedAlert.symptoms}</p>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Assessment</h3>
                <p style={styles.detailText}>{selectedAlert.reason}</p>
              </div>

              <div style={styles.alertActions}>
                <button onClick={handleRejectAlert} style={styles.rejectButton}>
                  Dismiss Alert
                </button>
                <button onClick={handleAcceptAlert} style={styles.acceptButton}>
                  Accept & Update Triage
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  container: {
    width: '100vw',
    height: '100vh',
    backgroundColor: '#e8eef3',
    padding: '40px',
    boxSizing: 'border-box',
    overflowY: 'auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
  },
  title: {
    fontSize: '42px',
    fontWeight: '500',
    color: '#5a5a5a',
    margin: 0,
  },
  addButton: {
    backgroundColor: '#3b9dff',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    padding: '14px 28px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    boxShadow: '0 2px 8px rgba(59, 157, 255, 0.25)',
    transition: 'all 0.2s ease',
  },
  statsContainer: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '20px 32px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginBottom: '30px',
    border: '1px solid #f3f4f6',
  },
  statItem: {
    textAlign: 'center',
    flex: 1,
  },
  statDivider: {
    width: '1px',
    height: '60px',
    backgroundColor: '#e5e7eb',
  },
  statNumber: {
    fontSize: '32px',
    fontWeight: '700',
    color: '#3b9dff',
    marginBottom: '6px',
  },
  statLabel: {
    fontSize: '13px',
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  queueContainer: {
    backgroundColor: '#fff',
    borderRadius: '20px',
    padding: '32px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
    minHeight: '400px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '400px',
  },
  emptyIcon: {
    fontSize: '80px',
    marginBottom: '20px',
    opacity: 0.3,
  },
  emptyText: {
    fontSize: '20px',
    color: '#999',
    marginBottom: '24px',
  },
  emptyButton: {
    backgroundColor: '#3b9dff',
    color: '#fff',
    border: 'none',
    borderRadius: '12px',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '500',
    cursor: 'pointer',
  },
  linkedList: {
    display: 'flex',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: '0',
    paddingBottom: '20px',
  },
  nodeWrapper: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    gap: '0',
    marginBottom: '24px',
  },
  node: {
    width: '240px',
    minWidth: '240px',
    backgroundColor: '#fff',
    borderRadius: '16px',
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    border: '1px solid #e5e7eb',
    transition: 'all 0.3s ease',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
  },
  nodeHeader: {
    padding: '12px 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    color: '#2c3e50',
    fontWeight: '600',
    backgroundColor: '#f3f4f6',
  },
  nodePosition: {
    fontSize: '20px',
    fontWeight: '700',
  },
  nodeTriageLevel: {
    fontSize: '14px',
    padding: '3px 10px',
    borderRadius: '6px',
    fontWeight: '700',
  },
  nodeBody: {
    padding: '16px',
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  nodeName: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1f2937',
  },
  nodeDetails: {
    display: 'flex',
    flexDirection: 'column',
    gap: '5px',
  },
  nodeDetail: {
    fontSize: '12px',
    color: '#6b7280',
  },
  nodeDetailLabel: {
    fontWeight: '600',
    color: '#9ca3af',
    fontSize: '11px',
  },
  removeButton: {
    backgroundColor: 'transparent',
    color: '#9ca3af',
    border: 'none',
    fontSize: '18px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 0,
    lineHeight: 1,
  },
  connector: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    width: '48px',
    position: 'relative',
  },
  arrow: {
    fontSize: '32px',
    color: '#3b9dff',
    fontWeight: '300',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    width: '90%',
    maxWidth: '600px',
    maxHeight: '80vh',
    overflow: 'auto',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  modalHeader: {
    padding: '24px',
    borderBottom: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    position: 'sticky',
    top: 0,
    backgroundColor: '#fff',
    zIndex: 1,
  },
  modalTitle: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#2c3e50',
    margin: 0,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '28px',
    color: '#999',
    cursor: 'pointer',
    padding: '0',
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modalBody: {
    padding: '24px',
  },
  detailSection: {
    marginBottom: '24px',
  },
  sectionTitle: {
    fontSize: '18px',
    fontWeight: '600',
    color: '#2c3e50',
    marginBottom: '12px',
    marginTop: 0,
  },
  detailRow: {
    display: 'flex',
    marginBottom: '12px',
    alignItems: 'center',
  },
  detailLabel: {
    fontWeight: '600',
    color: '#666',
    minWidth: '140px',
  },
  detailValue: {
    color: '#2c3e50',
  },
  detailText: {
    color: '#4b5563',
    lineHeight: '1.6',
    margin: 0,
  },
  alertBadge: {
    backgroundColor: '#ff3b3b',
    color: '#fff',
    border: 'none',
    borderRadius: '50%',
    width: '24px',
    height: '24px',
    fontSize: '14px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 0,
    animation: 'pulse 2s infinite',
    boxShadow: '0 0 10px rgba(255, 59, 59, 0.5)',
  },
  alertModalContent: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    width: '90%',
    maxWidth: '600px',
    maxHeight: '80vh',
    overflow: 'auto',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
    border: '3px solid #ff3b3b',
  },
  alertModalHeader: {
    padding: '24px',
    borderBottom: '2px solid #ff3b3b',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    position: 'sticky',
    top: 0,
    backgroundColor: '#fff3f3',
    zIndex: 1,
  },
  alertModalTitle: {
    fontSize: '24px',
    fontWeight: '600',
    color: '#ff3b3b',
    margin: 0,
  },
  alertWarning: {
    backgroundColor: '#fff3cd',
    border: '1px solid #ffeb3b',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '20px',
    fontSize: '16px',
    fontWeight: '600',
    color: '#856404',
    textAlign: 'center',
  },
  triageComparison: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '24px',
    padding: '20px',
    backgroundColor: '#f9fafb',
    borderRadius: '12px',
  },
  triageBox: {
    textAlign: 'center',
  },
  triageBoxLabel: {
    fontSize: '14px',
    color: '#6b7280',
    marginBottom: '8px',
    fontWeight: '600',
  },
  triageBoxValue: {
    width: '80px',
    height: '80px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '36px',
    fontWeight: '700',
    color: '#fff',
    margin: '0 auto 8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  },
  triageBoxLevel: {
    fontSize: '12px',
    color: '#6b7280',
    fontWeight: '600',
  },
  triageArrow: {
    fontSize: '32px',
    color: '#ff3b3b',
    fontWeight: '600',
  },
  alertActions: {
    display: 'flex',
    gap: '12px',
    marginTop: '24px',
    justifyContent: 'flex-end',
  },
  rejectButton: {
    backgroundColor: '#e5e7eb',
    color: '#374151',
    border: 'none',
    borderRadius: '8px',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  acceptButton: {
    backgroundColor: '#ff3b3b',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '12px 24px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
}