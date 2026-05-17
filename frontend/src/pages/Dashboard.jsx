import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { fileApi } from '../api/fileApi'
import { faqApi } from '../api/faqApi'
import StatCard from '../components/StatCard'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [files, setFiles] = useState([])
  const [questionsCount, setQuestionsCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        setError('')
        const [filesResult, faqResult] = await Promise.allSettled([
          fileApi.getMyFiles(),
          faqApi.getHistory()
        ])
        
        let hasRequestFailed = false
        let isRateLimited = false

        if (filesResult.status === 'fulfilled') {
          setFiles(filesResult.value?.data?.files || [])
        } else {
          console.warn('Failed to load files:', filesResult.reason)
          if (filesResult.reason?.response?.status === 429) {
            isRateLimited = true
          } else {
            const status = filesResult.reason?.response?.status
            if (!status || status >= 400) {
              hasRequestFailed = true
            }
          }
        }
        
        if (faqResult.status === 'fulfilled') {
          setQuestionsCount(faqResult.value?.data?.history?.length || 0)
        } else {
          console.warn('Failed to load history:', faqResult.reason)
          setQuestionsCount(0)
          if (faqResult.reason?.response?.status === 429) {
            isRateLimited = true
          }
        }

        if (isRateLimited) {
          setError('Too many requests. Please wait a moment and refresh.')
        } else if (hasRequestFailed) {
          setError('Failed to load some dashboard components. Using available data.')
        }
      } catch (err) {
        console.error('Unexpected error in dashboard data fetch:', err)
        setError('An unexpected error occurred.')
      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  const formatSize = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  // Filter out public documents that do not belong to the user
  const protectedFiles = files.filter(f => f.visibility !== 'public' || f.uploaded_by === user?.id)
  const totalBytes = protectedFiles.reduce((sum, f) => sum + (f.size_bytes || 0), 0)

  if (loading) return <Loading text="Syncing Security Node..." />

  return (
    <div className="animate-slide-up space-y-10">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <p className="text-indigo-400 font-bold uppercase tracking-widest text-xs mb-2">University System Node</p>
          <h1 className="heading-xl">
            Welcome, <span className="text-indigo-400">{user?.full_name}</span>
          </h1>
        </div>
        <div className="flex gap-3">
          <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/5 text-xs font-bold text-slate-400">
            Session: <span className="text-white">Secure</span>
          </div>
        </div>
      </header>

      {error && <ErrorMessage message={error} onClose={() => setError('')} />}

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <StatCard 
          label="AI Questions" 
          value={questionsCount.toString()} 
          icon="💬" 
          color="indigo" 
          trend="Total Interactions" 
        />
        <StatCard 
          label="Protected Files" 
          value={protectedFiles.length.toString()} 
          icon="🛡️" 
          color="violet" 
          trend={formatSize(totalBytes)} 
        />
        <StatCard 
          label="System Status" 
          value="Active" 
          icon="✅" 
          color="emerald" 
          trend="Encryption Verified" 
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Primary Column */}
        <div className="xl:col-span-2 space-y-8">
          <section className="card-premium">
            <h2 className="heading-lg mb-8">Core Functions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <button 
                onClick={() => navigate('/chat')}
                className="flex items-center gap-5 p-6 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 hover:bg-indigo-500/10 hover:border-indigo-500/20 transition-all text-left group"
              >
                <div className="w-12 h-12 rounded-xl bg-indigo-500 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">🤖</div>
                <div>
                  <p className="text-lg font-bold text-white">AI Assistant</p>
                  <p className="text-xs text-slate-400">Consult Knowledge Base</p>
                </div>
              </button>
              
              <button 
                onClick={() => navigate('/upload')}
                className="flex items-center gap-5 p-6 rounded-2xl bg-violet-500/5 border border-violet-500/10 hover:bg-violet-500/10 hover:border-violet-500/20 transition-all text-left group"
              >
                <div className="w-12 h-12 rounded-xl bg-violet-500 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">📤</div>
                <div>
                  <p className="text-lg font-bold text-white">Secure Vault</p>
                  <p className="text-xs text-slate-400">Encrypt Documents</p>
                </div>
              </button>
            </div>
          </section>

          <section className="card-premium">
            <div className="flex items-center justify-between mb-8">
              <h2 className="heading-lg">Protected Assets</h2>
              <button 
                onClick={() => navigate('/upload')}
                className="text-xs font-bold text-indigo-400 hover:underline"
              >
                Manage Files
              </button>
            </div>
            <div className="space-y-3">
              {protectedFiles.length > 0 ? (
                protectedFiles.slice(0, 5).map(file => (
                  <div key={file.id} className="flex items-center gap-5 p-4 rounded-xl bg-white/2 border border-white/5 hover:border-white/10 transition-all">
                    <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-xl">
                      {file.file_type?.includes('pdf') ? '📕' : file.file_type?.includes('doc') ? '📘' : '📄'}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-bold text-white truncate max-w-[200px] md:max-w-xs" title={file.original_filename || file.file_name}>
                        {file.original_filename || file.file_name}
                      </p>
                      <p className="text-[10px] text-slate-500">
                        Stored {new Date(file.created_at).toLocaleDateString()} • {formatSize(file.size_bytes)}
                      </p>
                    </div>
                    <div className="px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-[9px] font-black uppercase tracking-widest">
                      {file.status === 'processed' ? 'Encrypted' : file.status}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-10 text-slate-500 border border-dashed border-white/5 rounded-2xl">
                  <p className="text-sm">No protected files uploaded yet.</p>
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Sidebar Column */}
        <div className="space-y-8">
          <section className="card-premium">
            <h3 className="text-lg font-bold mb-6">Security Intelligence</h3>
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0"></div>
                <p className="text-sm text-slate-300">Fernet AES-256 encryption active.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0"></div>
                <p className="text-sm text-slate-300">Distributed RAG nodes synchronized.</p>
              </div>
            </div>
          </section>
          
          <div className="card-premium bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border-indigo-500/20">
            <h3 className="text-lg font-bold text-white mb-2">Need Help?</h3>
            <p className="text-sm text-slate-400 mb-6">Access the secure vault to manage your protected knowledge assets.</p>
            <button 
              onClick={() => navigate('/upload')}
              className="w-full btn-premium bg-white text-indigo-950 font-bold !h-10 text-xs uppercase tracking-widest"
            >
              Go to Vault
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
