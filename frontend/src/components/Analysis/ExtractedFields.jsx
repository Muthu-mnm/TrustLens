import React, { useState, useMemo } from 'react'
import { Search, Layers, ListFilter, FileText, CheckCircle2, AlertTriangle } from 'lucide-react'

export default function ExtractedFields({ fields = [], documents = [] }) {
  const [groupByDoc, setGroupByDoc] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  // Map doc ID to doc name for quick lookup if not present in field
  const docMap = useMemo(() => {
    const map = {}
    if (Array.isArray(documents)) {
      documents.forEach((d) => {
        if (d.id) map[d.id] = d.filename || d.name || `Doc ${d.id.slice(0, 8)}`
      })
    }
    return map
  }, [documents])

  const filteredFields = useMemo(() => {
    if (!Array.isArray(fields)) return []
    return fields.filter((f) => {
      const q = searchQuery.toLowerCase()
      const name = (f.field_name || '').toLowerCase()
      const val = (String(f.field_value || '')).toLowerCase()
      const docName = (f.document_name || docMap[f.document_id] || '').toLowerCase()
      return name.includes(q) || val.includes(q) || docName.includes(q)
    })
  }, [fields, searchQuery, docMap])

  // Group by document if enabled
  const groupedFields = useMemo(() => {
    if (!groupByDoc) return null
    const groups = {}
    filteredFields.forEach((field) => {
      const docId = field.document_id || 'unassigned'
      const docName = field.document_name || docMap[docId] || 'General Document'
      if (!groups[docName]) {
        groups[docName] = []
      }
      groups[docName].push(field)
    })
    return groups
  }, [filteredFields, groupByDoc, docMap])

  const getConfidenceInfo = (conf) => {
    const val = typeof conf === 'number' ? conf : parseFloat(conf) || 0
    const pct = Math.round(val <= 1 ? val * 100 : val)

    if (val >= 0.8 || pct >= 80) {
      return {
        pct,
        barColor: 'bg-emerald-500',
        textColor: 'text-emerald-700 font-semibold',
        badge: 'High',
      }
    }
    if (val >= 0.5 || pct >= 50) {
      return {
        pct,
        barColor: 'bg-amber-500',
        textColor: 'text-amber-700 font-semibold',
        badge: 'Moderate',
      }
    }
    return {
      pct,
      barColor: 'bg-rose-500',
      textColor: 'text-rose-700 font-semibold',
      badge: 'Low',
    }
  }

  const renderTableRows = (items) => {
    return items.map((f, idx) => {
      const conf = getConfidenceInfo(f.confidence)
      const docName = f.document_name || docMap[f.document_id] || (f.document_id ? `Doc ${f.document_id.slice(0, 8)}...` : 'N/A')

      return (
        <tr key={`${f.field_name}_${idx}`} className="hover:bg-slate-50/80 transition-colors">
          {/* Field Name */}
          <td className="px-4 py-3 text-xs font-semibold text-slate-800 font-mono">
            {f.field_name}
          </td>

          {/* Extracted Value */}
          <td className="px-4 py-3 text-xs text-slate-900 font-medium break-words max-w-xs">
            <span className="bg-slate-50 px-2 py-1 rounded border border-slate-200 block text-slate-800">
              {String(f.field_value ?? '—')}
            </span>
          </td>

          {/* Confidence */}
          <td className="px-4 py-3 text-xs">
            <div className="flex items-center gap-2 min-w-[130px]">
              <div className="w-16 bg-slate-200 h-2 rounded-full overflow-hidden flex-shrink-0">
                <div
                  className={`h-full rounded-full ${conf.barColor} transition-all duration-500`}
                  style={{ width: `${conf.pct}%` }}
                />
              </div>
              <span className={`text-xs ${conf.textColor}`}>
                {conf.pct}%
              </span>
            </div>
          </td>

          {/* Page */}
          <td className="px-4 py-3 text-xs text-slate-600">
            {f.page_number ? (
              <span className="px-2 py-0.5 rounded bg-slate-100 font-medium">
                P. {f.page_number}
              </span>
            ) : (
              <span className="text-slate-400">—</span>
            )}
          </td>

          {/* Document Reference */}
          {!groupByDoc && (
            <td className="px-4 py-3 text-xs text-slate-600 max-w-[180px] truncate">
              <span className="inline-flex items-center gap-1.5" title={docName}>
                <FileText className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                <span className="truncate">{docName}</span>
              </span>
            </td>
          )}
        </tr>
      )
    })
  }

  return (
    <div className="space-y-4">
      {/* Search & Group Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search field names, values, or docs..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
          />
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setGroupByDoc(!groupByDoc)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              groupByDoc
                ? 'bg-blue-50 border-blue-300 text-blue-700 shadow-sm'
                : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Group by Document</span>
          </button>
          <span className="text-xs text-slate-500 font-medium px-1">
            Total Fields: <strong className="text-slate-800">{filteredFields.length}</strong>
          </span>
        </div>
      </div>

      {/* Main Table / Grouped Views */}
      {filteredFields.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
          <ListFilter className="w-8 h-8 mx-auto text-slate-300 mb-2" />
          <p className="text-sm font-semibold">No extracted fields match your criteria.</p>
          <p className="text-xs text-slate-400 mt-1">Try adjusting your search query or run analysis again.</p>
        </div>
      ) : groupByDoc && groupedFields ? (
        <div className="space-y-4">
          {Object.entries(groupedFields).map(([docTitle, items]) => (
            <div
              key={docTitle}
              className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
            >
              <div className="px-4 py-2.5 bg-slate-100/70 border-b border-slate-200 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span>{docTitle}</span>
                </div>
                <span className="text-[11px] font-semibold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {items.length} fields
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/50 border-b border-slate-100 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      <th className="px-4 py-2">Field Name</th>
                      <th className="px-4 py-2">Extracted Value</th>
                      <th className="px-4 py-2">OCR Confidence</th>
                      <th className="px-4 py-2">Page</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {renderTableRows(items)}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="px-4 py-3">Field Name</th>
                  <th className="px-4 py-3">Extracted Value</th>
                  <th className="px-4 py-3">OCR Confidence</th>
                  <th className="px-4 py-3">Page</th>
                  <th className="px-4 py-3">Source Document</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {renderTableRows(filteredFields)}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
