import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import Upload from './pages/Upload'
import AdminDashboard from './pages/AdminDashboard'
import Forbidden from './pages/Forbidden'
import NotFound from './pages/NotFound'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'

/**
 * MainLayout ensures the Sidebar and Content are perfectly aligned without overlapping.
 * The Sidebar has a fixed width (260px) and the main area takes the rest.
 */
const MainLayout = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-[#020617]">
      <Sidebar />
      <main className="main-content">
        <div className="container-premium">
          {children}
        </div>
      </main>
    </div>
  )
}

function App() {
  const { user, loading, isAdmin } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#020617]">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
          <p className="text-slate-400 font-medium">Initializing system...</p>
        </div>
      </div>
    )
  }

  return (
    <Routes>
      {/* Public Auth Pages — Full Screen, No Sidebar */}
      <Route path="/login" element={!user ? <Login /> : <Navigate to={isAdmin ? "/admin" : "/dashboard"} />} />
      <Route path="/register" element={!user ? <Register /> : <Navigate to={isAdmin ? "/admin" : "/dashboard"} />} />

      {/* Protected Pages — Integrated Sidebar Layout */}
      <Route path="/dashboard" element={<ProtectedRoute><MainLayout><Dashboard /></MainLayout></ProtectedRoute>} />
      <Route path="/chat" element={<ProtectedRoute><MainLayout><Chat /></MainLayout></ProtectedRoute>} />
      <Route path="/upload" element={<ProtectedRoute><MainLayout><Upload /></MainLayout></ProtectedRoute>} />
      
      {/* Admin Protected Pages */}
      <Route path="/admin" element={<AdminRoute><MainLayout><AdminDashboard /></MainLayout></AdminRoute>} />

      {/* Error Pages */}
      <Route path="/forbidden" element={<Forbidden />} />
      <Route path="/" element={<Navigate to={isAdmin ? "/admin" : "/dashboard"} />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App
