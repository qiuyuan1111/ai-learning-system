import axios from 'axios'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:3000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Inject JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response Interceptor: Extract data and handle errors
api.interceptors.response.use(
  (response) => {
    // Return the response data directly (which is of type ApiResponse<T>)
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      
      // If unauthorized (401), clear local storage and redirect to home (session creation)
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('sessionId')
        if (window.location.pathname !== '/') {
          window.location.href = '/'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
