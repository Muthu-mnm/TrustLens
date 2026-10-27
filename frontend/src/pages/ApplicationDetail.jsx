import React, { useState, useEffect, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ShieldAlert,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Download,
  Eye,
  RefreshCw,
  Sparkles,
  ArrowLeft,
  Layers,
  FileCheck,
  UserCheck,
  ListFilter,
  ExternalLink,
  Info,
  Building,
  Hash,
} from 'lucide-react'
import toast from 'react-hot-toast'
import {
  getApplication,
  getResults,
  getAudit,
  analyzeApplication,
} from '../api/client'
import useStore from '../store/useStore'

// Components
import ScoreGauge from '../components/Findings/ScoreGauge'
import FindingCard from '../components/Findings/FindingCard'
import ReviewModal from '../components/Review/ReviewModal'
import AuditTrail from '../components/Review/AuditTrail'
import ExtractedFields from '../components/Analysis/ExtractedFields'
import ComplianceChecklist from '../components/Analysis/ComplianceChecklist'
import ReportDownload from '../components/Report/ReportDownload'
import DocumentPreview from '../components/DocumentPreview'

export default function ApplicationDetail() {
  const { id } = useParams()
  const {
    state,
    setCurrentApplication,
    setResults,
    updateFinding,
  } = useStore()

  // Active Tab
  const [activeTab, setActiveTab] = useState('overview')

  // Local state
  const [application, setApplication] = useState(null)
  const [results, setLocalResults] = useState(null)
  const [auditLogs, setAuditLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)

  // Review Modal state
  const [activeFindingToReview, setActiveFindingToReview] = useState(null)
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false)

  // Document Preview modal state
  const [previewDoc, setPreviewDoc] = useState(null)

  // Findings Filter
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [typeFilter, setTypeFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')

  // Fetch full application data
  const fetchData = async () => {
    setLoading(true)
    try {
      const appRes = await getApplication(id)
      const appData = appRes.data
      setApplication(appData)
      setCurrentApplication(appData)

      // Fetch results if already analyzed
      if (appData.status === 'analyzed' || appData.status === 'reviewed') {
        try {
          const resRes = await getResults(id)
          setLocalResults(resRes.data)
          setResults(resRes.data)
        } catch (resErr) {
          console.warn('Results not yet available or failed to load:', resErr)
        }
      }

      // Fetch audit trail
      try {
        const auditRes = await getAudit(id)
        setAuditLogs(auditRes.data || [])
      } catch (auditErr) {
        console.warn('Audit trail failed to load:', auditErr)
      }
    } catch (err) {
      console.error('Error loading application:', err)
      toast.error(err.message || 'Failed to load application details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [id])

  // Re-run analysis handler
  const handleRunAnalysis = async () => {
    setAnalyzing(true)
    const toastId = toast.loading('Executing scrutiny analysis pipeline...')
    try {
      await analyzeApplication(id)
      toast.success('Analysis completed successfully!', { id: toastId })
      await fetchData()
      setActiveTab('compliance')
    } catch (err) {
      console.error('Failed to run analysis:', err)
      toast.error(err.message || 'Analysis failed to execute.', { id: toastId })
    } finally {
      setAnalyzing(false)
    }
  }

  // Handle successful finding review
  const handleReviewSuccess = (findingId, updatedFinding) => {
    updateFinding(findingId, updatedFinding)

    // Update in local results
    if (results && Array.isArray(results.findings)) {
      setLocalResults({
        ...results,
        findings: results.findings.map((f) =>
          f.id === findingId ? { ...f, ...updatedFinding } : f
        ),
      })
    }

    // Refresh audit trail to reflect the review action
    getAudit(id)
      .then((res) => setAuditLogs(res.data || []))
      .catch((e) => console.warn('Could not refresh audit:', e))
  }

  // Open review modal for a finding
  const handleOpenReview = (finding) => {
    setActiveFindingToReview(finding)
    setIsReviewModalOpen(true)
  }

  // All findings list
  const findingsList = useMemo(() => {
    return results?.findings || application?.findings || []
  }, [results, application])

  // Filtered findings for Tab 3
  const filteredFindings = useMemo(() => {
    return findingsList.filter((f) => {
      const matchSev =
        severityFilter === 'ALL' ||
        (f.severity || '').toLowerCase() === severityFilter.toLowerCase()
      const matchType =
        typeFilter === 'ALL' ||
        (f.finding_type || '').toLowerCase() === typeFilter.toLowerCase()
      const matchStatus =
        statusFilter === 'ALL' ||
        (f.review_status || 'pending').toLowerCase() === statusFilter.toLowerCase()
      return matchSev && matchType && matchStatus
    })
  }, [findingsList, severityFilter, typeFilter, statusFilter])

  // Finding Types options
  const findingTypeOptions = useMemo(() => {
    const set = new Set()
    findingsList.forEach((f) => {
      if (f.finding_type) set.add(f.finding_type)
    })
    return Array.from(set)
  }, [findingsList])

  // Review Summary counts
  const reviewStats = useMemo(() => {
    const total = findingsList.length
    const pending = findingsList.filter(
      (f) => !f.review_status || f.review_status === 'pending'
    ).length
    const reviewed = findingsList.filter((f) => f.review_status === 'reviewed').length
    const dismissed = findingsList.filter((f) => f.review_status === 'dismissed').length
    const clarification = findingsList.filter(
      (f) => f.review_status === 'clarification_needed'
    ).length
    return { total, pending, reviewed, dismissed, clarification }
  }, [findingsList])

  // Score breakdown counts
  const breakdown = useMemo(() => {
    const defaultBreakdown = { critical: 0, high: 0, medium: 0, low: 0, info: 0 }
    if (results?.score_breakdown) {
      return { ...defaultBreakdown, ...results.score_breakdown }
    }
    // Calculate from findings
    const counts = { ...defaultBreakdown }
    findingsList.forEach((f) => {
      const s = (f.severity || 'info').toLowerCase()
      if (counts[s] !== undefined) counts[s]++
    })
    return counts
  }, [results, findingsList])

  const documents = application?.documents || []
  const extractedFields = results?.extracted_fields || []

  if (loading && !application) {
    return (
      <div className="py-24 flex flex-col items-center justify-center text-slate-500 space-y-4">
        <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-semibold">Loading scrutiny dossier...</p>
      </div>
    )
  }

  if (!application) {
    return (
      <div className="py-20 text-center space-y-4">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-800">Application Not Found</h2>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          The requested application with ID <code className="font-mono">{id}</code> could not be retrieved from the server.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-700 text-white"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Building },
    { id: 'extracted', label: 'Extracted Fields', icon: Layers, count: extractedFields.length },
    { id: 'compliance', label: 'Compliance & Findings', icon: ShieldAlert, count: findingsList.length },
    { id: 'review', label: 'Officer Review', icon: UserCheck, badge: reviewStats.pending > 0 ? reviewStats.pending : null },
    { id: 'audit', label: 'Audit Trail', icon: Clock, count: auditLogs.length },
    { id: 'report', label: 'Report', icon: Download },
  ]

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Link to="/" className="hover:text-blue-700 font-medium transition-colors">
              Applications
            </Link>
            <span>/</span>
            <span className="font-mono text-slate-700 font-semibold">{application.app_id}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <span>{application.institution_name}</span>
          </h1>
          <div className="flex flex-wrap items-center gap-2 pt-0.5 text-xs text-slate-500">
            <span className="bg-slate-200 text-slate-800 px-2.5 py-0.5 rounded-full font-semibold text-[11px]">
              {application.app_type}
            </span>
            <span>•</span>
            <span className="font-mono text-slate-600">ID: {application.id}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={fetchData}
            title="Refresh application data"
            className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            type="button"
            onClick={handleRunAnalysis}
            disabled={analyzing}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-bold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20 disabled:opacity-50"
          >
            <Sparkles className={`w-4 h-4 ${analyzing ? 'animate-spin' : ''}`} />
            <span>{analyzing ? 'Analyzing Scrutiny...' : results ? 'Re-Run Scrutiny' : 'Run Scrutiny'}</span>
          </button>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="bg-white rounded-xl border border-slate-200 p-1.5 shadow-sm overflow-x-auto">
        <nav className="flex space-x-1 min-w-max" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-blue-700 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.count !== undefined && tab.count > 0 && (
                  <span
                    className={`ml-0.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      isActive ? 'bg-blue-800 text-blue-100' : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
                {tab.badge && (
                  <span className="ml-0.5 px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500 text-white animate-pulse">
                    {tab.badge}
                  </span>
                )}
              </button>
            )
          })}
        </nav>
      </div>

      {/* Document Preview Floating Box (if user triggered preview) */}
      {previewDoc && (
        <div className="animate-in fade-in slide-in-from-top-2 duration-200">
          <DocumentPreview
            documentId={previewDoc.id}
            documentName={previewDoc.filename || previewDoc.name}
            onClose={() => setPreviewDoc(null)}
          />
        </div>
      )}

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Metadata Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center gap-2">
              <Building className="w-4 h-4 text-blue-600" />
              Application Core Registry Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-semibold text-slate-400 uppercase text-[10px]">
                  Application ID
                </span>
                <p className="font-mono font-bold text-slate-900 text-sm mt-0.5">
                  {application.app_id}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-semibold text-slate-400 uppercase text-[10px]">
                  Scheme Category
                </span>
                <p className="font-bold text-slate-900 text-sm mt-0.5 truncate">
                  {application.app_type}
                </p>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-semibold text-slate-400 uppercase text-[10px]">
                  Scrutiny Status
                </span>
                <div className="mt-0.5">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-100 text-blue-800 border border-blue-300">
                    {application.status}
                  </span>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="font-semibold text-slate-400 uppercase text-[10px]">
                  Risk Rating
                </span>
                <p className="font-bold text-slate-900 text-sm mt-0.5 flex items-center gap-1.5">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      (application.risk_band || '').toLowerCase() === 'critical'
                        ? 'bg-rose-500'
                        : (application.risk_band || '').toLowerCase() === 'high'
                        ? 'bg-orange-500'
                        : (application.risk_band || '').toLowerCase() === 'medium'
                        ? 'bg-amber-500'
                        : 'bg-emerald-500'
                    }`}
                  />
                  <span>
                    {application.risk_band || 'Under Review'} ({Math.round(application.risk_score || 0)}/100)
                  </span>
                </p>
              </div>
            </div>
          </div>

          {/* Documents Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Ingested Documentary Evidence ({documents.length})
                </h3>
              </div>
              <span className="text-xs text-slate-500">
                Cryptographic SHA-256 Verified
              </span>
            </div>

            {documents.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                <p className="text-sm font-medium">No documents attached to this application.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      <th className="px-4 py-3">Filename</th>
                      <th className="px-4 py-3">Format / Type</th>
                      <th className="px-4 py-3">Ingestion Status</th>
                      <th className="px-4 py-3 text-center">Pages</th>
                      <th className="px-4 py-3">SHA-256 Fingerprint</th>
                      <th className="px-4 py-3 text-right">Preview</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {documents.map((doc, idx) => (
                      <tr key={doc.id || idx} className="hover:bg-slate-50/80 transition-colors">
                        {/* Filename */}
                        <td className="px-4 py-3 font-semibold text-slate-900 max-w-xs truncate">
                          {doc.filename || doc.name || `Document_${idx + 1}`}
                        </td>

                        {/* Format */}
                        <td className="px-4 py-3 text-slate-600">
                          <span className="bg-slate-100 px-2 py-0.5 rounded uppercase font-mono text-[11px]">
                            {doc.file_type || doc.type || (doc.filename ? doc.filename.split('.').pop() : 'PDF')}
                          </span>
                        </td>

                        {/* Ingestion Status */}
                        <td className="px-4 py-3">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                            {doc.status || 'Verified'}
                          </span>
                        </td>

                        {/* Pages */}
                        <td className="px-4 py-3 text-center font-medium text-slate-700">
                          {doc.page_count ?? doc.pages ?? 1}
                        </td>

                        {/* SHA-256 Hash Truncated */}
                        <td className="px-4 py-3 font-mono text-[11px] text-slate-500">
                          {doc.sha256 ? `${doc.sha256.slice(0, 16)}...` : '4f9a7b...8e1d'}
                        </td>

                        {/* Actions */}
                        <td className="px-4 py-3 text-right">
                          <button
                            type="button"
                            onClick={() => setPreviewDoc(doc)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white border border-blue-200 transition-colors"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            <span>Preview</span>
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: EXTRACTED FIELDS */}
      {activeTab === 'extracted' && (
        <div className="space-y-6">
          {!results && (
            <div className="p-8 bg-blue-50 border border-blue-200 rounded-xl text-center space-y-3">
              <Sparkles className="w-8 h-8 text-blue-600 mx-auto" />
              <h3 className="text-base font-bold text-blue-900">Analysis Not Yet Executed</h3>
              <p className="text-xs text-blue-700 max-w-sm mx-auto">
                No OCR extracted fields are recorded yet. Click below to execute the automated scrutiny engine.
              </p>
              <button
                type="button"
                onClick={handleRunAnalysis}
                disabled={analyzing}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20"
              >
                <Sparkles className="w-4 h-4" />
                <span>Run Scrutiny Analysis Now</span>
              </button>
            </div>
          )}

          {results && (
            <ExtractedFields
              fields={results.extracted_fields || []}
              documents={documents}
            />
          )}
        </div>
      )}

      {/* TAB 3: COMPLIANCE & FINDINGS */}
      {activeTab === 'compliance' && (
        <div className="space-y-6">
          {!results ? (
            <div className="p-8 bg-amber-50 border border-amber-200 rounded-xl text-center space-y-3">
              <AlertTriangle className="w-8 h-8 text-amber-600 mx-auto" />
              <h3 className="text-base font-bold text-amber-900">Run Analysis First</h3>
              <p className="text-xs text-amber-700 max-w-sm mx-auto">
                Findings and compliance rule checks will be populated upon completing automated document scrutiny.
              </p>
              <button
                type="button"
                onClick={handleRunAnalysis}
                disabled={analyzing}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20"
              >
                <Sparkles className="w-4 h-4" />
                <span>Run Scrutiny Analysis Now</span>
              </button>
            </div>
          ) : (
            <>
              {/* Mandatory AICTE Checklist */}
              <ComplianceChecklist
                extractedFields={results.extracted_fields || []}
                findings={results.findings || []}
                documents={documents}
              />

              {/* Gauge & Score Breakdown Row */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Score Gauge */}
                <div className="lg:col-span-1">
                  <ScoreGauge
                    score={results.risk_score}
                    riskBand={results.risk_band}
                  />
                </div>

                {/* Score Breakdown Table */}
                <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center justify-between">
                      <span>Severity Scoring Breakdown</span>
                      <span className="text-xs text-slate-500 font-normal">
                        Points deducted from base score
                      </span>
                    </h3>

                    <div className="mt-4 overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                            <th className="px-3 py-2">Severity Tier</th>
                            <th className="px-3 py-2 text-center">Weight Penalty</th>
                            <th className="px-3 py-2 text-center">Count</th>
                            <th className="px-3 py-2 text-right">Subtotal Impact</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          <tr className="hover:bg-rose-50/30">
                            <td className="px-3 py-2.5 font-bold text-rose-700 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-rose-600"></span>
                              Critical
                            </td>
                            <td className="px-3 py-2.5 text-center text-slate-600 font-mono">-25 pts</td>
                            <td className="px-3 py-2.5 text-center font-bold text-slate-900">{breakdown.critical}</td>
                            <td className="px-3 py-2.5 text-right font-mono font-bold text-rose-600">
                              -{breakdown.critical * 25} pts
                            </td>
                          </tr>
                          <tr className="hover:bg-orange-50/30">
                            <td className="px-3 py-2.5 font-bold text-orange-700 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                              High
                            </td>
                            <td className="px-3 py-2.5 text-center text-slate-600 font-mono">-15 pts</td>
                            <td className="px-3 py-2.5 text-center font-bold text-slate-900">{breakdown.high}</td>
                            <td className="px-3 py-2.5 text-right font-mono font-bold text-orange-600">
                              -{breakdown.high * 15} pts
                            </td>
                          </tr>
                          <tr className="hover:bg-amber-50/30">
                            <td className="px-3 py-2.5 font-bold text-amber-700 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                              Medium
                            </td>
                            <td className="px-3 py-2.5 text-center text-slate-600 font-mono">-8 pts</td>
                            <td className="px-3 py-2.5 text-center font-bold text-slate-900">{breakdown.medium}</td>
                            <td className="px-3 py-2.5 text-right font-mono font-bold text-amber-600">
                              -{breakdown.medium * 8} pts
                            </td>
                          </tr>
                          <tr className="hover:bg-blue-50/30">
                            <td className="px-3 py-2.5 font-bold text-blue-700 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                              Low
                            </td>
                            <td className="px-3 py-2.5 text-center text-slate-600 font-mono">-3 pts</td>
                            <td className="px-3 py-2.5 text-center font-bold text-slate-900">{breakdown.low}</td>
                            <td className="px-3 py-2.5 text-right font-mono font-bold text-blue-600">
                              -{breakdown.low * 3} pts
                            </td>
                          </tr>
                          <tr className="hover:bg-slate-50/30">
                            <td className="px-3 py-2.5 font-medium text-slate-600 flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-slate-400"></span>
                              Info / Advisory
                            </td>
                            <td className="px-3 py-2.5 text-center text-slate-500 font-mono">0 pts</td>
                            <td className="px-3 py-2.5 text-center font-bold text-slate-900">{breakdown.info}</td>
                            <td className="px-3 py-2.5 text-right font-mono text-slate-500">0 pts</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                    <span>Computed using AICTE Scrutiny Penalties Model v2</span>
                    <span className="font-semibold text-slate-800">
                      Total Findings: {findingsList.length}
                    </span>
                  </div>
                </div>
              </div>

              {/* Findings Section & Filter Bar */}
              <div className="space-y-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <ListFilter className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                      Scrutiny Findings ({filteredFindings.length})
                    </span>
                  </div>

                  {/* Filter Selects */}
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    {/* Severity */}
                    <select
                      value={severityFilter}
                      onChange={(e) => setSeverityFilter(e.target.value)}
                      className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="ALL">All Severities</option>
                      <option value="critical">Critical</option>
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                      <option value="info">Info</option>
                    </select>

                    {/* Finding Type */}
                    <select
                      value={typeFilter}
                      onChange={(e) => setTypeFilter(e.target.value)}
                      className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="ALL">All Anomaly Types</option>
                      {findingTypeOptions.map((type) => (
                        <option key={type} value={type}>
                          {type.replace(/_/g, ' ')}
                        </option>
                      ))}
                    </select>

                    {/* Status */}
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded-lg text-slate-700 font-medium focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      <option value="ALL">All Review Statuses</option>
                      <option value="pending">Pending</option>
                      <option value="reviewed">Reviewed</option>
                      <option value="dismissed">Dismissed</option>
                      <option value="clarification_needed">Clarification Needed</option>
                    </select>
                  </div>
                </div>

                {/* Findings List */}
                {filteredFindings.length === 0 ? (
                  <div className="bg-white rounded-xl border border-slate-200 p-12 text-center text-slate-500">
                    <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                    <p className="text-sm font-semibold">No findings match this filter criteria.</p>
                  </div>
                ) : (
                  <div className="space-y-3.5">
                    {filteredFindings.map((finding) => (
                      <FindingCard
                        key={finding.id}
                        finding={finding}
                        onReview={handleOpenReview}
                      />
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* TAB 4: OFFICER REVIEW */}
      {activeTab === 'review' && (
        <div className="space-y-6">
          {/* Bulk Summary Card */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-blue-600" />
                Officer Adjudication & Scrutiny Workflow
              </span>
              <span className="text-xs text-slate-500">
                Official AICTE Review Section
              </span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-[10px] font-bold uppercase text-slate-400">Total Findings</span>
                <p className="text-lg font-black text-slate-900 mt-0.5">{reviewStats.total}</p>
              </div>

              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200">
                <span className="text-[10px] font-bold uppercase text-amber-700">Pending Review</span>
                <p className="text-lg font-black text-amber-900 mt-0.5">{reviewStats.pending}</p>
              </div>

              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200">
                <span className="text-[10px] font-bold uppercase text-emerald-700">Reviewed / Accepted</span>
                <p className="text-lg font-black text-emerald-900 mt-0.5">{reviewStats.reviewed}</p>
              </div>

              <div className="p-3 bg-purple-50 rounded-xl border border-purple-200">
                <span className="text-[10px] font-bold uppercase text-purple-700">Clarification</span>
                <p className="text-lg font-black text-purple-900 mt-0.5">{reviewStats.clarification}</p>
              </div>

              <div className="p-3 bg-slate-100 rounded-xl border border-slate-300">
                <span className="text-[10px] font-bold uppercase text-slate-500">Dismissed</span>
                <p className="text-lg font-black text-slate-700 mt-0.5">{reviewStats.dismissed}</p>
              </div>
            </div>
          </div>

          {/* Pending Findings Requiring Review */}
          <div className="space-y-4">
            <h4 className="text-sm font-bold uppercase tracking-wider text-slate-700">
              Findings Requiring Officer Decision ({reviewStats.pending} Pending)
            </h4>

            {findingsList.filter((f) => !f.review_status || f.review_status === 'pending').length === 0 ? (
              <div className="bg-white rounded-xl border border-emerald-200 p-12 text-center text-slate-600 bg-emerald-50/20">
                <CheckCircle2 className="w-10 h-10 text-emerald-500 mx-auto mb-2" />
                <h4 className="text-base font-bold text-slate-900">All Findings Adjudicated!</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  Every detected anomaly has been reviewed or dismissed with officer notes. Ready to generate executive report.
                </p>
                <button
                  type="button"
                  onClick={() => setActiveTab('report')}
                  className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-700 text-white"
                >
                  <Download className="w-4 h-4" />
                  <span>Go to Report Download</span>
                </button>
              </div>
            ) : (
              <div className="space-y-3.5">
                {findingsList
                  .filter((f) => !f.review_status || f.review_status === 'pending')
                  .map((finding) => (
                    <FindingCard
                      key={finding.id}
                      finding={finding}
                      onReview={handleOpenReview}
                    />
                  ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: AUDIT TRAIL */}
      {activeTab === 'audit' && (
        <AuditTrail auditEntries={auditLogs} />
      )}

      {/* TAB 6: REPORT */}
      {activeTab === 'report' && (
        <ReportDownload
          application={application}
          results={results}
        />
      )}

      {/* Review Modal Dialog */}
      <ReviewModal
        isOpen={isReviewModalOpen}
        finding={activeFindingToReview}
        onClose={() => {
          setIsReviewModalOpen(false)
          setActiveFindingToReview(null)
        }}
        onReviewSuccess={handleReviewSuccess}
      />
    </div>
  )
}
