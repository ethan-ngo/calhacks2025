import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import VoiceNurse from './pages/voice_nurse'

function App() {
    return (
        <Routes>
            <Route path="/input_test" element={<InputLoginPage />} />
            <Route path="/voice_nurse" element={<VoiceNurse />} />
        </Routes>
    )
}

export default App