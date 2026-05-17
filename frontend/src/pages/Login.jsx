import { useState, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google'
import { useAuth } from '../hooks/useAuth'
import ErrorMessage from '../components/ErrorMessage'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID

function SocialButtons({ onLoading, onError }) {
  const { loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      onLoading(true)
      const result = await loginWithGoogle(tokenResponse.access_token)
      onLoading(false)
      
      if (result.success) {
        navigate(result.isAdmin ? '/admin' : '/dashboard')
      } else {
        onError(result.error || 'Google login failed')
      }
    },
    onError: (error) => {
      console.error('Google Login Failed:', error)
      onError('Google login failed. Please try again.')
    }
  })

  const handleGithubLogin = () => {
    const redirectUri = window.location.origin + '/login'
    const scope = 'user:email'
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${redirectUri}&scope=${scope}`
  }

  return (
    <div className="space-y-3">
      <button 
        type="button" 
        onClick={() => googleLogin()}
        className="btn-secondary w-full flex items-center justify-center gap-3 py-3 border border-white/10 rounded-xl hover:bg-white/5 transition-all group"
      >
        <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
          <path fill="#EA4335" d="M5.266 9.765A7.077 7.077 0 0 1 12 4.909c1.69 0 3.218.6 4.418 1.582L19.91 3C17.782 1.145 15.055 0 12 0 7.27 0 3.198 2.698 1.24 6.65l4.026 3.115Z" />
          <path fill="#34A853" d="M16.04 18.013c-1.09.61-2.42.987-4.04.987-2.91 0-5.387-1.93-6.382-4.594l-4.032 3.123C3.54 21.146 7.505 24 12 24c3.082 0 5.864-1.018 8.018-2.768l-3.978-3.219Z" />
          <path fill="#4285F4" d="M19.82 12c0-.72-.06-1.41-.17-2.072H12v4.145h4.39c-.19 1.011-.758 1.866-1.608 2.44l3.978 3.219C21.05 17.575 24 14.73 24 12c0-.72-.06-1.41-.17-2.072Z" />
          <path fill="#FBBC05" d="M5.658 14.406c-.25-.75-.39-1.556-.39-2.406s.14-1.656.39-2.406l-4.026-3.115C.44 8.217 0 10.05 0 12c0 1.95.44 3.783 1.242 5.526l4.032-3.12Z" />
        </svg>
        <span className="text-sm font-bold text-white">Continue with Google</span>
      </button>

      <button 
        type="button" 
        onClick={handleGithubLogin}
        className="btn-secondary w-full flex items-center justify-center gap-3 py-3 border border-white/10 rounded-xl hover:bg-white/5 transition-all group"
      >
        <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24" fill="white">
          <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
        </svg>
        <span className="text-sm font-bold text-white">Continue with GitHub</span>
      </button>
    </div>
  )
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, loginWithGithub } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Handle GitHub Redirect Callback
  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const code = params.get('code')
    
    if (code) {
      const performGithubLogin = async () => {
        setLoading(true)
        const result = await loginWithGithub(code)
        setLoading(false)
        
        if (result.success) {
          navigate(result.isAdmin ? '/admin' : '/dashboard')
        } else {
          setError(result.error || 'GitHub authentication failed')
          // Clear query params
          navigate('/login', { replace: true })
        }
      }
      performGithubLogin()
    }
  }, [location, loginWithGithub, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    const result = await login(email, password)
    setLoading(false)
    
    if (result.success) {
      navigate(result.isAdmin ? '/admin' : '/dashboard')
    } else {
      setError(result.error || 'Login failed. Please check credentials.')
    }
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#020617] p-6 relative overflow-hidden">
        {/* Background Decor */}
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-violet-500/10 rounded-full blur-[120px]"></div>

        <div className="w-full max-w-[420px] relative z-10 animate-slide-up">
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center text-3xl mx-auto mb-4 shadow-xl shadow-indigo-500/20">
              🎓
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight mb-2">Welcome Back</h1>
            <p className="text-slate-400">Authenticate to access the AI portal</p>
          </div>

          <div className="card-premium p-10 shadow-2xl">
            <ErrorMessage message={error} onClose={() => setError('')} />

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest px-1">Email Address</label>
                <input
                  type="email"
                  required
                  className="input-premium"
                  placeholder="name@university.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest px-1">Password</label>
                <input
                  type="password"
                  required
                  className="input-premium"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <button type="submit" disabled={loading} className="btn-premium w-full mt-2">
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/5"></div>
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-[#020617]/50 px-2 text-slate-500 font-bold tracking-widest">Or continue with</span>
              </div>
            </div>

            <SocialButtons onLoading={setLoading} onError={setError} />

            <div className="mt-8 pt-6 border-t border-white/5 text-center">
              <p className="text-sm text-slate-400">
                New here?{' '}
                <Link to="/register" className="text-indigo-400 hover:text-indigo-300 font-bold transition-colors">
                  Create Account
                </Link>
              </p>
            </div>
          </div>

          <p className="mt-8 text-center text-xs text-slate-600 font-bold uppercase tracking-widest">
            &copy; 2026 University AI • Secure Access
          </p>
        </div>
      </div>
    </GoogleOAuthProvider>
  )
}
