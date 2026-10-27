import React from 'react'
import { CheckCircle2, XCircle, FileText, AlertTriangle, ShieldCheck } from 'lucide-react'

const MANDATORY_AICTE_FIELDS = [
  { key: 'institution_name', label: 'Institution Name', category: 'Identity' },
  { key: 'trust_name', label: 'Trust / Society / Company Name', category: 'Identity' },
  { key: 'society_registration_no', label: 'Society / Trust Registration Certificate', category: 'Legal Entity' },
  { key: 'land_area_acres', label: 'Land Area Ownership / Lease Deed', category: 'Infrastructure' },
  { key: 'building_plan_approved', label: 'Competent Authority Approved Building Plan', category: 'Infrastructure' },
  { key: 'fire_safety_noc', label: 'Fire & Rescue Safety NOC Certificate', category: 'Safety & Statutory' },
  { key: 'occupancy_certificate', label: 'Building Completion / Occupancy Certificate', category: 'Infrastructure' },
  { key: 'fdr_amount', label: 'Joint FDR / Corpus Fund Verification', category: 'Financial Viability' },
  { key: 'principal_qualified', label: 'Qualified Principal / Director Appointment', category: 'Faculty & Governance' },
  { key: 'water_electricity_certificate', label: 'Potable Water & Power Supply Clearance', category: 'Statutory Utilities' },
]

export default function ComplianceChecklist({ extractedFields = [], findings = [], documents = [] }) {
  // Map doc ID to name
  const docMap = {}
  if (Array.isArray(documents)) {
    documents.forEach((d) => {
      if (d.id) docMap[d.id] = d.filename || d.name || `Doc ${d.id.slice(0, 8)}`
    })
  }

  // Build lookup of extracted fields by normalized field name
  const fieldMap = {}
  if (Array.isArray(extractedFields)) {
    extractedFields.forEach((item) => {
      if (item.field_name) {
        const normKey = item.field_name.toLowerCase().trim()
        fieldMap[normKey] = item
      }
    })
  }

  // Find any missing_field findings
  const missingFieldKeys = new Set(
    (findings || [])
      .filter((f) => f.finding_type === 'missing_field' || f.severity === 'critical')
      .map((f) => (f.field_name || '').toLowerCase().trim())
  )

  // Calculate compliance stats
  const evaluatedFields = MANDATORY_AICTE_FIELDS.map((spec) => {
    const foundField = fieldMap[spec.key.toLowerCase()]
    const isExplicitlyMissing = missingFieldKeys.has(spec.key.toLowerCase())
    const isPresent = Boolean(foundField && foundField.field_value && !isExplicitlyMissing)

    return {
      ...spec,
      isPresent,
      foundData: foundField,
      docName: foundField
        ? foundField.document_name || docMap[foundField.document_id] || (foundField.document_id ? `Doc ${foundField.document_id.slice(0, 8)}` : null)
        : null,
    }
  })

  const verifiedCount = evaluatedFields.filter((f) => f.isPresent).length
  const totalCount = evaluatedFields.length
  const compliancePct = Math.round((verifiedCount / totalCount) * 100)

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
      {/* Header & Stats Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            Mandatory AICTE Regulatory Checklist
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Cross-verification of mandatory documentary requirements according to the AICTE Approval Process Handbook (APH).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs font-semibold text-slate-500">Compliance Rate</div>
            <div className="text-xl font-bold text-slate-900">
              {verifiedCount} / {totalCount}{' '}
              <span className="text-xs font-medium text-slate-500">({compliancePct}%)</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-full border-4 border-slate-100 flex items-center justify-center font-bold text-xs"
               style={{
                 borderColor: compliancePct >= 80 ? '#10b981' : compliancePct >= 50 ? '#f59e0b' : '#ef4444'
               }}>
            {compliancePct}%
          </div>
        </div>
      </div>

      {/* Checklist Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {evaluatedFields.map((item) => (
          <div
            key={item.key}
            className={`p-3.5 rounded-xl border transition-all flex items-start gap-3 ${
              item.isPresent
                ? 'bg-emerald-50/40 border-emerald-200 hover:bg-emerald-50/70'
                : 'bg-rose-50/40 border-rose-200 hover:bg-rose-50/70'
            }`}
          >
            <div className="mt-0.5 flex-shrink-0">
              {item.isPresent ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-600" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-bold text-slate-900 truncate">
                  {item.label}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider flex-shrink-0 ${
                    item.isPresent
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-rose-100 text-rose-800'
                  }`}
                >
                  {item.isPresent ? 'Verified' : 'Missing'}
                </span>
              </div>

              <div className="mt-1 text-xs text-slate-600">
                <span className="text-[11px] text-slate-400 font-medium">Category: {item.category}</span>
              </div>

              {item.isPresent && item.foundData ? (
                <div className="mt-2 pt-2 border-t border-emerald-100/80 text-xs flex flex-wrap items-center gap-2 text-slate-600">
                  <span className="font-semibold text-slate-700">Value:</span>
                  <span className="bg-white/80 px-1.5 py-0.5 rounded border border-emerald-200 font-mono text-[11px] text-slate-900 truncate max-w-[200px]">
                    {String(item.foundData.field_value)}
                  </span>
                  {item.docName && (
                    <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                      <FileText className="w-3 h-3 text-slate-400" />
                      <span className="truncate max-w-[120px]">{item.docName}</span>
                    </span>
                  )}
                  {item.foundData.page_number && (
                    <span className="text-[10px] bg-emerald-100/60 px-1.5 py-0.2 rounded text-emerald-800 font-medium">
                      P. {item.foundData.page_number}
                    </span>
                  )}
                </div>
              ) : (
                <div className="mt-2 pt-2 border-t border-rose-100/80 text-[11px] text-rose-700 flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-500 flex-shrink-0" />
                  <span>Mandatory AICTE submission not identified or failed validation.</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
