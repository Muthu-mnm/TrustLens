import React, { useState } from 'react'
import { format, parseISO } from 'date-fns'
import { Clock, ShieldCheck, UserCheck, FileUp, Sparkles, AlertCircle, FileText, Lock, CheckCircle2, ShieldAlert } from 'lucide-react'
import { verifyAudit } from '../../api/client'
import toast from 'react-hot-toast'

export default function AuditTrail({ auditEntries = [], applicationId }) {
  const [verifying, setVerifying] = useState(false)
  const [verificationResult, setVerificationResult] = useState(null)

  const handleVerifyChain = async () => {
    if (!applicationId) {
      toast.error('Application ID not available for chain verification')
      return
    }
    setVerifying(true)
    try {
      const res = await verifyAudit(applicationId)
      setVerificationResult(res.data)
      if (res.data?.chain_valid) {
        toast.success(`Audit chain verified intact! (${res.data.total_entries} records verified)`)
      } else {
        toast.error('Audit chain verification failed: possible tampering detected!')
      }
    } catch (err) {
      toast.error(err.message || 'Audit verification request failed')
    } finally {
      setVerifying(false)
    }
  }

  const getActionStyle = (action = '') => {
    const act = action.toUpperCase()
    if (act.includes('CREATED') || act.includes('INITIAL')) {
      return {
        badge: 'bg-blue-100 text-blue-800 border-blue-300',
        dot: 'bg-blue-600',
        icon: ShieldCheck,
      }
    }
    if (act.includes('UPLOAD')) {
      return {
        badge: 'bg-indigo-100 text-indigo-800 border-indigo-300',
        dot: 'bg-indigo-600',
        icon: FileUp,
      }
    }
    if (act.includes('ANALYSIS') || act.includes('ANALYZE')) {
      return {
        badge: 'bg-purple-100 text-purple-800 border-purple-300',
        dot: 'bg-purple-600',
        icon: Sparkles,
      }
    }
    if (act.includes('REVIEW') || act.includes('DECISION')) {
      return {
        badge: 'bg-emerald-100 text-emerald-800 border-emerald-300',
        dot: 'bg-emerald-600',
        icon: UserCheck,
      }
    }
    if (act.includes('REPORT') || act.includes('DOWNLOAD')) {
      return {
        badge: 'bg-amber-100 text-amber-800 border-amber-300',
        dot: 'bg-amber-600',
        icon: FileText,
      }
    }
    return {
      badge: 'bg-slate-100 text-slate-800 border-slate-300',
      dot: 'bg-slate-600',
      icon: Clock,
    }
  }

  const formatTimestamp = (ts) => {
    if (!ts) return 'Unknown timestamp'
    try {
      const parsed = typeof ts === 'string' ? parseISO(ts) : new Date(ts)
      if (isNaN(parsed.getTime())) return String(ts)
      return format(parsed, 'PPpp') // e.g. "Apr 29, 2024, 5:30 PM"
    } catch {
      return String(ts)
    }
  }

  // Sort newest first
  const sortedEntries = [...(auditEntries || [])].sort((a, b) => {
    const dateA = new Date(a.timestamp || 0).getTime()
    const dateB = new Date(b.timestamp || 0).getTime()
    return dateB - dateA
  })

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Lock className="w-4 h-4 text-slate-700" />
            Append-Only Audit Trail
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Cryptographic SHA-256 hash-chained record of scrutiny actions, uploads, and officer decisions.
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {applicationId && (
            <button
              type="button"
              onClick={handleVerifyChain}
              disabled={verifying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
            >
              <ShieldCheck className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : 'text-emerald-400'}`} />
              <span>{verifying ? 'Verifying...' : 'Verify Hash Chain'}</span>
            </button>
          )}
          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200">
            <span>Entries:</span>
            <span className="font-bold text-slate-800">{sortedEntries.length}</span>
          </div>
        </div>
      </div>

      {/* Verification Status Banner (if checked) */}
      {verificationResult && (
        <div
          className={`p-3.5 rounded-xl border flex items-center justify-between text-xs transition-all ${
            verificationResult.chain_valid
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {verificationResult.chain_valid ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            ) : (
              <ShieldAlert className="w-4 h-4 text-rose-600 flex-shrink-0" />
            )}
            <div>
              <span className="font-bold">
                {verificationResult.chain_valid ? 'Cryptographic Integrity Confirmed:' : 'Integrity Failure:'}
              </span>{' '}
              <span>{verificationResult.message}</span>
            </div>
          </div>
          <span className="text-[11px] font-mono opacity-80">
            {verificationResult.verified_entries}/{verificationResult.total_entries} Blocks Intact
          </span>
        </div>
      )}

      {/* Empty State */}
      {sortedEntries.length === 0 ? (
        <div className="py-12 text-center text-slate-400 space-y-2">
          <Clock className="w-8 h-8 mx-auto text-slate-300" />
          <p className="text-sm font-medium">No audit entries recorded yet for this application.</p>
        </div>
      ) : (
        /* Timeline List */
        <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
          {sortedEntries.map((entry, index) => {
            const style = getActionStyle(entry.action)
            const Icon = style.icon

            let detailsString = entry.details
            if (typeof detailsString === 'object') {
              try {
                detailsString = JSON.stringify(detailsString, null, 2)
              } catch {
                detailsString = String(detailsString)
              }
            }

            const currentHash = entry.entry_hash || entry.hash
            const prevHash = entry.previous_hash || entry.prev_hash

            return (
              <div key={entry.id || index} className="relative group">
                {/* Timeline Dot */}
                <span
                  className={`absolute -left-[1.85rem] top-1.5 w-4 h-4 rounded-full border-2 border-white ring-2 ring-slate-200 ${style.dot} transition-transform group-hover:scale-110 flex items-center justify-center`}
                />

                {/* Entry Card */}
                <div className="bg-slate-50/80 rounded-xl p-4 border border-slate-200/80 transition-all hover:bg-slate-50 hover:border-slate-300 space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    {/* Action Tag & Actor */}
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style.badge}`}
                      >
                        <Icon className="w-3.5 h-3.5" />
                        {entry.action || 'ACTION_LOGGED'}
                      </span>
                      <span className="text-xs font-medium text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                        Actor: <strong className="text-slate-900">{entry.actor || 'System'}</strong>
                      </span>
                    </div>

                    {/* Timestamp Pill */}
                    <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {formatTimestamp(entry.timestamp)}
                    </span>
                  </div>

                  {/* Details */}
                  {detailsString && (
                    <div className="text-xs text-slate-700 font-sans leading-relaxed pt-1">
                      {typeof entry.details === 'object' ? (
                        <pre className="p-2 bg-slate-900 text-slate-200 text-[11px] font-mono rounded overflow-x-auto">
                          {detailsString}
                        </pre>
                      ) : (
                        <p>{detailsString}</p>
                      )}
                    </div>
                  )}

                  {/* Cryptographic hash info */}
                  {(currentHash || prevHash) && (
                    <div className="pt-2 border-t border-slate-200/60 flex flex-wrap items-center gap-3 text-[10px] text-slate-500 font-mono">
                      {currentHash && (
                        <span>
                          <strong className="text-slate-700">Hash:</strong> {currentHash.slice(0, 16)}...
                        </span>
                      )}
                      {prevHash && (
                        <span>
                          <strong className="text-slate-700">Prev:</strong> {prevHash.slice(0, 16)}...
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Audit Footnote */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 bg-slate-50 -mx-6 -mb-6 p-4 rounded-b-xl border">
        <div className="flex items-center gap-2">
          <Lock className="w-3.5 h-3.5 text-slate-400" />
          <span>
            Audit trail is append-only and hash-chained (simplified). Not a full blockchain.
          </span>
        </div>
        <span className="text-[11px] font-medium text-slate-400">Section 26 AICTE Compliance</span>
      </div>
    </div>
  )
}
