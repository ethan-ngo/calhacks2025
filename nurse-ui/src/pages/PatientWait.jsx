import { useState, useEffect } from 'react'

export default function PatientWait() {
  const [waitTime, setWaitTime] = useState(20)
  const [queuePosition, setQueuePosition] = useState(5)
  const [patientName, setPatientName] = useState('Araya')

  const handleUpdate = async () => {
    // TODO: Fetch updated queue information from backend
    // For now, just simulate an update
    try {
      // const response = await fetch('http://127.0.0.1:5000/patient/status', {
      //   method: 'GET',
      // })
      // const data = await response.json()
      // setWaitTime(data.waitTime)
      // setQueuePosition(data.position)
      
      alert('System updated!')
    } catch (error) {
      console.error('Failed to update:', error)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <h1 style={styles.greeting}>
          Hello, Welcome
        </h1>
        <h1 style={styles.name}>
          to <span style={styles.highlight}>{patientName}</span>
        </h1>

        <div style={styles.card}>
          <div style={styles.cardLabel}>Estimated Wait Time</div>
          <div style={styles.waitTime}>
            <span style={styles.waitNumber}>{waitTime}</span>
            <span style={styles.waitUnit}>mins</span>
          </div>
        </div>

        <div style={styles.positionText}>
          Current Queue Position: <span style={styles.positionNumber}>{queuePosition}th</span>
        </div>

        <button onClick={handleUpdate} style={styles.updateButton}>
          Update System
        </button>
      </div>
    </div>
  )
}

const styles = {
  container: {
    width: '100vw',
    minHeight: '100vh',
    backgroundColor: '#e8eef3',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    padding: '20px',
    boxSizing: 'border-box',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  content: {
    width: '100%',
    maxWidth: '500px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
  },
  greeting: {
    fontSize: 'clamp(32px, 8vw, 48px)',
    fontWeight: '600',
    color: '#1f2937',
    margin: '0 0 10px 0',
  },
  name: {
    fontSize: 'clamp(32px, 8vw, 48px)',
    fontWeight: '600',
    color: '#1f2937',
    margin: '0 0 60px 0',
  },
  highlight: {
    color: '#3b9dff',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: '24px',
    padding: '40px 60px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
    marginBottom: '40px',
    width: '100%',
    maxWidth: '400px',
    boxSizing: 'border-box',
  },
  cardLabel: {
    fontSize: '18px',
    color: '#6b7280',
    marginBottom: '20px',
    fontWeight: '500',
  },
  waitTime: {
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'center',
  },
  waitNumber: {
    fontSize: 'clamp(72px, 15vw, 96px)',
    fontWeight: '700',
    color: '#3b9dff',
    lineHeight: 1,
  },
  waitUnit: {
    fontSize: 'clamp(36px, 7vw, 48px)',
    fontWeight: '400',
    color: '#3b9dff',
    marginLeft: '4px',
  },
  positionText: {
    fontSize: '20px',
    color: '#6b7280',
    marginBottom: '80px',
    fontWeight: '400',
  },
  positionNumber: {
    fontWeight: '700',
    color: '#1f2937',
  },
  updateButton: {
    backgroundColor: '#3b9dff',
    color: '#fff',
    border: 'none',
    borderRadius: '50px',
    padding: '18px 80px',
    fontSize: '20px',
    fontWeight: '600',
    cursor: 'pointer',
    boxShadow: '0 4px 12px rgba(59, 157, 255, 0.3)',
    transition: 'all 0.2s ease',
  },
}

