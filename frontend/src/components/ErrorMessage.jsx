export default function ErrorMessage({ message, onClose }) {
  if (!message) return null

  return (
    <div className="flex items-center gap-4 p-4 mb-6 rounded-2xl bg-rose-500/10 border border-rose-500/20 animate-in group">
      <div className="w-8 h-8 shrink-0 rounded-full bg-rose-500/20 flex items-center justify-center text-rose-500 font-bold">
        !
      </div>
      <p className="text-rose-400 text-sm font-semibold flex-1 leading-tight">{message}</p>
      {onClose && (
        <button 
          onClick={onClose} 
          className="w-8 h-8 flex items-center justify-center rounded-xl hover:bg-rose-500/20 text-rose-500 transition-colors"
        >
          ✕
        </button>
      )}
    </div>
  )
}
