import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Attach restaurant tenant header if stored
  const restaurantId = localStorage.getItem('restaurant_id');
  if (restaurantId) {
    config.headers['X-Restaurant-ID'] = restaurantId;
  }

  return config;
});

// Response interceptor to automatically handle expired sessions
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const originalRequest = error.config;

    // Check if error is 401 Unauthorized and we haven't already tried retrying this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Clear all stored tokens
      localStorage.removeItem('token');
      localStorage.removeItem('access_token');

      // Redirect to login if not already there
      if (!window.location.pathname.includes('/login')) {
        const currentPath = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login?expired=true&next=${currentPath}`;
      }
    }

    return Promise.reject(error);
  }
);