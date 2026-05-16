import { useAuth } from '../hooks/useAuth'
import StatCard from '../components/StatCard'

export default function Dashboard() {
  const { user } = useAuth()

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

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <StatCard label="AI Questions" value="12" icon="💬" color="indigo" trend="+2 New" />
        <StatCard label="Protected Files" value="5" icon="🛡️" color="violet" trend="8.2 MB" />
        <StatCard label="System Security" value="100%" icon="✅" color="emerald" trend="Optimal" />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        {/* Primary Column */}
        <div className="xl:col-span-2 space-y-8">
          <section className="card-premium">
            <h2 className="heading-lg mb-8">Core Functions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <button className="flex items-center gap-5 p-6 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 hover:bg-indigo-500/10 hover:border-indigo-500/20 transition-all text-left group">
                <div className="w-12 h-12 rounded-xl bg-indigo-500 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">🤖</div>
                <div>
                  <p className="text-lg font-bold text-white">AI Assistant</p>
                  <p className="text-xs text-slate-400">Consult Knowledge Base</p>
                </div>
              </button>
              
              <button className="flex items-center gap-5 p-6 rounded-2xl bg-violet-500/5 border border-violet-500/10 hover:bg-violet-500/10 hover:border-violet-500/20 transition-all text-left group">
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
              <button className="text-xs font-bold text-indigo-400 hover:underline">View All</button>
            </div>
            <div className="space-y-3">
              {[1, 2].map(i => (
                <div key={i} className="flex items-center gap-5 p-4 rounded-xl bg-white/2 border border-white/5 hover:border-white/10 transition-all">
                  <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center text-xl">📕</div>
                  <div className="flex-1">
                    <p className="text-sm font-bold text-white">Enrollment_Guidelines_2026.pdf</p>
                    <p className="text-[10px] text-slate-500">Stored May 1{i}, 2026 • 2.4 MB</p>
                  </div>
                  <div className="px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-[9px] font-black uppercase tracking-widest">Encrypted</div>
                </div>
              ))}
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
                <p className="text-sm text-slate-300">Fernet encryption active on all disk commits.</p>
              </div>
              <div className="flex gap-3">
                <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0"></div>
                <p className="text-sm text-slate-300">Node synchronization successful.</p>
              </div>
            </div>
          </section>
          
          <div className="card-premium bg-gradient-to-br from-indigo-500/10 to-violet-500/10 border-indigo-500/20">
            <h3 className="text-lg font-bold text-white mb-2">Need Help?</h3>
            <p className="text-sm text-slate-400 mb-6">System documentation is available for all authorized users.</p>
            <button className="w-full btn-premium bg-white text-indigo-950 font-bold !h-10 text-xs uppercase tracking-widest">Open Docs</button>
          </div>
        </div>
      </div>
    </div>
  )
}
