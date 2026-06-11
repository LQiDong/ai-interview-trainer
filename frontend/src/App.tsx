import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import JDInput from './pages/JDInput'
import Interview from './pages/Interview'
import Report from './pages/Report'
import EvalDashboard from './pages/EvalDashboard'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/jd-input" element={<JDInput />} />
        <Route path="/interview/:sessionId" element={<Interview />} />
        <Route path="/report/:sessionId" element={<Report />} />
        <Route path="/eval" element={<EvalDashboard />} />
      </Route>
    </Routes>
  )
}
