import { useState, useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import AdminPage from './pages/AdminPage'
import DoctorPage from './pages/DoctorPage'
import PatientPage from './pages/PatientPage'

function App() {
  const [user, setUser] = useState(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const role = localStorage.getItem('role')
    const name = localStorage.getItem('name')
    const userId = localStorage.getItem('userId')
    if (token && role) {
      setUser({ token, role, name, userId: parseInt(userId) })
    }
  }, [])

  const handleLogin = (userData) => {
    localStorage.setItem('token', userData.token)
    localStorage.setItem('role', userData.role)
    localStorage.setItem('name', userData.name)
    localStorage.setItem('userId', userData.userId)
    setUser(userData)
  }

  const handleLogout = () => {
    localStorage.clear()
    setUser(null)
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />
  }

  const renderPage = () => {
    switch (user.role) {
      case 'Admin':   return <AdminPage user={user} onLogout={handleLogout} />
      case 'Doctor':  return <DoctorPage user={user} onLogout={handleLogout} />
      case 'Patient': return <PatientPage user={user} onLogout={handleLogout} />
      default: return <div>Unknown role</div>
    }
  }

  return renderPage()
}

export default App
