import { useState, useEffect } from 'react'
import { adminApi } from '../api/adminApi'
import StatCard from '../components/StatCard'
import ErrorMessage from '../components/ErrorMessage'

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('Overview')
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState([])
  const [queries, setQueries] = useState([])
  const [users, setUsers] = useState([])
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Filters
  const [logFilterAction, setLogFilterAction] = useState('')
  const [logFilterStatus, setLogFilterStatus] = useState('')

  const loadData = async () => {
    try {
      setLoading(true)
      const [sRes, lRes, qRes, uRes, fRes] = await Promise.allSettled([
        adminApi.getStats(),
        adminApi.getAuditLogs(50),
        adminApi.getRecentQueries(20),
        adminApi.getUsers(1),
        adminApi.getAllFiles()
      ])
      if (sRes.status === 'fulfilled') setStats(sRes.value.data.stats)
      if (lRes.status === 'fulfilled') setLogs(lRes.value.data.logs || [])
      if (qRes.status === 'fulfilled') setQueries(qRes.value.data.queries || [])
      if (uRes.status === 'fulfilled') setUsers(uRes.value.data.users || [])
      if (fRes.status === 'fulfilled') setFiles(fRes.value.data.files || [])
    } catch {
      setError('Authorization or connectivity error.')
    }
    setLoading(false)
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadData()
  }, [])

  const handleUpdateUserStatus = async (user) => {
    if (!window.confirm(`Are you sure you want to ${user.is_active ? 'deactivate' : 'activate'} user ${user.username}?`)) return
    try {
      await adminApi.updateUserStatus(user.id, !user.is_active)
      setSuccess(`User ${user.username} ${!user.is_active ? 'activated' : 'deactivated'}`)
      setError('')
      loadData()
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to update user status')
      setSuccess('')
    }
  }

  const handleToggleAdmin = async (user) => {
    const isAdmin = user.roles?.some(r => r.name === 'admin')
    if (!window.confirm(`Are you sure you want to ${isAdmin ? 'remove admin role from' : 'promote'} user ${user.username}?`)) return
    try {
      if (isAdmin) {
        await adminApi.revokeRole(user.id, 'admin')
        setSuccess(`Admin role removed from ${user.username}`)
      } else {
        await adminApi.assignRole(user.id, 'admin')
        setSuccess(`User ${user.username} promoted to admin`)
      }
      setError('')
      loadData()
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to change user role')
      setSuccess('')
    }
  }

  const handleDeleteFile = async (file) => {
    if (!window.confirm(`Are you sure you want to permanently delete file "${file.original_filename}"?`)) return
    try {
      await adminApi.deleteFile(file.id)
      setSuccess('File deleted successfully')
      setError('')
      loadData()
    } catch (e) {
      setError(e.response?.data?.message || 'Failed to delete file')
      setSuccess('')
    }
  }

  const formatSize = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  if (loading && !stats) return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <div className="w-12 h-12 border-4 border-white/5 border-t-indigo-500 rounded-full animate-spin"></div>
      <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Loading Console...</p>
    </div>
  )

  const filteredLogs = logs.filter(log => {
    if (logFilterAction && !log.action.includes(logFilterAction)) return false
    if (logFilterStatus && log.status !== logFilterStatus) return false
    return true
  })

  return (
    <div className="animate-slide-up space-y-10">
      <header className="flex items-start justify-between">
        <div>
          <p className="text-rose-400 font-bold uppercase tracking-widest text-[10px] mb-2">Administrator Console</p>
          <h1 className="heading-xl">Infrastructure Control</h1>
          <p className="text-lg text-slate-400 mt-2 max-w-2xl">Manage users, encrypted assets, and security audit trails.</p>
        </div>
        <div className="hidden lg:flex gap-3">
          <div className="card-premium py-2 px-6 bg-emerald-500/5 border-emerald-500/10">
            <p className="text-emerald-400 font-black uppercase text-[9px] tracking-widest mb-0.5">Status</p>
            <p className="text-lg font-bold text-white">Optimal</p>
          </div>
        </div>
      </header>

      {error && <ErrorMessage message={error} onClose={() => setError('')} />}
      {success && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm font-bold flex justify-between items-center">
          {success}
          <button onClick={() => setSuccess('')} className="text-emerald-400/50 hover:text-emerald-400">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/10 pb-4 overflow-x-auto">
        {['Overview', 'Users', 'Files', 'Audit Logs'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-3 text-sm font-bold rounded-lg transition-colors whitespace-nowrap ${
              activeTab === tab ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/20' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Overview' && (
        <div className="space-y-8 animate-fade-in">
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <StatCard label="Users" value={stats.total_users} icon="👥" color="indigo" />
              <StatCard label="Files" value={stats.total_files} icon="🛡️" color="violet" />
              <StatCard label="AI Queries" value={stats.total_queries} icon="💬" color="cyan" />
              <StatCard label="Security Alerts" value={stats.unauthorized_attempts + stats.failed_logins} icon="⚠️" color="rose" />
            </div>
          )}

          <section className="card-premium flex flex-col">
            <h2 className="heading-lg mb-8">Recent AI Processing</h2>
            <div className="space-y-4 flex-1 overflow-y-auto max-h-[400px] pr-2">
              {queries.length === 0 ? (
                <p className="text-center py-10 text-slate-600 font-bold">No activity.</p>
              ) : queries.map(q => (
                <div key={q.id} className="p-6 rounded-2xl bg-white/[0.01] border border-white/5 flex gap-4 items-start">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/5 flex items-center justify-center text-xl shrink-0">💬</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 font-medium leading-relaxed mb-3">"{q.question_text}"</p>
                    <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-slate-600">
                      <span>Node #{q.user_id}</span>
                      <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
                      <span>{new Date(q.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {activeTab === 'Users' && (
        <section className="card-premium !p-0 overflow-hidden animate-fade-in">
          <div className="p-8 border-b border-white/5 flex items-center justify-between">
            <h2 className="heading-lg">Access Management</h2>
            <button onClick={loadData} className="text-[10px] font-black text-indigo-400 hover:text-indigo-300 uppercase tracking-widest">Refresh</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-white/[0.02]">
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">User Identity</th>
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Role</th>
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Status</th>
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {users.map(u => {
                  const isAdmin = u.roles?.some(r => r.name === 'admin')
                  return (
                  <tr key={u.id} className="hover:bg-white/2">
                    <td className="px-6 py-4">
                      <p className="text-sm font-bold text-white">{u.username}</p>
                      <p className="text-xs text-slate-500">{u.email}</p>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-[10px] uppercase tracking-widest font-bold ${isAdmin ? 'bg-indigo-500/20 text-indigo-400' : 'bg-slate-800 text-slate-400'}`}>
                        {isAdmin ? 'Admin' : 'User'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-[10px] uppercase tracking-widest font-bold ${u.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                        {u.is_active ? 'Active' : 'Suspended'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => handleUpdateUserStatus(u)} className="btn-premium !py-1.5 !px-3 !h-auto text-[10px] border-white/10 hover:border-white/20">
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button onClick={() => handleToggleAdmin(u)} className="btn-premium !py-1.5 !px-3 !h-auto text-[10px] border-white/10 hover:border-white/20">
                          {isAdmin ? 'Demote' : 'Promote'}
                        </button>
                      </div>
                    </td>
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === 'Files' && (
        <section className="card-premium !p-0 overflow-hidden animate-fade-in">
          <div className="p-8 border-b border-white/5 flex items-center justify-between">
            <h2 className="heading-lg">Encrypted Assets</h2>
            <button onClick={loadData} className="text-[10px] font-black text-indigo-400 hover:text-indigo-300 uppercase tracking-widest">Refresh</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-white/[0.02]">
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">File Details</th>
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Owner</th>
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Size</th>
                  <th className="px-6 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {files.map(f => (
                  <tr key={f.id} className="hover:bg-white/2">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-bold text-white truncate max-w-[200px]" title={f.original_filename}>{f.original_filename}</p>
                        {f.visibility === 'public' && (
                          <span className="bg-emerald-500/20 text-emerald-400 text-[8px] font-black uppercase px-1.5 py-0.5 rounded border border-emerald-500/30">Public</span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-500">{new Date(f.created_at).toLocaleString()}</p>
                    </td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-400">Node-{f.uploaded_by}</td>
                    <td className="px-6 py-4 text-xs font-mono text-slate-400">{formatSize(f.size_bytes)}</td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => alert(`Metadata:\nType: ${f.mime_type}\nStatus: ${f.upload_status}\nEncrypted: ${f.encrypted}\nSHA-256: ${f.sha256_hash}`)} className="btn-premium !py-1.5 !px-3 !h-auto text-[10px] border-white/10">View</button>
                        <button onClick={() => handleDeleteFile(f)} className="btn-premium bg-rose-500/10 text-rose-400 !border-rose-500/20 hover:bg-rose-500/20 !py-1.5 !px-3 !h-auto text-[10px]">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === 'Audit Logs' && (
        <section className="card-premium !p-0 overflow-hidden flex flex-col animate-fade-in">
          <div className="p-8 border-b border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <h2 className="heading-lg">Security Audit Trail</h2>
            <div className="flex gap-3">
              <select className="bg-slate-900 border border-white/10 rounded-lg text-xs font-bold text-white px-3 py-2 outline-none focus:border-indigo-500" value={logFilterAction} onChange={e => setLogFilterAction(e.target.value)}>
                <option value="">All Actions</option>
                <option value="login">Login</option>
                <option value="upload">Upload</option>
                <option value="delete">Delete</option>
                <option value="update_user_status">Update Status</option>
                <option value="assign_role">Assign Role</option>
              </select>
              <select className="bg-slate-900 border border-white/10 rounded-lg text-xs font-bold text-white px-3 py-2 outline-none focus:border-indigo-500" value={logFilterStatus} onChange={e => setLogFilterStatus(e.target.value)}>
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
              </select>
              <button onClick={loadData} className="btn-premium !py-2 !px-4 !h-auto text-[10px] border-white/10">Refresh</button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-white/[0.02]">
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Event</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Status</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Details</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest text-right">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {filteredLogs.length === 0 ? (
                  <tr><td colSpan="4" className="px-8 py-10 text-center text-slate-600 font-bold">No telemetry matches filters.</td></tr>
                ) : filteredLogs.map(log => (
                  <tr key={log.id} className="hover:bg-white/2 transition-colors">
                    <td className="px-8 py-6">
                      <p className="text-sm font-bold text-slate-200 mb-0.5">{log.action}</p>
                      <p className="text-[10px] font-mono text-slate-600">Node-{log.user_id || 'System'}</p>
                    </td>
                    <td className="px-8 py-6">
                      <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${
                        log.status === 'success' ? 'bg-emerald-500/5 text-emerald-400' : 'bg-rose-500/5 text-rose-400'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="px-8 py-6">
                      <p className="text-[10px] font-mono text-slate-500 max-w-xs truncate" title={JSON.stringify(log.details)}>
                        {JSON.stringify(log.details)}
                      </p>
                    </td>
                    <td className="px-8 py-6 text-[11px] font-semibold text-slate-500 text-right whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
