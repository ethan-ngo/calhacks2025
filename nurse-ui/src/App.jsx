import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import NurseForm from './pages/nurse_form'
import Queue from './pages/Queue'
import PatientWait from './pages/PatientWait'
import PatientChat from './pages/PatientChat'
import VoiceNurse from './pages/voice_nurse'
import TriageDashboard from './pages/nurse_dashboard'

function App() {
    return (
        <Routes>
            <Route path="/voice_nurse" element={<VoiceNurse />} />
            <Route path="/" element={<Queue />} />
            <Route path="/inputtest" element={<InputLoginPage />} />
            <Route path="/nurseform" element={<NurseForm />} />
            <Route path="/patientwait" element={<PatientWait />} />
            <Route path="/patientwait/:patientId" element={<PatientWait />} />
            <Route path="/patientchat" element={<PatientChat />} />
            <Route path="/patientchat/:patientId" element={<PatientChat />} />
            <Route path="/triage-dashboard" element={<TriageDashboard />} />
        </Routes>
    )
}

export default App