import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || '/api',
  timeout: 60000,
  headers: {
    'Accept': 'application/json',
  }
})

// Request Interceptor
api.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// Response Interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Standardize error messaging
    const message = error.response?.data?.detail || error.response?.data?.message || error.message || 'API request failed'
    return Promise.reject(new Error(message))
  }
)

export const healthCheck = () => api.get('/health')
export const createApplication = (data) => api.post('/applications', data)
export const listApplications = () => api.get('/applications')
export const getApplication = (id) => api.get(`/applications/${id}`)
export const getDocuments = (appId) => api.get(`/applications/${appId}/documents`)
export const uploadDocuments = (appId, files) => {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  return api.post(`/applications/${appId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
export const analyzeApplication = (id) => api.post(`/applications/${id}/analyze`)
export const getResults = (id) => api.get(`/applications/${id}/results`)
export const getAudit = (id) => api.get(`/applications/${id}/audit`)
export const verifyAudit = (id) => api.get(`/applications/${id}/audit/verify`)
export const reviewFinding = (findingId, data) => api.post(`/findings/${findingId}/review`, data)
export const downloadReport = (appId) => api.get(`/applications/${appId}/report`, { responseType: 'blob' })
export const getDocumentPreview = (docId) => api.get(`/documents/${docId}/preview`)

export default api

