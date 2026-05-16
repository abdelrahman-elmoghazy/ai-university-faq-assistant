import { useState, useEffect } from 'react'
import { adminApi } from '../api/adminApi'
import StatCard from '../components/StatCard'
import ErrorMessage from '../components/ErrorMessage'

export default function AdminDashboard() {
  const [stats, setStats] = useState(null)
  const [logs, setLogs] = useState([])
  const [queries, setQueries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const [sRes, lRes, qRes] = await Promise.allSettled([
          adminApi.getStats(),
          adminApi.getAuditLogs(20),
          adminApi.getRecentQueries(10),
        ])
        if (sRes.status === 'fulfilled') setStats(sRes.value.data.stats)
        if (lRes.status === 'fulfilled') setLogs(lRes.value.data.logs || [])
        if (qRes.status === 'fulfilled') setQueries(qRes.value.data.queries || [])
      } catch {
        setError('Authorization or connectivity error.')
      }
      setLoading(false)
    }
    load()
  }, [])

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <div className="w-12 h-12 border-4 border-white/5 border-t-indigo-500 rounded-full animate-spin"></div>
      <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Loading Console...</p>
    </div>
  )

  return (
    <div className="animate-slide-up space-y-10">
      <header className="flex items-start justify-between">
        <div>
          <p className="text-rose-400 font-bold uppercase tracking-widest text-[10px] mb-2">Administrator Console</p>
          <h1 className="heading-xl">Infrastructure</h1>
          <p className="text-lg text-slate-400 mt-2 max-w-2xl">Real-time monitoring of AI nodes and security audit trails.</p>
        </div>
        <div className="hidden lg:flex gap-3">
          <div className="card-premium py-2 px-6 bg-emerald-500/5 border-emerald-500/10">
            <p className="text-emerald-400 font-black uppercase text-[9px] tracking-widest mb-0.5">Status</p>
            <p className="text-lg font-bold text-white">Optimal</p>
          </div>
          <div className="card-premium py-2 px-6 bg-indigo-500/5 border-indigo-500/10">
            <p className="text-indigo-400 font-black uppercase text-[9px] tracking-widest mb-0.5">Version</p>
            <p className="text-lg font-bold text-white">v2.1</p>
          </div>
        </div>
      </header>

      <ErrorMessage message={error} onClose={() => setError('')} />

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          <StatCard label="Users" value={stats.total_users} icon="👥" color="indigo" />
          <StatCard label="Files" value={stats.total_files} icon="🛡️" color="violet" />
          <StatCard label="AI Queries" value={stats.total_queries} icon="💬" color="cyan" />
          <StatCard label="Security" value={stats.unauthorized_attempts + stats.failed_logins} icon="⚠️" color="rose" />
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Audit Logs */}
        <section className="card-premium !p-0 overflow-hidden flex flex-col">
          <div className="p-8 border-b border-white/5 flex items-center justify-between">
            <h2 className="heading-lg">Audit Trail</h2>
            <button className="text-[10px] font-black text-indigo-400 hover:text-indigo-300 transition-colors uppercase tracking-[0.2em]">Live Logs</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-white/[0.02]">
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Event</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Status</th>
                  <th className="px-8 py-4 text-[10px] font-black text-slate-500 uppercase tracking-widest">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {logs.length === 0 ? (
                  <tr><td colSpan="3" className="px-8 py-10 text-center text-slate-600 font-bold">No telemetry.</td></tr>
                ) : logs.map(log => (
                  <tr key={log.id} className="hover:bg-white/2 transition-colors">
                    <td className="px-8 py-6">
                      <p className="text-sm font-bold text-slate-200 mb-0.5">{log.action}</p>
                      <p className="text-[10px] font-mono text-slate-600">node-{log.user_id || '0'}</p>
                    </td>
                    <td className="px-8 py-6">
                      <div className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${
                        log.status === 'success' ? 'bg-emerald-500/5 text-emerald-400' : 'bg-rose-500/5 text-rose-400'
                      }`}>
                        {log.status}
                      </div>
                    </td>
                    <td className="px-8 py-6 text-[11px] font-semibold text-slate-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* AI Stream */}
        <section className="card-premium flex flex-col">
          <h2 className="heading-lg mb-8">AI Processing</h2>
          <div className="space-y-4 flex-1 overflow-y-auto max-h-[600px] pr-2">
            {queries.length === 0 ? (
              <p className="text-center py-10 text-slate-600 font-bold">No activity.</p>
            ) : queries.map(q => (
              <div key={q.id} className="p-6 rounded-2xl bg-white/[0.01] border border-white/5 hover:border-white/10 transition-all flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/5 flex items-center justify-center text-xl shrink-0">💬</div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200 font-medium leading-relaxed mb-3">"{q.question_text}"</p>
                  <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-widest text-slate-600">
                    <span>ID #{q.user_id}</span>
                    <span className="w-1 h-1 bg-slate-700 rounded-full"></span>
                    <span>{new Date(q.created_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
