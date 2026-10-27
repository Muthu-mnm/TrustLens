import React from 'react'

export default function ScoreGauge({ score = 0, riskBand = 'Low' }) {
  // Normalize score between 0 and 100
  const normalizedScore = Math.min(100, Math.max(0, Number(score) || 0))

  // Determine band and colors if not provided
  let band = riskBand
  if (!band || band === 'Unknown') {
    if (normalizedScore <= 25) band = 'Low'
    else if (normalizedScore <= 50) band = 'Medium'
    else if (normalizedScore <= 75) band = 'High'
    else band = 'Critical'
  }

  const getBandStyles = () => {
    switch (band?.toLowerCase()) {
      case 'critical':
        return {
          textColor: 'text-rose-600',
          bgColor: 'bg-rose-50',
          borderColor: 'border-rose-200',
          badgeBg: 'bg-rose-100 text-rose-800 border-rose-300',
          colorHex: '#e11d48',
          explanation: 'Severe non-compliance or document tampering detected. Immediate review and rejection risk.',
        }
      case 'high':
        return {
          textColor: 'text-orange-600',
          bgColor: 'bg-orange-50',
          borderColor: 'border-orange-200',
          badgeBg: 'bg-orange-100 text-orange-800 border-orange-300',
          colorHex: '#ea580c',
          explanation: 'Substantial discrepancies or missing critical approvals identified. Requires thorough inspection.',
        }
      case 'medium':
        return {
          textColor: 'text-amber-600',
          bgColor: 'bg-amber-50',
          borderColor: 'border-amber-200',
          badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
          colorHex: '#d97706',
          explanation: 'Moderate discrepancies or low confidence extractions requiring officer verification.',
        }
      case 'low':
      default:
        return {
          textColor: 'text-emerald-600',
          bgColor: 'bg-emerald-50',
          borderColor: 'border-emerald-200',
          badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          colorHex: '#059669',
          explanation: 'Application documents show high compliance consistency with minor or no anomalies.',
        }
    }
  }

  const style = getBandStyles()

  // SVG Gauge Math
  // Center: (100, 95), Radius: 70
  // Arc length of semi-circle = PI * 70 = 219.91
  const radius = 70
  const arcLength = Math.PI * radius
  // Offset represents how much is hidden from total arcLength
  const strokeOffset = arcLength - (normalizedScore / 100) * arcLength

  // Needle calculation
  const angleDeg = 180 + (normalizedScore / 100) * 180
  const angleRad = (angleDeg * Math.PI) / 180
  const needleLength = 52
  const needleX = 100 + needleLength * Math.cos(angleRad)
  const needleY = 95 + needleLength * Math.sin(angleRad)

  return (
    <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col items-center text-center">
      <div className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-2">
        Composite Risk Assessment
      </div>

      <div className="relative w-64 h-36 flex items-center justify-center">
        <svg viewBox="0 0 200 115" className="w-full h-full overflow-visible">
          <defs>
            {/* Color Zone Gradients */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="35%" stopColor="#f59e0b" />
              <stop offset="70%" stopColor="#f97316" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15" />
            </filter>
          </defs>

          {/* Background Track (M 25,95 A 75,75 0 0,1 175,95) */}
          <path
            d="M 30,95 A 70,70 0 0,1 170,95"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="14"
            strokeLinecap="round"
          />

          {/* Colored Segments Background */}
          {/* Low: 0-25% */}
          <path
            d="M 30,95 A 70,70 0 0,1 170,95"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${arcLength}`}
            strokeDashoffset={strokeOffset}
            className="transition-all duration-700 ease-out"
          />

          {/* Center Pivot */}
          <circle cx="100" cy="95" r="7" fill="#1e293b" />
          <circle cx="100" cy="95" r="3" fill="#ffffff" />

          {/* Needle Pointer */}
          <line
            x1="100"
            y1="95"
            x2={needleX}
            y2={needleY}
            stroke="#0f172a"
            strokeWidth="3"
            strokeLinecap="round"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Numeric Score */}
        <div className="absolute bottom-0 text-center flex flex-col items-center">
          <div className="text-3xl font-extrabold tracking-tight text-slate-900 leading-none">
            {Math.round(normalizedScore)}
            <span className="text-base font-normal text-slate-400">/100</span>
          </div>
        </div>
      </div>

      {/* Band Badge */}
      <div className="mt-3">
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${style.badgeBg}`}
        >
          {band} Risk
        </span>
      </div>

      {/* Explanation */}
      <p className="mt-3 text-xs text-slate-600 max-w-xs leading-relaxed">
        {style.explanation}
      </p>

      {/* Zone Legend */}
      <div className="w-full grid grid-cols-4 gap-1 mt-4 pt-3 border-t border-slate-100 text-[10px] text-slate-500 font-medium">
        <div className="flex flex-col items-center">
          <span className="w-2.5 h-1.5 rounded bg-emerald-500 mb-0.5"></span>
          <span>0–25 Low</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="w-2.5 h-1.5 rounded bg-amber-500 mb-0.5"></span>
          <span>26–50 Med</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="w-2.5 h-1.5 rounded bg-orange-500 mb-0.5"></span>
          <span>51–75 High</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="w-2.5 h-1.5 rounded bg-rose-500 mb-0.5"></span>
          <span>76–100 Crit</span>
        </div>
      </div>
    </div>
  )
}
