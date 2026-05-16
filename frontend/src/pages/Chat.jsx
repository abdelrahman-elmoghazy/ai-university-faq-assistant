import { useState, useEffect, useRef } from 'react'
import { faqApi } from '../api/faqApi'

export default function Chat() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const scrollRef = useRef(null)

  const loadHistory = async () => {
    try {
      const res = await faqApi.getHistory()
      setHistory(res.data.history || [])
    } catch (error) {
      console.error("Failed to load history:", error)
    }
    setInitialLoading(false)
  }

  useEffect(() => {
    const init = async () => {
      await loadHistory()
    }
    init()
  }, [])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [history])

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    
    const userQ = question
    setQuestion('')
    setLoading(true)
    setHistory(prev => [...prev, { question_text: userQ, answer_text: '...', id: Date.now() }])
    
    try {
      const res = await faqApi.askQuestion({ question_text: userQ })
      const data = res?.data || res
      console.log("FAQ ask response:", data)

      const answerText =
        data?.answer?.answer_text ||
        data?.answer_text ||
        (typeof data?.answer === "string" ? data.answer : null) ||
        data?.message ||
        "No answer returned."

      setHistory(prev => prev.map(item => 
        item.question_text === userQ && item.answer_text === '...' 
          ? { ...item, answer_text: answerText } 
          : item
      ))
    } catch (error) {
      console.error("FAQ ask failed:", error.response?.data || error.message)
      setHistory(prev => prev.map(item => 
        item.question_text === userQ && item.answer_text === '...' 
          ? { ...item, answer_text: 'Communication error with AI node.' } 
          : item
      ))
    }
    setLoading(false)
  }

  return (
    <div className="animate-slide-up flex flex-col h-[calc(100vh-5rem)]">
      {/* Header */}
      <div className="max-w-[900px] w-full mx-auto mb-8 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="heading-lg">AI Assistant</h1>
            <p className="text-sm text-slate-400">Natural Language Knowledge Query</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/10">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest">Active</span>
          </div>
        </div>
      </div>

      {/* Main Conversation Area */}
      <div className="flex-1 min-h-0 max-w-[900px] w-full mx-auto relative flex flex-col bg-white/[0.01] border-x border-white/5 px-8">
        <div 
          ref={scrollRef}
          className="flex-1 overflow-y-auto pr-2 space-y-8 py-8"
        >
          {initialLoading ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-500">
              <div className="w-12 h-12 border-4 border-white/5 border-t-indigo-500 rounded-full animate-spin"></div>
              <p className="font-bold text-sm">Synchronizing Node...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-10">
              <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center text-3xl mb-6 border border-white/5">🤖</div>
              <h3 className="heading-lg mb-3">Welcome to University AI</h3>
              <p className="text-base text-slate-400 max-w-md mx-auto mb-8">
                How can I assist you today? Ask about admissions, housing, or campus life.
              </p>
              <div className="grid grid-cols-2 gap-3 w-full max-w-xl">
                {['Admission requirements', 'Tuition fees', 'Campus security', 'IT Support'].map(topic => (
                  <button 
                    key={topic}
                    onClick={() => setQuestion(topic)}
                    className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-indigo-500/30 hover:bg-white/10 transition-all text-sm text-slate-300"
                  >
                    "{topic}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            history.map((msg) => (
              <div key={msg.id} className="flex flex-col gap-4 animate-slide-up">
                <div className="flex justify-end">
                  <div className="bg-indigo-600 text-white p-4 rounded-2xl rounded-br-none max-w-[80%] text-[15px] shadow-lg">
                    {msg.question_text}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-white/5 border border-white/10 text-slate-100 p-5 rounded-2xl rounded-bl-none max-w-[85%] text-[15px] leading-relaxed">
                    {msg.answer_text === '...' ? (
                      <div className="flex gap-1.5 py-1">
                        <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                        <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce"></div>
                      </div>
                    ) : (
                      msg.answer_text
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input Bar */}
        <div className="py-8 bg-[#020617]">
          <form onSubmit={handleAsk} className="relative group">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              disabled={loading}
              className="w-full h-14 bg-slate-900 border border-white/10 rounded-2xl px-6 pr-28 text-base text-white outline-none focus:border-indigo-500/30 transition-all"
            />
            <div className="absolute right-2 top-2 bottom-2 flex items-center">
              <button 
                type="submit" 
                disabled={loading || !question.trim()}
                className="btn-premium h-full px-6 text-sm"
              >
                {loading ? '...' : 'Send'}
              </button>
            </div>
          </form>
          <p className="text-[9px] text-center text-slate-700 mt-4 font-bold uppercase tracking-[0.3em]">
            Distributed AI Cluster • v2.1
          </p>
        </div>
      </div>
    </div>
  )
}
