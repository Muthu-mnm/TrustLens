import React, { useState } from 'react'
import { FileDown, FileCheck, Shield, Clock, AlertTriangle, CheckCircle2, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import { downloadReport } from '../../api/client'

export default function ReportDownload({ application, results }) {
  const [downloading, setDownloading] = useState(false)
  const [previewing, setPreviewing] = useState(false)

  if (!application) return null

  const getReportBlob = async () => {
    const response = await downloadReport(application.id)
    const blob = response.data instanceof Blob
      ? response.data
      : new Blob([response.data], { type: 'application/pdf' })

    if (blob.size === 0) {
      throw new Error('Received an empty report from the scrutiny engine.')
    }

    if (blob.size < 200) {
      try {
        const text = await blob.text()
        if (text.startsWith('{') || text.startsWith('<!DOCTYPE') || text.startsWith('<html')) {
          let errDetail = 'Server returned an invalid response instead of a PDF report.'
          try {
            const parsed = JSON.parse(text)
            if (parsed.detail) errDetail = parsed.detail
          } catch {}
          throw new Error(errDetail)
        }
      } catch (e) {
        if (e.message) throw e
      }
    }

    return blob
  }

  const handleDownload = async () => {
    setDownloading(true)
    const toastId = toast.loading('Generating scrutiny dossier...')
    try {
      const blob = await getReportBlob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const safeId = (application.app_id || application.id).replace(/[^\w\-]/g, '_')
      link.setAttribute('download', `TrustLens_Scrutiny_Report_${safeId}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      setTimeout(() => window.URL.revokeObjectURL(url), 30000)

      toast.success('Report downloaded successfully!', { id: toastId })
    } catch (err) {
      console.error('Failed to download report:', err)
      toast.error(err.message || 'Failed to download scrutiny report.', { id: toastId })
    } finally {
      setDownloading(false)
    }
  }

  const handlePreview = async () => {
    setPreviewing(true)
    const toastId = toast.loading('Opening scrutiny report preview...')
    try {
      const blob = await getReportBlob()
      const url = window.URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => window.URL.revokeObjectURL(url), 60000)
      toast.success('Report opened in new tab!', { id: toastId })
    } catch (err) {
      console.error('Failed to preview report:', err)
      toast.error(err.message || 'Failed to preview scrutiny report.', { id: toastId })
    } finally {
      setPreviewing(false)
    }
  }

  const generatedTime = results?.analyzed_at
    ? new Date(results.analyzed_at).toLocaleString()
    : new Date().toLocaleString()

  const findingCount = results?.findings?.length ?? application?.finding_count ?? 0
  const riskBand = results?.risk_band || application?.risk_band || 'Under Review'
  const riskScore = results?.risk_score ?? application?.risk_score ?? 0

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center flex-shrink-0 border border-blue-200">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">
              Executive Scrutiny & Compliance Report
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Comprehensive decision-support dossier including OCR extraction logs, visual tamper analysis, and rule audit findings.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
          <button
            type="button"
            onClick={handlePreview}
            disabled={previewing || downloading}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 transition-all shadow-sm disabled:opacity-50 flex-shrink-0"
          >
            {previewing ? (
              <>
                <span className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin"></span>
                <span>Opening...</span>
              </>
            ) : (
              <>
                <Eye className="w-4 h-4 text-slate-500" />
                <span>Preview</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleDownload}
            disabled={downloading || previewing}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold bg-blue-700 hover:bg-blue-800 text-white transition-all shadow-md shadow-blue-700/20 disabled:opacity-50 flex-shrink-0"
          >
            {downloading ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                <span>Generating PDF...</span>
              </>
            ) : (
              <>
                <FileDown className="w-4 h-4" />
                <span>Download PDF Report</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Application ID</span>
          <p className="text-sm font-bold text-slate-900 mt-1 font-mono truncate">
            {application.app_id || application.id}
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Institution</span>
          <p className="text-sm font-bold text-slate-900 mt-1 truncate">
            {application.institution_name}
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Scrutiny Risk Band</span>
          <p className="text-sm font-bold text-slate-900 mt-1 flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                riskBand.toLowerCase() === 'critical'
                  ? 'bg-rose-500'
                  : riskBand.toLowerCase() === 'high'
                  ? 'bg-orange-500'
                  : riskBand.toLowerCase() === 'medium'
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
            />
            {riskBand} ({Math.round(riskScore)}/100)
          </p>
        </div>

        <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-500 uppercase">Total Findings</span>
          <p className="text-sm font-bold text-slate-900 mt-1">
            {findingCount} Recorded
          </p>
        </div>
      </div>

      {/* Report Features / Metadata */}
      <div className="bg-slate-50/60 rounded-xl p-4 border border-slate-200 space-y-2 text-xs text-slate-600">
        <div className="flex items-center gap-2 text-slate-700 font-semibold">
          <Shield className="w-4 h-4 text-blue-600" />
          <span>Report Contents & Authentication Details</span>
        </div>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-600 pl-6 list-disc">
          <li>Institution & Trust registration credential verification</li>
          <li>Detailed OCR extracted values with confidence metrics</li>
          <li>Error Level Analysis (ELA) and perceptual hash tamper checks</li>
          <li>Officer review annotations, timestamps, and digital signing block</li>
        </ul>
        <div className="pt-2 flex items-center gap-2 text-[11px] text-slate-500 font-mono">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Report Snapshot Generated: {generatedTime}</span>
        </div>
      </div>

      {/* Mandatory Disclaimer */}
      <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
        <span className="font-medium">
          Disclaimer: This report is for internal review purposes only. Official AICTE decisions must adhere to designated committee directives.
        </span>
      </div>
    </div>
  )
}
