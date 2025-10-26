import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import NurseForm from './pages/nurse_form'

function App() {
    return (
        <Routes>
            <Route path="/" element={<p>Hello World</p>} />
            <Route path="/inputtest" element={<InputLoginPage />} />
            <Route path="/nurseform" element={<NurseForm />} />
        </Routes>
    )
}

export default App