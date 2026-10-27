import React from 'react'
import {
  AlertCircle,
  AlertTriangle,
  Info,
  CheckCircle2,
  FileText,
  Bookmark,
  MessageSquare,
  ChevronRight,
  ShieldAlert,
} from 'lucide-react'

export default function FindingCard({ finding, onReview }) {
  if (!finding) return null

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return {
          bg: 'bg-rose-50 border-rose-200 text-rose-700',
          dot: 'bg-rose-600',
          label: 'Critical',
          icon: ShieldAlert,
        }
      case 'high':
        return {
          bg: 'bg-orange-50 border-orange-200 text-orange-700',
          dot: 'bg-orange-500',
          label: 'High',
          icon: AlertTriangle,
        }
      case 'medium':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-700',
          dot: 'bg-amber-500',
          label: 'Medium',
          icon: AlertCircle,
        }
      case 'low':
        return {
          bg: 'bg-blue-50 border-blue-200 text-blue-700',
          dot: 'bg-blue-500',
          label: 'Low',
          icon: Info,
        }
      case 'info':
      default:
        return {
          bg: 'bg-slate-100 border-slate-200 text-slate-700',
          dot: 'bg-slate-400',
          label: 'Info',
          icon: Info,
        }
    }
  }

  const getReviewStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case 'reviewed':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      case 'dismissed':
        return 'bg-slate-100 text-slate-600 border-slate-300 line-through'
      case 'clarification_needed':
        return 'bg-purple-100 text-purple-800 border-purple-300'
      case 'pending':
      default:
        return 'bg-amber-50 text-amber-800 border-amber-300'
    }
  }

  const formatFindingType = (type) => {
    if (!type) return 'Anomaly'
    return type
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  }

  const sevStyle = getSeverityBadge(finding.severity)
  const SevIcon = sevStyle.icon

  return (
    <div className="bg-white rounded-xl border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
      {/* Top Banner / Tags */}
      <div className="px-5 py-3 bg-slate-50/70 border-b border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Badge */}
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full font-semibold border ${sevStyle.bg}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${sevStyle.dot}`}></span>
            <SevIcon className="w-3.5 h-3.5" />
            <span>{sevStyle.label}</span>
          </span>

          {/* Finding Type Chip */}
          <span className="inline-flex items-center px-2 py-0.5 rounded-md font-medium bg-slate-100 text-slate-700 border border-slate-200">
            {formatFindingType(finding.finding_type)}
          </span>

          {/* Rule ID Badge */}
          {finding.rule_id && (
            <span className="inline-flex items-center gap-1 font-mono text-[11px] px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              <Bookmark className="w-3 h-3 text-blue-500" />
              {finding.rule_id}
            </span>
          )}
        </div>

        {/* Review Status Badge */}
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize border ${getReviewStatusBadge(
              finding.review_status
            )}`}
          >
            Status: {finding.review_status || 'Pending'}
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="p-5 space-y-3">
        {/* Title */}
        <h4 className="text-base font-bold text-slate-900 leading-snug">
          {finding.title || 'Discrepancy Detected'}
        </h4>

        {/* Description */}
        <p className="text-sm text-slate-600 leading-relaxed">
          {finding.description}
        </p>

        {/* Evidence Block */}
        {finding.evidence && (
          <div className="space-y-1">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Verification Evidence:
            </span>
            <pre className="p-3 bg-slate-900 text-emerald-400 font-mono text-xs rounded-lg overflow-x-auto whitespace-pre-wrap leading-relaxed shadow-inner border border-slate-800">
              {finding.evidence}
            </pre>
          </div>
        )}

        {/* Metadata Footer: Doc, Page, Field & Officer Notes */}
        <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
          <div className="flex flex-wrap items-center gap-3">
            {(finding.document_name || finding.document_id) && (
              <span className="inline-flex items-center gap-1 font-medium text-slate-700">
                <FileText className="w-3.5 h-3.5 text-slate-400" />
                {finding.document_name || `Doc: ${finding.document_id.slice(0, 8)}...`}
              </span>
            )}
            {finding.page_number && (
              <span className="bg-slate-100 px-2 py-0.5 rounded text-slate-600 font-medium">
                Page {finding.page_number}
              </span>
            )}
            {finding.field_name && (
              <span className="text-slate-500">
                Field: <code className="text-slate-700 font-semibold">{finding.field_name}</code>
              </span>
            )}
          </div>

          {/* Review Button */}
          <button
            type="button"
            onClick={() => onReview?.(finding)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white border border-blue-200 transition-colors shadow-sm"
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>{finding.review_status && finding.review_status !== 'pending' ? 'Update Review' : 'Review Finding'}</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>

        {/* Review Comment if available */}
        {finding.review_comment && (
          <div className="mt-2 p-2.5 bg-blue-50/60 rounded-md border border-blue-100 text-xs text-blue-900 flex items-start gap-2">
            <span className="font-semibold text-blue-700 flex-shrink-0">Officer Comment:</span>
            <span className="italic">{finding.review_comment}</span>
          </div>
        )}
      </div>
    </div>
  )
}
