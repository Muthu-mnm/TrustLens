import React, { useState, useEffect } from 'react'
import { X, CheckCircle, AlertCircle, HelpCircle, User, MessageSquare } from 'lucide-react'
import toast from 'react-hot-toast'
import { reviewFinding } from '../../api/client'

export default function ReviewModal({ isOpen, finding, onClose, onReviewSuccess }) {
  const [reviewStatus, setReviewStatus] = useState('reviewed')
  const [reviewedBy, setReviewedBy] = useState('AICTE Scrutiny Officer')
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (finding) {
      setReviewStatus(finding.review_status && finding.review_status !== 'pending' ? finding.review_status : 'reviewed')
      setComment(finding.review_comment || '')
    }
  }, [finding])

  if (!isOpen || !finding) return null

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!reviewedBy.trim()) {
      toast.error('Please enter the officer name or ID')
      return
    }

    if (reviewStatus === 'dismissed' && !comment.trim()) {
      toast.error('Dismissing a finding requires an explanatory justification comment.')
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        review_status: reviewStatus,
        comment: comment.trim(),
        reviewed_by: reviewedBy.trim(),
      }

      const response = await reviewFinding(finding.id, payload)
      toast.success('Finding review recorded successfully!')
      if (onReviewSuccess) {
        onReviewSuccess(finding.id, response.data || payload)
      }
      onClose()
    } catch (err) {
      console.error('Error submitting review:', err)
      toast.error(err.message || 'Failed to submit finding review.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-blue-600/30 text-blue-400 border border-blue-500/30">
              <CheckCircle className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Officer Finding Review</h3>
              <p className="text-xs text-slate-300">ID: {finding.id}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Finding Summary Callout */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
            <span className="text-[11px] font-semibold uppercase text-slate-500">Finding Subject</span>
            <p className="text-sm font-semibold text-slate-800">{finding.title}</p>
            {finding.field_name && (
              <p className="text-xs text-slate-600">
                Target Field: <code className="font-mono bg-slate-200 px-1 rounded">{finding.field_name}</code>
              </p>
            )}
            <div className="pt-1 flex items-center gap-2 text-xs text-slate-500">
              <span>Severity: <strong className="capitalize">{finding.severity}</strong></span>
              <span>•</span>
              <span>Current Status: <strong className="capitalize">{finding.review_status || 'Pending'}</strong></span>
            </div>
          </div>

          {/* Review Decision / Status */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Review Decision <span className="text-rose-500">*</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setReviewStatus('reviewed')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  reviewStatus === 'reviewed'
                    ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-sm ring-1 ring-emerald-400'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <CheckCircle className="w-4 h-4 mb-1 text-emerald-600" />
                <span>Reviewed</span>
              </button>

              <button
                type="button"
                onClick={() => setReviewStatus('clarification_needed')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  reviewStatus === 'clarification_needed'
                    ? 'bg-purple-50 border-purple-500 text-purple-800 shadow-sm ring-1 ring-purple-400'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <HelpCircle className="w-4 h-4 mb-1 text-purple-600" />
                <span>Clarify</span>
              </button>

              <button
                type="button"
                onClick={() => setReviewStatus('dismissed')}
                className={`flex flex-col items-center justify-center p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                  reviewStatus === 'dismissed'
                    ? 'bg-rose-50 border-rose-500 text-rose-800 shadow-sm ring-1 ring-rose-400'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <AlertCircle className="w-4 h-4 mb-1 text-rose-600" />
                <span>Dismiss</span>
              </button>
            </div>
            {reviewStatus === 'dismissed' && (
              <p className="mt-1.5 text-xs text-rose-600 font-medium">
                * Note: Justification required below for audit trails when dismissing a system finding.
              </p>
            )}
          </div>

          {/* Reviewed By */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Reviewing Officer <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                required
                value={reviewedBy}
                onChange={(e) => setReviewedBy(e.target.value)}
                placeholder="e.g., Dr. R. Sharma (AICTE Scrutiny Committee)"
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Comment / Justification */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Officer Observations & Justification {reviewStatus === 'dismissed' && <span className="text-rose-500">*</span>}
            </label>
            <div className="relative">
              <MessageSquare className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <textarea
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder={
                  reviewStatus === 'dismissed'
                    ? 'Provide mandatory justification why this finding was dismissed...'
                    : 'Add officer verification notes, clarification questions, or cross-checks...'
                }
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Modal Footer */}
          <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-3">
            <button
              type="button"
              disabled={submitting}
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold bg-blue-700 text-white hover:bg-blue-800 disabled:opacity-50 transition-all shadow-sm"
            >
              {submitting ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  <span>Saving...</span>
                </>
              ) : (
                <span>Confirm Decision</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
