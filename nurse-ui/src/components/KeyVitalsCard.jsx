export default function KeyVitalsCard({ patientData, handleInputChange }) {
  return (
    <div style={styles.card}>
      <h2 style={styles.sectionTitle}>Key Vitals</h2>
      <div style={styles.vitalsGrid}>
        <div>
          <div style={styles.vitalLabel}>Heart rate</div>
          <div style={styles.vitalBox}>
            <span style={styles.icon}>❤️</span>
            <input 
              type="text" 
              name="heartRate"
              value={patientData.heartRate}
              onChange={handleInputChange}
              style={styles.vitalInput}
            />
          </div>
        </div>
        <div>
          <div style={styles.vitalLabel}>Blood Pressure</div>
          <div style={styles.vitalBox}>
            <span style={styles.icon}>🩸</span>
            <input 
              type="text" 
              name="bloodPressure"
              value={patientData.bloodPressure}
              onChange={handleInputChange}
              style={styles.vitalInput}
            />
          </div>
        </div>
        <div>
          <div style={styles.vitalLabel}>Temperature</div>
          <div style={styles.vitalBox}>
            <span style={styles.icon}>🌡️</span>
            <input 
              type="text" 
              name="temperature"
              value={patientData.temperature}
              onChange={handleInputChange}
              style={styles.vitalInput}
            />
          </div>
        </div>
        <div>
          <div style={styles.vitalLabel}>Respiratory rate</div>
          <div style={styles.vitalBox}>
            <span style={styles.icon}>🫁</span>
            <input 
              type="text" 
              name="respiratoryRate"
              value={patientData.respiratoryRate}
              onChange={handleInputChange}
              style={styles.vitalInput}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

const styles = {
  card: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '24px',
    marginBottom: '20px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  sectionTitle: {
    fontSize: '20px',
    fontWeight: '600',
    marginBottom: '20px',
    color: '#000',
  },
  vitalsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: '16px',
  },
  vitalLabel: {
    fontSize: '14px',
    color: '#666',
    marginBottom: '8px',
  },
  vitalBox: {
    backgroundColor: '#f5f5f5',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  icon: {
    fontSize: '20px',
    flexShrink: 0,
  },
  vitalInput: {
    border: 'none',
    background: 'transparent',
    fontSize: '16px',
    fontWeight: '500',
    color: '#000',
    flex: 1,
    outline: 'none',
    minWidth: 0,
  },
}

