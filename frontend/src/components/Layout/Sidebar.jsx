import React from 'react'
import { NavLink } from 'react-router-dom'
import { ShieldCheck, LayoutDashboard, FilePlus2, FileText, CheckCircle2 } from 'lucide-react'

export default function Sidebar() {
  const navItems = [
    {
      to: '/',
      label: 'Dashboard',
      icon: LayoutDashboard,
      end: true,
    },
    {
      to: '/applications/new',
      label: 'New Application',
      icon: FilePlus2,
      end: false,
    },
  ]

  return (
    <aside className="w-64 bg-slate-900 text-slate-200 flex flex-col flex-shrink-0 border-r border-slate-800 select-none min-h-screen">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-700 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white flex-shrink-0">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
              TrustLens
            </h1>
            <p className="text-xs text-blue-300 font-medium tracking-wide">
              AICTE Document Scrutiny
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-6 space-y-1.5">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Scrutiny Portal
        </div>
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-700 text-white shadow-md shadow-blue-900/40 font-semibold'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`
              }
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40">
        <div className="flex items-center justify-between mb-2">
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            System Online
          </span>
          <span className="text-[11px] text-slate-400 font-mono">v1.0.0</span>
        </div>
        <div className="text-xs text-slate-400 flex items-center justify-between">
          <span>AI Decision Support</span>
          <span className="px-1.5 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-900/60 text-[10px] font-semibold">
            SIH 2026 Demo
          </span>
        </div>
      </div>
    </aside>
  )
}
