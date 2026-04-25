import axios from 'axios';

const defaultBaseUrl = import.meta.env.DEV
  ? 'http://127.0.0.1:8000'
  : window.location.origin;

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || defaultBaseUrl,
  timeout: 60000,
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const getErrorMessage = (error, fallback = 'Something went wrong.') => {
  return error?.response?.data?.detail || error?.message || fallback;
};

export const registerUser = (data) => API.post('/auth/register', data);
export const loginUser = (data) => API.post('/auth/login', data);
export const completeCode = (data) => API.post('/code/complete', data);
export const fixCode = (data) => API.post('/code/fix', data);
export const explainCode = (data) => API.post('/code/explain', data);
export const getHistory = () => API.get('/code/history');
