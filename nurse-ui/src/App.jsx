import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import NurseForm from './pages/nurse_form'
import Queue from './pages/Queue'
import PatientWait from './pages/PatientWait'
import PatientChat from './pages/PatientChat'

function App() {
    return (
        <Routes>
            <Route path="/" element={<Queue />} />
            <Route path="/inputtest" element={<InputLoginPage />} />
            <Route path="/nurseform" element={<NurseForm />} />
            <Route path="/patientwait" element={<PatientWait />} />
            <Route path="/chat" element={<PatientChat />} />
        </Routes>
    )
}

export default App