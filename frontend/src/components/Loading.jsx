export default function Loading({ text = 'Loading...' }) {
  return (
    <div className="min-h-[400px] flex flex-col items-center justify-center gap-6 animate-in">
      <div className="relative">
        <div className="w-16 h-16 border-4 border-indigo-500/20 rounded-full"></div>
        <div className="w-16 h-16 border-4 border-transparent border-t-indigo-500 rounded-full animate-spin absolute top-0 left-0"></div>
        <div className="w-16 h-16 border-4 border-transparent border-b-violet-500 rounded-full animate-spin absolute top-0 left-0 [animation-duration:1.5s] opacity-50"></div>
      </div>
      <div className="flex flex-col items-center gap-1">
        <p className="text-slate-50 font-bold tracking-tight">{text}</p>
        <p className="text-[10px] text-slate-500 uppercase font-black tracking-[0.3em]">Processing Distributed Request</p>
      </div>
    </div>
  )
}
