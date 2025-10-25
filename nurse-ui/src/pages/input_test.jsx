import { useState } from 'react';
import { ERQueue, Patient, getRandomInteger } from '../utils/erQueue';

export default function ERQueueTest() {
  const [erQueue] = useState(() => new ERQueue());
  const [snapshot, setSnapshot] = useState(erQueue.getAllPatientsSorted());

  const [triageLevel, setTriageLevel] = useState('');
  const [patientId, setPatientId] = useState('');
  const [updateId, setUpdateId] = useState('');
  const [newTriageLevel, setNewTriageLevel] = useState('');

  // Add patient
  const handleAddPatient = () => {
    if (!triageLevel) return;
    const id = Math.floor(Math.random() * 10000);
    const patient = new Patient(id, Number(triageLevel), new Date(Date.now() + getRandomInteger(0, 5000)));
    erQueue.addPatient(patient);
    setSnapshot(erQueue.getAllPatientsSorted());
    setTriageLevel('');
  };

  // Remove patient
  const handleRemovePatient = () => {
    if (!patientId) return;
    erQueue.removePatient(Number(patientId));
    setSnapshot(erQueue.getAllPatientsSorted());
    setPatientId('');
  };

  // Update patient triage
  const handleUpdatePatient = () => {
    if (!updateId || !newTriageLevel) return;
    erQueue.changePatientInfo(Number(updateId), Number(newTriageLevel));
    setSnapshot(erQueue.getAllPatientsSorted());
    setUpdateId('');
    setNewTriageLevel('');
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h2>🏥 ER Queue Test</h2>

      {/* Add Section */}
      <div style={{ marginBottom: '15px' }}>
        <input
          type="number"
          placeholder="Triage Level (1-5)"
          value={triageLevel}
          onChange={(e) => setTriageLevel(e.target.value)}
        />
        <button onClick={handleAddPatient} style={{ marginLeft: '8px' }}>
          Add Patient
        </button>
      </div>

      {/* Remove Section */}
      <div style={{ marginBottom: '15px' }}>
        <input
          type="number"
          placeholder="Patient ID to remove"
          value={patientId}
          onChange={(e) => setPatientId(e.target.value)}
        />
        <button onClick={handleRemovePatient} style={{ marginLeft: '8px' }}>
          Remove Patient
        </button>
      </div>

      {/* Update Section */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="number"
          placeholder="Patient ID to update"
          value={updateId}
          onChange={(e) => setUpdateId(e.target.value)}
        />
        <input
          type="number"
          placeholder="New Triage Level"
          value={newTriageLevel}
          onChange={(e) => setNewTriageLevel(e.target.value)}
          style={{ marginLeft: '8px' }}
        />
        <button onClick={handleUpdatePatient} style={{ marginLeft: '8px' }}>
          Update Triage
        </button>
      </div>

      {/* Queue List */}
      <h3>🩺 Current Queue:</h3>
      <ul>
        {snapshot.map((p, i) => (
          <li key={p.id}>
            <strong>#{i + 1}</strong> — ID: {p.id}, Triage: {p.triageLevel}, Time:{' '}
            {new Date(p.timeIn).toLocaleTimeString()}
          </li>
        ))}
      </ul>
    </div>
  );
}
