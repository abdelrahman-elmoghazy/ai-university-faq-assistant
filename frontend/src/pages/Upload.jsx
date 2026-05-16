import { useState, useEffect } from 'react'
import { fileApi } from '../api/fileApi'
import ErrorMessage from '../components/ErrorMessage'

export default function Upload() {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(true)
  const [verifyResults, setVerifyResults] = useState({})

  const loadFiles = async () => {
    try {
      const res = await fileApi.getMyFiles()
      // Safely unwrap response: res.data.files, res.data.documents, res.data.data, or res.data
      const rawData = res.data?.files || res.data?.documents || res.data?.data || (Array.isArray(res.data) ? res.data : [])
      setFiles(rawData)
      console.log("Vault Inventory synced:", rawData.length, "files found.")
    } catch (error) {
      console.error("Failed to sync vault inventory:", error)
    } 
    setLoading(false)
  }

  useEffect(() => {
    const init = async () => {
      await loadFiles()
    }
    init()
  }, [])

  const handleUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setError(''); setSuccess(''); setUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fileApi.upload(formData)
      
      // Extract file object from response (backend returns { file: { ... } })
      const newFile = res.data?.file || res.data?.data?.file || res.data?.files?.[0] || res.data?.data?.files?.[0]
      
      if (newFile) {
        setFiles(prev => [newFile, ...prev])
        setSuccess(`"${newFile.original_filename || newFile.file_name || 'Document'}" has been encrypted and stored.`)
      } else {
        setSuccess("File uploaded successfully.")
      }
      
      // Still refresh from server to ensure full sync
      loadFiles()
    } catch (err) {
      setError(err.response?.data?.message || 'Upload rejected.')
    }
    setUploading(false)
    e.target.value = ''
  }

  const handleVerify = async (fileId) => {
    setVerifyResults(prev => ({ ...prev, [fileId]: { loading: true } }))
    try {
      const res = await fileApi.verifyIntegrity(fileId)
      setVerifyResults(prev => ({ ...prev, [fileId]: res.data }))
    } catch {
      setVerifyResults(prev => ({ ...prev, [fileId]: { integrity_status: 'error', message: 'Failed' } }))
    }
  }

  return (
    <div className="animate-slide-up max-w-[1200px] mx-auto space-y-10">
      <header>
        <p className="text-violet-400 font-bold uppercase tracking-widest text-xs mb-2">Secure Infrastructure</p>
        <h1 className="heading-xl">Document Vault</h1>
        <p className="text-lg text-slate-400 mt-2">AES-128-CBC encryption with SHA-256 integrity verification.</p>
      </header>

      <ErrorMessage message={error} onClose={() => setError('')} />
      
      {success && (
        <div className="flex items-center gap-4 p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 animate-slide-up">
          <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center text-2xl shadow-lg shadow-emerald-500/20">✅</div>
          <span className="text-emerald-400 font-bold text-sm">{success}</span>
          <button onClick={() => setSuccess('')} className="ml-auto text-emerald-500 hover:text-emerald-400 px-2 font-bold">✕</button>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-8 items-start">
        {/* Upload Area */}
        <div className="xl:col-span-2">
          <div className="card-premium space-y-8 sticky top-10">
            <h2 className="heading-lg">New Upload</h2>
            
            <label className={`block cursor-pointer group relative ${uploading ? 'pointer-events-none' : ''}`}>
              <div className={`border-2 border-dashed border-white/5 rounded-3xl h-[220px] flex flex-col items-center justify-center transition-all group-hover:border-indigo-500/30 group-hover:bg-white/2 ${uploading ? 'bg-white/5' : ''}`}>
                {uploading ? (
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
                    <p className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Encrypting...</p>
                  </div>
                ) : (
                  <>
                    <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center text-4xl mb-4 shadow-xl group-hover:scale-110 transition-transform">📄</div>
                    <p className="text-xl font-bold text-white mb-1">Click to Upload</p>
                    <p className="text-xs text-slate-500 text-center">PDF, TXT, DOCX up to 10MB</p>
                  </>
                )}
              </div>
              <input type="file" accept=".pdf,.txt,.docx" onChange={handleUpload} className="hidden" />
            </label>

            <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5">
              <h3 className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-4">Vault Security</h3>
              <ul className="space-y-3">
                {['AES-128 Encryption', 'SHA-256 Verification', 'Secure Disk Commit'].map(rule => (
                  <li key={rule} className="flex items-center gap-3 text-slate-300 font-semibold text-sm">
                    <span className="text-indigo-500 text-lg">🛡️</span> {rule}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Inventory */}
        <div className="xl:col-span-3 space-y-6">
          <h2 className="heading-lg px-1">Vault Inventory ({files.length})</h2>
          
          {loading ? (
            <div className="flex justify-center py-20">
              <div className="w-10 h-10 border-4 border-white/5 border-t-indigo-500 rounded-full animate-spin"></div>
            </div>
          ) : files.length === 0 ? (
            <div className="card-premium p-16 text-center border-dashed border-white/5 bg-transparent">
              <p className="text-lg text-slate-600 font-bold">Secure vault is empty.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {files.map((f) => (
                <div key={f.id} className="card-premium group">
                  <div className="flex items-center gap-6 mb-6">
                    <div className="w-12 h-12 rounded-xl bg-slate-900 flex items-center justify-center text-3xl border border-white/5">
                      {f.mime_type?.includes('pdf') ? '📕' : '📄'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-lg font-bold text-white truncate">
                        {f.original_filename || f.file_name || f.title || 'Unnamed Document'}
                      </p>
                      <p className="text-xs text-slate-500">
                        {f.size_bytes ? `${(f.size_bytes / 1024).toFixed(1)} KB` : 'Size unknown'} • {f.created_at ? new Date(f.created_at).toLocaleDateString() : 'Date unknown'}
                      </p>
                    </div>
                    <div className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest border ${
                      (f.upload_status || f.status) === 'failed' 
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/10' 
                        : (f.upload_status || f.status) === 'completed' || (f.upload_status || f.status) === 'processed' || (f.upload_status || f.status) === 'uploaded'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/10'
                        : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/10 animate-pulse'
                    }`}>
                      {f.upload_status || f.status || 'Pending'}
                    </div>
                  </div>
                  
                  <div className="pt-6 border-t border-white/5 flex flex-col gap-4">
                    <div className="flex items-center justify-between">
                      <code className="text-[10px] font-mono text-slate-600 truncate max-w-[250px]">
                        HASH: {f.sha256_hash || 'SHA-256 Pending'}
                      </code>
                      <button 
                        onClick={() => handleVerify(f.id)} 
                        className="btn-premium !h-9 px-4 text-xs"
                      >
                        {verifyResults[f.id]?.loading ? (
                          <div className="w-3 h-3 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                        ) : 'Verify'}
                      </button>
                    </div>

                    {verifyResults[f.id] && !verifyResults[f.id].loading && (
                      <div className={`p-4 rounded-xl text-sm font-bold animate-slide-up border ${
                        verifyResults[f.id].integrity_status === 'valid' 
                          ? 'bg-emerald-500/5 text-emerald-400 border-emerald-500/10' 
                          : 'bg-rose-500/5 text-rose-400 border-rose-500/10'
                      }`}>
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{verifyResults[f.id].integrity_status === 'valid' ? '✅' : '❌'}</span>
                          <p>{verifyResults[f.id].message}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
