import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

// Store
import { StoreProvider } from './store/useStore'

// Layout & Components
import Sidebar from './components/Layout/Sidebar'

// Pages
import Home from './pages/Home'
import ApplicationNew from './pages/ApplicationNew'
import ApplicationDetail from './pages/ApplicationDetail'

export default function App() {
  return (
    <StoreProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-50 flex flex-col antialiased text-slate-800">
          {/* Notification Toaster */}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#0f172a',
                color: '#f8fafc',
                fontSize: '13px',
                borderRadius: '10px',
                padding: '12px 16px',
                boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.2)',
              },
              success: {
                iconTheme: {
                  primary: '#10b981',
                  secondary: '#0f172a',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#0f172a',
                },
              },
            }}
          />

          {/* Main App Layout: Sidebar + Workspace */}
          <div className="flex flex-1 overflow-hidden">
            {/* Sidebar */}
            <Sidebar />

            {/* Scrollable Main Viewport */}
            <main className="flex-1 overflow-y-auto min-h-screen p-6 lg:p-8">
              <div className="max-w-7xl mx-auto">
                <Routes>
                  <Route path="/" element={<Home />} />
                  <Route path="/applications/new" element={<ApplicationNew />} />
                  <Route path="/applications/:id" element={<ApplicationDetail />} />
                  {/* Fallback */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </div>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </StoreProvider>
  )
}
