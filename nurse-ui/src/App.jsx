import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import NurseForm from './pages/nurse_form'
import Queue from './pages/Queue'

function App() {
    return (
        <Routes>
            <Route path="/" element={<Queue />} />
            <Route path="/inputtest" element={<InputLoginPage />} />
            <Route path="/nurseform" element={<NurseForm />} />
            <Route path="/queue" element={<Queue />} />
        </Routes>
    )
}

export default App