import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Sidebar() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: '📊' },
    { name: 'AI Assistant', path: '/chat', icon: '🤖' },
    { name: 'Secure Vault', path: '/upload', icon: '📁' },
  ]

  if (isAdmin) {
    navItems.push({ name: 'System Admin', path: '/admin', icon: '🛡️' })
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar-fixed flex flex-col shadow-xl">
      {/* Branding Section */}
      <div className="p-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-xl shadow-lg shadow-indigo-500/20">
            🎓
          </div>
          <div className="flex flex-col">
            <span className="font-bold text-lg text-white tracking-tight leading-none">UniFAQ</span>
            <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider mt-0.5">Assistant</span>
          </div>
        </div>
      </div>

      {/* Nav Section */}
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${
                isActive
                  ? 'bg-indigo-500 text-white font-semibold'
                  : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <span className="text-xl group-hover:scale-110 transition-transform">{item.icon}</span>
            <span className="text-sm">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* User / Profile Section */}
      <div className="p-6 border-t border-white/5">
        <div className="flex items-center gap-3 mb-4 px-1">
          <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center border border-white/5 text-lg">
            👤
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-white truncate">{user?.full_name || user?.username}</p>
            <p className="text-[9px] text-slate-500 uppercase font-black tracking-widest">{isAdmin ? 'admin' : 'user'}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 py-2 text-xs font-bold text-slate-400 hover:text-rose-400 hover:bg-rose-500/5 rounded-lg transition-all"
        >
          <span>🚪</span> Sign Out
        </button>
      </div>
    </aside>
  )
}
