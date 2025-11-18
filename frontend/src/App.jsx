import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Trials from './pages/Trials'
import Predictions from './pages/Predictions'
import Monitoring from './pages/Monitoring'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trials" element={<Trials />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/monitoring" element={<Monitoring />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
