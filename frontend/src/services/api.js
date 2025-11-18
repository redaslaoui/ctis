import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Trials API
export const trialsApi = {
  getAll: () => api.get('/trials'),
  getById: (id) => api.get(`/trials/${id}`),
  create: (data) => api.post('/trials', data),
  getSimilar: (id) => api.get(`/trials/similar/${id}`),
}

// Predictions API
export const predictionsApi = {
  predictRisk: (data) => api.post('/predictions/risk', data),
  getRecommendations: (data) => api.post('/predictions/recommendations', data),
}

// Monitoring API
export const monitoringApi = {
  getKPIs: (trialId) => api.get(`/monitoring/kpis/${trialId}`),
  getAlerts: (trialId) => api.get(`/monitoring/alerts/${trialId}`),
}

export default api
