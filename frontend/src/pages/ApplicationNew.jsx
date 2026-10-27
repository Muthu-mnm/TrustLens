import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Building2,
  FileUp,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  FileText,
  ShieldCheck,
  Check,
  Loader2,
} from 'lucide-react'
import toast from 'react-hot-toast'
import FileDropzone from '../components/Upload/FileDropzone'
import { createApplication, uploadDocuments, analyzeApplication } from '../api/client'
import useStore from '../store/useStore'

const APP_TYPES = [
  'New Technical Institution',
  'Extension of Approval',
  'Increase in Intake',
  'New Program',
]

const ANALYSIS_STEPS = [
  'Extracting digital text and running OCR on scanned certificates...',
  'Computing SHA-256 signatures & perceptual hashes for duplicate detection...',
  'Executing AICTE APH compliance rule engine checks...',
  'Performing Error Level Analysis (ELA) for image tamper verification...',
  'Calculating composite risk score and synthesizing explainable findings...',
]

export default function ApplicationNew() {
  const navigate = useNavigate()
  const { setCurrentApplication } = useStore()

  // Current step: 1, 2, or 3
  const [currentStep, setCurrentStep] = useState(1)

  // Step 1 State: Details
  const [appType, setAppType] = useState('New Technical Institution')
  const [appId, setAppId] = useState('')
  const [institutionName, setInstitutionName] = useState('')
  const [isCreatingApp, setIsCreatingApp] = useState(false)
  const [createdApplication, setCreatedApplication] = useState(null)

  // Step 2 State: Files
  const [files, setFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedDocCount, setUploadedDocCount] = useState(0)

  // Step 3 State: Analysis
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisStepIndex, setAnalysisStepIndex] = useState(0)

  // STEP 1 HANDLER: Create application record
  const handleStep1Submit = async (e) => {
    e.preventDefault()
    if (!institutionName.trim()) {
      toast.error('Please enter the Institution Name')
      return
    }

    setIsCreatingApp(true)
    const toastId = toast.loading('Registering application dossier...')
    try {
      const payload = {
        app_id: appId.trim() || `AICTE-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        app_type: appType,
        institution_name: institutionName.trim(),
      }

      const response = await createApplication(payload)
      const appData = response.data
      setCreatedApplication(appData)
      setCurrentApplication(appData)
      toast.success('Application registered successfully!', { id: toastId })
      setCurrentStep(2)
    } catch (err) {
      console.error('Error creating application:', err)
      toast.error(err.message || 'Failed to register application.', { id: toastId })
    } finally {
      setIsCreatingApp(false)
    }
  }

  // STEP 2 HANDLER: Upload files
  const handleStep2Upload = async () => {
    if (!files || files.length === 0) {
      toast.error('Please select at least one document to upload.')
      return
    }

    if (!createdApplication?.id) {
      toast.error('Application reference missing. Please return to Step 1.')
      return
    }

    setIsUploading(true)
    const toastId = toast.loading(`Uploading ${files.length} document(s)...`)
    try {
      const response = await uploadDocuments(createdApplication.id, files)
      const uploadedDocs = response.data?.documents || response.data || []
      const count = Array.isArray(uploadedDocs) ? uploadedDocs.length : files.length
      setUploadedDocCount(count)
      toast.success(`Successfully uploaded ${count} documents!`, { id: toastId })
      setCurrentStep(3)
    } catch (err) {
      console.error('Error uploading documents:', err)
      toast.error(err.message || 'Document upload failed. Please try again.', { id: toastId })
    } finally {
      setIsUploading(false)
    }
  }

  // STEP 3 HANDLER: Trigger Analysis
  const handleStartAnalysis = async () => {
    if (!createdApplication?.id) return
    setIsAnalyzing(true)

    // Animated progress simulation while backend runs analysis
    const interval = setInterval(() => {
      setAnalysisStepIndex((prev) => (prev + 1) % ANALYSIS_STEPS.length)
    }, 1400)

    try {
      const response = await analyzeApplication(createdApplication.id)
      clearInterval(interval)
      toast.success('Scrutiny analysis complete!')
      // Navigate to detail page
      navigate(`/applications/${createdApplication.id}`)
    } catch (err) {
      clearInterval(interval)
      console.error('Analysis error:', err)
      toast.error(err.message || 'Analysis encountered an error.')
      setIsAnalyzing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          New Scrutiny Application
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Initiate automated document verification, OCR extraction, and regulatory cross-checks.
        </p>
      </div>

      {/* Stepper Progress Bar */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between max-w-2xl mx-auto relative">
          {/* Connector Line */}
          <div className="absolute left-8 right-8 top-1/2 -translate-y-1/2 h-0.5 bg-slate-200 -z-0">
            <div
              className="h-full bg-blue-600 transition-all duration-500"
              style={{
                width: currentStep === 1 ? '0%' : currentStep === 2 ? '50%' : '100%',
              }}
            />
          </div>

          {/* Step 1 Circle */}
          <div className="relative z-10 flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                currentStep > 1
                  ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                  : currentStep === 1
                  ? 'bg-blue-700 text-white ring-4 ring-blue-100 shadow-md shadow-blue-600/30'
                  : 'bg-slate-100 text-slate-400 border border-slate-300'
              }`}
            >
              {currentStep > 1 ? <Check className="w-5 h-5" /> : '1'}
            </div>
            <span
              className={`text-xs font-semibold mt-2 ${
                currentStep >= 1 ? 'text-slate-900' : 'text-slate-400'
              }`}
            >
              Application Details
            </span>
          </div>

          {/* Step 2 Circle */}
          <div className="relative z-10 flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                currentStep > 2
                  ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                  : currentStep === 2
                  ? 'bg-blue-700 text-white ring-4 ring-blue-100 shadow-md shadow-blue-600/30'
                  : 'bg-slate-100 text-slate-400 border border-slate-300'
              }`}
            >
              {currentStep > 2 ? <Check className="w-5 h-5" /> : '2'}
            </div>
            <span
              className={`text-xs font-semibold mt-2 ${
                currentStep >= 2 ? 'text-slate-900' : 'text-slate-400'
              }`}
            >
              Upload Documents
            </span>
          </div>

          {/* Step 3 Circle */}
          <div className="relative z-10 flex flex-col items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                currentStep === 3
                  ? 'bg-blue-700 text-white ring-4 ring-blue-100 shadow-md shadow-blue-600/30'
                  : 'bg-slate-100 text-slate-400 border border-slate-300'
              }`}
            >
              3
            </div>
            <span
              className={`text-xs font-semibold mt-2 ${
                currentStep === 3 ? 'text-slate-900' : 'text-slate-400'
              }`}
            >
              Review & Scrutiny
            </span>
          </div>
        </div>
      </div>

      {/* STEP 1: Application Details */}
      {currentStep === 1 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8">
          <form onSubmit={handleStep1Submit} className="space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-600" />
                Step 1: Application & Institution Profile
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Enter core identification parameters for this AICTE approval application.
              </p>
            </div>

            {/* Application Type */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Application Category / Scheme <span className="text-rose-500">*</span>
              </label>
              <select
                value={appType}
                onChange={(e) => setAppType(e.target.value)}
                className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-slate-800 font-medium"
              >
                {APP_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-500 mt-1">
                Select the regulatory category as per the AICTE Approval Process Handbook.
              </p>
            </div>

            {/* Application ID */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                AICTE Application ID
              </label>
              <input
                type="text"
                value={appId}
                onChange={(e) => setAppId(e.target.value)}
                placeholder="AICTE-2024-001 (or leave blank to auto-generate)"
                className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white font-mono text-slate-800 transition-all"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Official AICTE Portal application tracking reference number.
              </p>
            </div>

            {/* Institution Name */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Full Institution Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={institutionName}
                onChange={(e) => setInstitutionName(e.target.value)}
                placeholder="e.g. ABC Institute of Engineering & Technology"
                className="w-full px-4 py-2.5 text-sm bg-slate-50 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white text-slate-800 font-medium transition-all"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Ensure this exactly matches the legal name submitted in land/trust certificates.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="pt-4 border-t border-slate-100 flex items-center justify-end">
              <button
                type="submit"
                disabled={isCreatingApp}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20 disabled:opacity-50"
              >
                {isCreatingApp ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Registering...</span>
                  </>
                ) : (
                  <>
                    <span>Next: Upload Documents</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* STEP 2: Document Upload */}
      {currentStep === 2 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="border-b border-slate-100 pb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <FileUp className="w-5 h-5 text-blue-600" />
                Step 2: Upload Verification Dossiers
              </h2>
              <p className="text-xs text-slate-500 mt-1">
                Upload PDFs or high-resolution scans for Land Deeds, Society Registration, Building Plan, Fire NOC, and FDRs.
              </p>
            </div>
            {createdApplication && (
              <span className="font-mono text-xs bg-blue-50 text-blue-700 px-3 py-1 rounded-lg border border-blue-200">
                {createdApplication.app_id}
              </span>
            )}
          </div>

          {/* Dropzone component */}
          <FileDropzone
            files={files}
            onFilesChange={setFiles}
            disabled={isUploading}
          />

          {/* Action Buttons */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              type="button"
              disabled={isUploading}
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Details</span>
            </button>

            <button
              type="button"
              disabled={isUploading || files.length === 0}
              onClick={handleStep2Upload}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold bg-blue-700 text-white hover:bg-blue-800 transition-all shadow-md shadow-blue-700/20 disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Uploading {files.length} Document(s)...</span>
                </>
              ) : (
                <>
                  <span>Upload and Continue</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Review & Scrutiny */}
      {currentStep === 3 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              Step 3: Review & Initiate Scrutiny
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Verify application metadata and uploaded dossiers prior to kicking off OCR pipelines and AICTE rule verification.
            </p>
          </div>

          {/* Summary Metadata Card */}
          <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <span className="text-[11px] font-bold uppercase text-slate-400">
                  Application ID
                </span>
                <p className="text-sm font-bold text-slate-900 font-mono mt-0.5">
                  {createdApplication?.app_id}
                </p>
              </div>

              <div>
                <span className="text-[11px] font-bold uppercase text-slate-400">
                  Category
                </span>
                <p className="text-sm font-bold text-slate-900 mt-0.5">
                  {createdApplication?.app_type}
                </p>
              </div>

              <div>
                <span className="text-[11px] font-bold uppercase text-slate-400">
                  Institution Name
                </span>
                <p className="text-sm font-bold text-slate-900 mt-0.5 truncate">
                  {createdApplication?.institution_name}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <span>
                  <strong>{files.length || uploadedDocCount}</strong> document(s) uploaded and staged for ingestion.
                </span>
              </div>
              <span className="text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded font-semibold text-[11px]">
                Ready for Analysis
              </span>
            </div>
          </div>

          {/* File summary chips */}
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Ingested Document Dossiers:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {files.map((file, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg border border-slate-200 bg-white flex items-center gap-2 text-xs text-slate-700"
                >
                  <FileText className="w-4 h-4 text-red-500 flex-shrink-0" />
                  <span className="truncate font-medium flex-1">{file.name}</span>
                  <span className="text-slate-400 text-[11px]">
                    {(file.size / (1024 * 1024)).toFixed(1)} MB
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Analyzing Progress State */}
          {isAnalyzing && (
            <div className="p-6 bg-blue-50 border border-blue-200 rounded-2xl text-center space-y-4 animate-in fade-in">
              <div className="w-12 h-12 rounded-full border-4 border-blue-600 border-t-transparent animate-spin mx-auto"></div>
              <div>
                <h4 className="text-base font-bold text-blue-900">
                  TrustLens AICTE Engine Running
                </h4>
                <p className="text-xs text-blue-700 mt-1 transition-all duration-300">
                  {ANALYSIS_STEPS[analysisStepIndex]}
                </p>
              </div>
              <div className="w-full bg-blue-200 h-1.5 rounded-full overflow-hidden max-w-md mx-auto">
                <div className="bg-blue-600 h-full rounded-full animate-subtle-pulse w-3/4"></div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {!isAnalyzing && (
            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setCurrentStep(2)}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Manage Files</span>
              </button>

              <button
                type="button"
                onClick={handleStartAnalysis}
                className="inline-flex items-center gap-2 px-7 py-3 rounded-xl text-sm font-bold bg-blue-700 hover:bg-blue-800 text-white transition-all shadow-lg shadow-blue-700/25"
              >
                <Sparkles className="w-4 h-4" />
                <span>Start Scrutiny Analysis</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
