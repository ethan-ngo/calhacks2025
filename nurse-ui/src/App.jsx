import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'
import NurseForm from './pages/nurse_form'

function App() {
    return (
        <Routes>
            <Route path="/input_test" element={<InputLoginPage />} />
            <Route path="/nurse_form" element={<NurseForm />} />
        </Routes>
    )
}

export default App