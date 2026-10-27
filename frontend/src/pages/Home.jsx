import React, { useEffect, useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  PlusCircle,
  Search,
  ExternalLink,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  Building,
  FileCheck2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { listApplications } from '../api/client'
import useStore from '../store/useStore'

export default function Home() {
  const navigate = useNavigate()
  const { state, setApplications, setLoading, setError } = useStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [isRefreshing, setIsRefreshing] = useState(false)

  const fetchApplicationsList = async (showToast = false) => {
    setIsRefreshing(true)
    setLoading(true)
    try {
      const response = await listApplications()
      const data = response.data || []
      setApplications(data)
      if (showToast) {
        toast.success(`Refreshed ${data.length} applications`)
      }
    } catch (err) {
      console.error('Error fetching applications:', err)
      setError(err.message)
      toast.error(err.message || 'Failed to fetch applications')
    } finally {
      setIsRefreshing(false)
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchApplicationsList()
  }, [])

  const applications = state.applications || []

  // Stats calculation
  const stats = useMemo(() => {
    const total = applications.length
    const analyzed = applications.filter(
      (a) => a.status === 'analyzed' || a.status === 'reviewed'
    ).length
    const pendingReview = applications.filter(
      (a) => a.status === 'uploaded' || a.status === 'analyzing' || (a.status === 'analyzed' && (a.finding_count || 0) > 0)
    ).length
    const highRisk = applications.filter((a) => {
      const band = (a.risk_band || '').toLowerCase()
      const score = Number(a.risk_score) || 0
      return band === 'high' || band === 'critical' || score >= 51
    }).length

    return { total, analyzed, pendingReview, highRisk }
  }, [applications])

  // Filtered applications
  const filteredApps = useMemo(() => {
    return applications.filter((app) => {
      const q = searchTerm.toLowerCase()
      const matchesSearch =
        (app.app_id || '').toLowerCase().includes(q) ||
        (app.institution_name || '').toLowerCase().includes(q) ||
        (app.app_type || '').toLowerCase().includes(q)

      const matchesStatus =
        statusFilter === 'ALL' ||
        (app.status || '').toLowerCase() === statusFilter.toLowerCase()

      return matchesSearch && matchesStatus
    })
  }, [applications, searchTerm, statusFilter])

  const getStatusBadge = (status) => {
    switch ((status || '').toLowerCase()) {
      case 'analyzed':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'reviewed':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300'
      case 'analyzing':
        return 'bg-amber-100 text-amber-800 border-amber-300 animate-pulse'
      case 'uploaded':
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300'
    }
  }

  const getRiskScoreBadge = (score, band) => {
    const s = Number(score) || 0
    let b = band
    if (!b) {
      if (s <= 25) b = 'Low'
      else if (s <= 50) b = 'Medium'
      else if (s <= 75) b = 'High'
      else b = 'Critical'
    }

    let badgeClass = 'bg-slate-100 text-slate-700 border-slate-200'
    let dotClass = 'bg-slate-400'

    const lowerBand = (b || '').toLowerCase()
    if (lowerBand === 'critical' || s >= 76) {
      badgeClass = 'bg-rose-50 text-rose-800 border-rose-300'
      dotClass = 'bg-rose-600'
    } else if (lowerBand === 'high' || s >= 51) {
      badgeClass = 'bg-orange-50 text-orange-800 border-orange-300'
      dotClass = 'bg-orange-500'
    } else if (lowerBand === 'medium' || s >= 26) {
      badgeClass = 'bg-amber-50 text-amber-800 border-amber-300'
      dotClass = 'bg-amber-500'
    } else {
      badgeClass = 'bg-emerald-50 text-emerald-800 border-emerald-300'
      dotClass = 'bg-emerald-500'
    }

    return (
      <span
        className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeClass}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`}></span>
        <span>{Math.round(s)} / 100</span>
        <span className="text-[10px] uppercase font-bold tracking-wider opacity-80">
          ({b})
        </span>
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
            Applications Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Explainable AI decision-support scrutiny for AICTE technical institution applications.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => fetchApplicationsList(true)}
            disabled={isRefreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <Link
            to="/applications/new"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Application</span>
          </Link>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Applications */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/90 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Total Applications
            </span>
            <div className="text-2xl font-black text-slate-900 mt-1">
              {stats.total}
            </div>
            <span className="text-xs text-slate-500 mt-0.5 inline-block">
              Across all categories
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center border border-blue-100">
            <Building className="w-6 h-6" />
          </div>
        </div>

        {/* Analyzed */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/90 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Scrutiny Completed
            </span>
            <div className="text-2xl font-black text-slate-900 mt-1">
              {stats.analyzed}
            </div>
            <span className="text-xs text-emerald-600 font-semibold mt-0.5 inline-block">
              Rules & ELA evaluated
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100">
            <FileCheck2 className="w-6 h-6" />
          </div>
        </div>

        {/* Pending Review */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/90 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Pending Action
            </span>
            <div className="text-2xl font-black text-slate-900 mt-1">
              {stats.pendingReview}
            </div>
            <span className="text-xs text-amber-600 font-semibold mt-0.5 inline-block">
              Requires officer attention
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* High Risk */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/90 shadow-sm flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              High / Critical Risk
            </span>
            <div className="text-2xl font-black text-rose-600 mt-1">
              {stats.highRisk}
            </div>
            <span className="text-xs text-rose-500 font-semibold mt-0.5 inline-block">
              Immediate inspection
            </span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-700 flex items-center justify-center border border-rose-100">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Applications Table Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table Filters & Search */}
        <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-50/50">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by ID, institution name, or type..."
              className="w-full pl-9 pr-3 py-2 text-xs sm:text-sm bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 text-xs font-medium bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-sm text-slate-700"
            >
              <option value="ALL">All Statuses</option>
              <option value="uploaded">Uploaded</option>
              <option value="analyzing">Analyzing</option>
              <option value="analyzed">Analyzed</option>
              <option value="reviewed">Reviewed</option>
            </select>
          </div>
        </div>

        {/* Table Content */}
        {state.isLoading && applications.length === 0 ? (
          <div className="py-16 flex flex-col items-center justify-center text-slate-500 space-y-3">
            <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm font-semibold">Loading applications registry...</p>
          </div>
        ) : filteredApps.length === 0 ? (
          <div className="py-16 px-4 text-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100 shadow-sm">
              <FileText className="w-8 h-8" />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="text-base font-bold text-slate-800">
                {applications.length === 0
                  ? 'No applications registered yet'
                  : 'No matching applications found'}
              </h3>
              <p className="text-xs text-slate-500">
                {applications.length === 0
                  ? 'Get started by creating your first AICTE scrutiny application and uploading regulatory verification dossiers.'
                  : 'Try refining your search keyword or clearing the status filter.'}
              </p>
            </div>
            {applications.length === 0 && (
              <Link
                to="/applications/new"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Create New Application</span>
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="px-4 py-3.5">App ID</th>
                  <th className="px-4 py-3.5">Institution Name</th>
                  <th className="px-4 py-3.5">Application Type</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Risk Score</th>
                  <th className="px-4 py-3.5 text-center">Docs</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {filteredApps.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => navigate(`/applications/${app.id}`)}
                    className="hover:bg-blue-50/40 transition-colors cursor-pointer group"
                  >
                    {/* App ID */}
                    <td className="px-4 py-3.5 font-mono font-bold text-blue-700">
                      {app.app_id || app.id.slice(0, 8)}
                    </td>

                    {/* Institution Name */}
                    <td className="px-4 py-3.5 font-semibold text-slate-900 max-w-xs truncate">
                      {app.institution_name}
                    </td>

                    {/* Type */}
                    <td className="px-4 py-3.5 text-slate-600">
                      <span className="bg-slate-100 px-2 py-0.5 rounded text-[11px] font-medium border border-slate-200">
                        {app.app_type || 'New Technical Inst.'}
                      </span>
                    </td>

                    {/* Status Badge */}
                    <td className="px-4 py-3.5">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold capitalize border ${getStatusBadge(
                          app.status
                        )}`}
                      >
                        {app.status || 'uploaded'}
                      </span>
                    </td>

                    {/* Risk Score */}
                    <td className="px-4 py-3.5">
                      {getRiskScoreBadge(app.risk_score, app.risk_band)}
                    </td>

                    {/* Documents Count */}
                    <td className="px-4 py-3.5 text-center font-medium text-slate-700">
                      <span className="inline-flex items-center gap-1 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        <FileText className="w-3 h-3 text-slate-500" />
                        {app.document_count ?? 0}
                      </span>
                    </td>

                    {/* Action Button */}
                    <td className="px-4 py-3.5 text-right">
                      <Link
                        to={`/applications/${app.id}`}
                        onClick={(e) => e.stopPropagation()}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-600 hover:text-white border border-blue-200 transition-colors shadow-sm"
                      >
                        <span>View</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Table Footer */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>Showing {filteredApps.length} of {applications.length} applications</span>
          <span className="font-mono text-[11px]">AICTE e-Governance Portal • TrustLens Engine</span>
        </div>
      </div>
    </div>
  )
}
