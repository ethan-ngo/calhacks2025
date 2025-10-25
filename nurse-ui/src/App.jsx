import { Routes, Route } from 'react-router-dom'
import InputLoginPage from './pages/input_test'

function App() {
    return (
        <Routes>
            <Route path="/input_test" element={<InputLoginPage />} />
        </Routes>
    )
}

export default App