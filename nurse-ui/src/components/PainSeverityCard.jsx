export default function PainSeverityCard({ painSeverity, handleInputChange }) {
  return (
    <div style={styles.painCard}>
      <div style={styles.painLabel}>Pain Severity</div>
      <div style={styles.painScore}>
        <input 
          type="text" 
          name="painSeverity"
          value={painSeverity}
          onChange={handleInputChange}
          style={styles.painInput}
          size={painSeverity.length || 1}
          minLength={0}
          maxLength={2}
        />
        /
        <p style={{width: '45%'}}>
        10
        </p>
      </div>
    </div>
  )
}

const styles = {
  painCard: {
    backgroundColor: '#fff',
    borderRadius: '16px',
    padding: '40px 32px',
    textAlign: 'left',
    minWidth: '250px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'flex-start',
    height: '100%',
  },
  painLabel: {
    fontSize: '18px',
    color: '#666',
    marginBottom: '24px',
  },
  painScore: {
    fontSize: '60px',
    fontWeight: '600',
    color: '#000',
    display: 'flex',
    alignItems: 'baseline',
    justifyContent: 'flex-start',
    gap: '6px',
  },
  painInput: {
    border: 'none',
    fontSize: '60px',
    fontWeight: '550',
    width: '40%',
    textAlign: 'right',
    background: 'transparent',
    outline: 'none',
    padding: 0,
    margin: 0,
  },
}

