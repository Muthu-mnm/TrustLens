import React, { createContext, useContext, useReducer } from 'react'

const StoreContext = createContext(null)

const initialState = {
  applications: [],
  currentApplication: null,
  analysisResults: null,
  isLoading: false,
  error: null,
}

export const ACTION_TYPES = {
  SET_APPLICATIONS: 'SET_APPLICATIONS',
  SET_CURRENT_APPLICATION: 'SET_CURRENT_APPLICATION',
  SET_RESULTS: 'SET_RESULTS',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  UPDATE_FINDING: 'UPDATE_FINDING',
}

function storeReducer(state, action) {
  switch (action.type) {
    case ACTION_TYPES.SET_APPLICATIONS:
      return {
        ...state,
        applications: Array.isArray(action.payload) ? action.payload : [],
        isLoading: false,
        error: null,
      }
    case ACTION_TYPES.SET_CURRENT_APPLICATION:
      return { ...state, currentApplication: action.payload, isLoading: false, error: null }
    case ACTION_TYPES.SET_RESULTS:
      return { ...state, analysisResults: action.payload, isLoading: false, error: null }
    case ACTION_TYPES.SET_LOADING:
      return { ...state, isLoading: action.payload }
    case ACTION_TYPES.SET_ERROR:
      return { ...state, error: action.payload, isLoading: false }
    case ACTION_TYPES.UPDATE_FINDING: {
      const { findingId, updatedFinding } = action.payload
      let updatedResults = state.analysisResults
      if (updatedResults && Array.isArray(updatedResults.findings)) {
        updatedResults = {
          ...updatedResults,
          findings: updatedResults.findings.map((f) =>
            f.id === findingId ? { ...f, ...updatedFinding } : f
          ),
        }
      }
      let updatedApp = state.currentApplication
      if (updatedApp && Array.isArray(updatedApp.findings)) {
        updatedApp = {
          ...updatedApp,
          findings: updatedApp.findings.map((f) =>
            f.id === findingId ? { ...f, ...updatedFinding } : f
          ),
        }
      }
      return { ...state, analysisResults: updatedResults, currentApplication: updatedApp }
    }
    default:
      return state
  }
}

export function StoreProvider({ children }) {
  const [state, dispatch] = useReducer(storeReducer, initialState)

  const value = {
    state,
    dispatch,
    setApplications: (apps) => dispatch({ type: ACTION_TYPES.SET_APPLICATIONS, payload: apps }),
    setCurrentApplication: (app) => dispatch({ type: ACTION_TYPES.SET_CURRENT_APPLICATION, payload: app }),
    setResults: (results) => dispatch({ type: ACTION_TYPES.SET_RESULTS, payload: results }),
    setLoading: (isLoading) => dispatch({ type: ACTION_TYPES.SET_LOADING, payload: isLoading }),
    setError: (error) => dispatch({ type: ACTION_TYPES.SET_ERROR, payload: error }),
    updateFinding: (findingId, updatedFinding) =>
      dispatch({ type: ACTION_TYPES.UPDATE_FINDING, payload: { findingId, updatedFinding } }),
  }

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}

export function useStore() {
  const context = useContext(StoreContext)
  if (!context) {
    throw new Error('useStore must be used within a StoreProvider')
  }
  return context
}

export default useStore
