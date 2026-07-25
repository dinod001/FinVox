// FinVox API Client Setup

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'; // Backend URL from .env

// Helper to get token
const getToken = () => localStorage.getItem('finvox_token');

// Helper to handle API errors properly
const handleApiError = async (response: Response) => {
  let errorMsg = response.statusText;
  try {
    const data = await response.json();
    if (data.detail) {
      errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    }
  } catch (e) {
    // Ignore JSON parse errors on non-JSON error responses
  }
  throw new Error(errorMsg);
};

export const apiClient = {
  /**
   * Perform a GET request to the backend.
   */
  get: async (endpoint: string, options: RequestInit = {}) => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
    if (!response.ok) {
      await handleApiError(response);
    }
    return response.json();
  },

  /**
   * Perform a POST request to the backend.
   */
  post: async (endpoint: string, data: any, options: RequestInit = {}) => {
    const token = getToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    };

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      ...options,
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      await handleApiError(response);
    }
    return response.json();
  },
  
  /**
   * Base URL for streaming or custom fetch requests
   */
  baseURL: BASE_URL,
};
