import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
// Ensure baseURL is relative if API_BASE is empty
const axiosClient = axios.create({
  baseURL: API_BASE ? (API_BASE.endsWith('/') ? `${API_BASE}api` : `${API_BASE}/api`) : '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})
console.log('Axios Client Initialized. BaseURL:', axiosClient.defaults.baseURL)

// Request interceptor — attach JWT token
axiosClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — handle 401
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default axiosClient
