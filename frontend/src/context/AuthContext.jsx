import { useState, useEffect } from 'react'
import { authApi } from '../api/authApi'
import { AuthContext } from './AuthContext'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user')
      return stored ? JSON.parse(stored) : null
    } catch { return null }
  })
  const [loading, setLoading] = useState(false)

  // Sync user to localStorage
  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user))
    } else {
      localStorage.removeItem('user')
    }
  }, [user])

  const login = async (email, password) => {
    setLoading(true)
    try {
      const res = await authApi.login({ email, password })
      const { access_token, refresh_token, user: userData } = res.data
      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      setUser(userData)
      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.message || 'Login failed'
      return { success: false, error: msg }
    } finally {
      setLoading(false)
    }
  }

  const register = async (username, email, password, fullName) => {
    setLoading(true)
    try {
      await authApi.register({ username, email, password, full_name: fullName })
      return { success: true }
    } catch (err) {
      const msg = err.response?.data?.message || 'Registration failed'
      return { success: false, error: msg }
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try { 
      await authApi.logout() 
    } catch (error) {
      console.error("Logout error:", error)
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const isAdmin = user?.roles?.includes('admin')

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAdmin }}>
      {children}
    </AuthContext.Provider>
  )
}
