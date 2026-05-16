import { Link } from 'react-router-dom'

export default function Forbidden() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020617] p-6 text-center">
      <div className="max-w-md animate-in">
        <div className="w-24 h-24 bg-rose-500/10 border border-rose-500/20 rounded-3xl flex items-center justify-center text-5xl mx-auto mb-8 shadow-2xl">
          🚫
        </div>
        <h1 className="text-4xl font-black tracking-tighter mb-4 text-white">403: Restricted Area</h1>
        <p className="text-slate-400 mb-10 leading-relaxed">
          Your current security clearance (role) does not permit access to this module. Please contact the administrator if you believe this is an error.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/dashboard" className="btn-premium">
            Back to Dashboard
          </Link>
          <Link to="/chat" className="px-6 py-3 rounded-xl border border-slate-700 hover:bg-slate-800 transition-all font-bold text-sm text-slate-300">
            Talk to AI
          </Link>
        </div>
      </div>
    </div>
  )
}
