import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020617] p-6 text-center">
      <div className="max-w-md animate-in">
        <div className="w-24 h-24 bg-slate-800 border border-slate-700 rounded-3xl flex items-center justify-center text-5xl mx-auto mb-8 shadow-2xl">
          🔍
        </div>
        <h1 className="text-4xl font-black tracking-tighter mb-4 text-white">404: Lost in Space</h1>
        <p className="text-slate-400 mb-10 leading-relaxed">
          The distributed node you are looking for does not exist or has been relocated to another cluster.
        </p>
        <Link to="/" className="btn-premium">
          Return to Mission Control
        </Link>
      </div>
    </div>
  )
}
