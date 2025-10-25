import { useState } from 'react';
import { ERQueue, Patient, getRandomInteger } from '../utils/erQueue'; // import your ERQueue class

export default function ERQueueTest() {
  // Create the queue once
  const [erQueue] = useState(() => new ERQueue());

  // State for triggering re-render
  const [snapshot, setSnapshot] = useState(erQueue.getAllPatientsSorted());

  // Inputs
  const [triageLevel, setTriageLevel] = useState('');
  const [patientId, setPatientId] = useState('');

  // Add a new patient
  const handleAddPatient = () => {
    if (!triageLevel) return;

    const id = Math.floor(Math.random() * 10000); // random unique ID
    const patient = new Patient(id, Number(triageLevel), new Date((Date.now() + getRandomInteger(0, 5000))));
    erQueue.addPatient(patient);
    setSnapshot(erQueue.getAllPatientsSorted());
    setTriageLevel('');
  };

  // Remove a patient by ID
  const handleRemovePatient = () => {
    if (!patientId) return;
    erQueue.removePatient(Number(patientId));
    setSnapshot(erQueue.getAllPatientsSorted());
    setPatientId('');
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>ER Queue Test</h2>

      <div style={{ marginBottom: '10px' }}>
        <input
          type="number"
          placeholder="Triage Level (1-5)"
          value={triageLevel}
          onChange={(e) => setTriageLevel(e.target.value)}
        />
        <button onClick={handleAddPatient} style={{ marginLeft: '5px' }}>
          Add Patient
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <input
          type="number"
          placeholder="Patient ID to remove"
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
        />
        <button onClick={handleRemovePatient} style={{ marginLeft: '5px' }}>
          Remove Patient
        </button>
      </div>

      <h3>Current Queue:</h3>
      <ul>
        {snapshot.map((p, i) => (
          <li key={p.id}>
            ({i}) ID: {p.id}, Triage: {p.triageLevel}, Time:{' '}
            {new Date(p.timeIn).toLocaleTimeString()}
          </li>
        ))}
      </ul>
    </div>
  );
}
