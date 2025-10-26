export default function CommentsCard({ comments, handleInputChange }) {
  return (
    <div style={styles.card}>
      <h2 style={styles.sectionTitle}>Comments</h2>
      <textarea
        name="comments"
        value={comments}
        onChange={handleInputChange}
        placeholder="Enter any patient specific comments here..."
        style={styles.textarea}
      />
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
  textarea: {
    width: '100%',
    minHeight: '100px',
    border: 'none',
    fontSize: '15px',
    color: '#666',
    resize: 'vertical',
    fontFamily: 'inherit',
    outline: 'none',
  },
}

