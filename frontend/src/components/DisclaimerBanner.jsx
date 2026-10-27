import React from 'react'
import { AlertTriangle, ShieldAlert } from 'lucide-react'

export default function DisclaimerBanner() {
  return (
    <div className="bg-amber-500 text-slate-950 px-4 py-2 border-b border-amber-600 shadow-sm transition-all duration-200">
      <div className="max-w-7xl mx-auto flex items-center justify-between text-xs sm:text-sm font-medium">
        <div className="flex items-center gap-2.5 mx-auto text-center md:text-left">
          <AlertTriangle className="w-4 h-4 text-slate-950 flex-shrink-0 animate-pulse" />
          <span>
            <strong className="font-bold tracking-wide">⚠️ PROTOTYPE SYSTEM</strong> — Not an official AICTE application. All findings are advisory only. Final decisions rest with authorized AICTE officers.
          </span>
        </div>
      </div>
    </div>
  )
}
