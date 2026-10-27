import React, { useState, useEffect } from 'react'
import { FileText, Copy, Check, AlertCircle, RefreshCw, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import { getDocumentPreview } from '../api/client'

export default function DocumentPreview({ documentId, documentName, onClose }) {
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const fetchPreview = async () => {
    if (!documentId) return
    setLoading(true)
    setError(null)
    try {
      const response = await getDocumentPreview(documentId)
      let textData = ''
      if (typeof response.data === 'string') {
        textData = response.data
      } else if (response.data?.text_preview) {
        textData = response.data.text_preview
      } else if (response.data?.text) {
        textData = response.data.text
      } else if (response.data?.content) {
        textData = response.data.content
      } else if (response.data?.preview) {
        textData = response.data.preview
      } else {
        textData = JSON.stringify(response.data, null, 2)
      }
      setContent(textData || 'No text extracted from this document.')
    } catch (err) {
      console.error('Failed to fetch document preview:', err)
      setError(err.message || 'Unable to retrieve document preview.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPreview()
  }, [documentId])

  const handleCopy = () => {
    if (!content) return
    navigator.clipboard.writeText(content)
    setCopied(true)
    toast.success('Document text copied to clipboard!')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-slate-900 text-white flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <Eye className="w-4 h-4 text-blue-400 flex-shrink-0" />
          <h4 className="text-sm font-semibold truncate text-slate-100">
            Document OCR Text: {documentName || `Doc ${documentId?.slice(0, 8)}`}
          </h4>
        </div>
        <div className="flex items-center gap-2">
          {content && !loading && (
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-slate-800 text-slate-200 hover:text-white hover:bg-slate-700 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Text'}</span>
            </button>
          )}
          <button
            type="button"
            onClick={fetchPreview}
            disabled={loading}
            title="Reload Preview"
            className="p-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
            >
              Close
            </button>
          )}
        </div>
      </div>

      {/* Body */}
      <div className="p-4 bg-slate-950 min-h-[220px] max-h-[460px] overflow-y-auto">
        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-2">
            <span className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></span>
            <span className="text-xs">Fetching OCR text streams...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-rose-950/60 border border-rose-800 rounded-lg text-rose-200 text-xs flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-semibold">Failed to load preview</p>
              <p className="text-rose-300 mt-0.5">{error}</p>
            </div>
          </div>
        ) : (
          <pre className="font-mono text-xs text-emerald-400 leading-relaxed whitespace-pre-wrap select-text">
            {content}
          </pre>
        )}
      </div>

      {/* Footer Info */}
      <div className="px-4 py-2 bg-slate-900 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
        <span>Raw text extracted via PyMuPDF / Tesseract OCR pipeline</span>
        <span>ID: {documentId}</span>
      </div>
    </div>
  )
}
