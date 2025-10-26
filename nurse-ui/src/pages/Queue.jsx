import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ERQueue, Patient, getRandomInteger } from '../utils/erQueue'

export default function Queue() {
  const navigate = useNavigate()
  
  // Initialize queue with sample data
  const [erQueue] = useState(() => {
    const queue = new ERQueue()
    const samplePatients = [
      { name: 'John Doe', triageLevel: 2, symptoms: 'Chest pain, shortness of breath', history: 'Previous heart condition', comments: 'Monitor closely' },
      { name: 'Sarah Smith', triageLevel: 3, symptoms: 'Severe headache, nausea', history: 'Migraines', comments: 'Requires pain management' },
      { name: 'Mike Johnson', triageLevel: 1, symptoms: 'Unresponsive, trauma', history: 'No known allergies', comments: 'Critical - immediate attention' },
      { name: 'Emily Davis', triageLevel: 4, symptoms: 'Minor cut on hand', history: 'None', comments: 'Low priority' },
      { name: 'Robert Brown', triageLevel: 2, symptoms: 'Difficulty breathing', history: 'Asthma', comments: 'Bring inhaler' },
      { name: 'Anna Wilson', triageLevel: 2, symptoms: 'High fever, chills', history: 'Diabetic', comments: 'Check blood sugar' },
      { name: 'David Lee', triageLevel: 3, symptoms: 'Abdominal pain', history: 'None', comments: 'Possible appendicitis' },
      { name: 'David Lee', triageLevel: 3, symptoms: 'Abdominal pain', history: 'None', comments: 'Possible appendicitis' },
      { name: 'David Lee', triageLevel: 3, symptoms: 'Abdominal pain', history: 'None', comments: 'Possible appendicitis' },

    ]
    
    samplePatients.forEach((p, idx) => {
      const patient = new Patient(
        1000 + idx,
        p.triageLevel,
        new Date(Date.now() + getRandomInteger(0, 5000))
      )
      patient.name = p.name
      patient.symptoms = p.symptoms
      patient.history = p.history
      patient.comments = p.comments
      queue.addPatient(patient)
    })
    
    return queue
  })
  
  const [patients, setPatients] = useState(erQueue.getAllPatientsSorted())
  const [selectedPatient, setSelectedPatient] = useState(null)

  const handleAddPatient = () => {
    navigate('/nurseform')
  }

  const handleRemovePatient = (id, e) => {
    e.stopPropagation() // Prevent card click
    erQueue.removePatient(id)
    setPatients(erQueue.getAllPatientsSorted())
  }

  const handleCardClick = (patient) => {
    setSelectedPatient(patient)
  }

  const closeModal = () => {
    setSelectedPatient(null)
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
    // Estimated processing time per ESI level (in minutes)
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
        {patients.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>🏥</div>
            <div style={styles.emptyText}>No patients in queue</div>
            <button onClick={handleAddPatient} style={styles.emptyButton}>
              Add First Patient
            </button>
          </div>
        ) : (
          <div style={styles.linkedList}>
            {patients.map((patient, index) => (
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
                    <span style={styles.nodePosition}>#{index + 1}</span>
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
                        {patient.name || `Patient ${patient.id}`}
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
                        {new Date(patient.timeIn).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </div>
                {index < patients.length - 1 && (
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
                  <span style={styles.detailValue}>{selectedPatient.name || `Patient ${selectedPatient.id}`}</span>
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
                  <span style={styles.detailValue}>{new Date(selectedPatient.timeIn).toLocaleString()}</span>
                </div>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Symptoms</h3>
                <p style={styles.detailText}>{selectedPatient.symptoms || 'No symptoms recorded'}</p>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Medical History</h3>
                <p style={styles.detailText}>{selectedPatient.history || 'No history recorded'}</p>
              </div>

              <div style={styles.detailSection}>
                <h3 style={styles.sectionTitle}>Comments</h3>
                <p style={styles.detailText}>{selectedPatient.comments || 'No comments'}</p>
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
}

