export default function PatientInfoCard({ patientData, handleInputChange }) {
  return (
    <div style={styles.card}>
      <div style={styles.infoRow}>
        <span style={styles.label}>Name:</span>
        <input 
          type="text" 
          name="name"
          value={patientData.name}
          onChange={handleInputChange}
          style={styles.input}
        />
      </div>
      <div style={styles.infoRow}>
        <span style={styles.label}>Age:</span>
        <input 
          type="text" 
          name="age"
          value={patientData.age}
          onChange={handleInputChange}
          style={styles.input}
        />
      </div>
      <div style={styles.infoRow}>
        <span style={styles.label}>Gender:</span>
        <input 
          type="text" 
          name="gender"
          value={patientData.gender}
          onChange={handleInputChange}
          style={styles.input}
        />
      </div>
      <div style={styles.infoRow}>
        <span style={styles.label}>Weight:</span>
        <input 
          type="text" 
          name="weight"
          value={patientData.weight}
          onChange={handleInputChange}
          style={styles.input}
        />
      </div>
    </div>
  )
}

const styles = {
  card: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    flex: 1,
  },
  infoRow: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: '12px',
    gap: '8px',
  },
  label: {
    color: '#999',
    fontSize: '16px',
    minWidth: '70px',
  },
  input: {
    border: 'none',
    fontSize: '16px',
    color: '#000',
    fontWeight: '500',
    background: 'transparent',
    flex: 1,
    outline: 'none',
  },
}

