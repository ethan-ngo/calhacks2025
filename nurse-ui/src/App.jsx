import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import NurseForm from './pages/nurse_form'
import Queue from './pages/Queue'
import PatientWait from './pages/PatientWait'
import VoiceNurse from './pages/voice_nurse'

function App() {
    return (
        <Routes>
            <Route path="/input_test" element={<InputLoginPage />} />
            <Route path="/voice_nurse" element={<VoiceNurse />} />
            <Route path="/" element={<Queue />} />
            <Route path="/inputtest" element={<InputLoginPage />} />
            <Route path="/nurseform" element={<NurseForm />} />
            <Route path="/patientwait" element={<PatientWait />} />
        </Routes>
    )
}

export default App