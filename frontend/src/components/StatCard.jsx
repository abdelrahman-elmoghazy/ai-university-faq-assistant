export default function StatCard({ label, value, icon, color, trend }) {
  const iconColors = {
    indigo: 'bg-indigo-500 shadow-indigo-500/20',
    violet: 'bg-violet-500 shadow-violet-500/20',
    emerald: 'bg-emerald-500 shadow-emerald-500/20',
    rose: 'bg-rose-500 shadow-rose-500/20',
    cyan: 'bg-cyan-500 shadow-cyan-500/20',
  }

  return (
    <div className="card-premium group">
      <div className="flex items-start justify-between mb-6">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl shadow-lg transition-transform duration-300 group-hover:scale-110 ${iconColors[color] || 'bg-slate-700'} text-white`}>
          {icon}
        </div>
        {trend && (
          <div className="px-2 py-1 rounded-md bg-white/5 border border-white/5 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
            {trend}
          </div>
        )}
      </div>
      <div>
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">{label}</p>
        <p className="text-4xl font-black text-white tracking-tight">{value}</p>
      </div>
    </div>
  )
}
