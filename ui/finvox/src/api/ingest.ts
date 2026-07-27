export interface IngestionResponse {
  status: string;
  file_name: string;
  user_id: string;
  time_taken_ms: number;
  message?: string;
  doc_id?: string;
  rows_processed?: number;
}

import { apiClient } from './client';

const BASE_URL = apiClient.baseURL;
export const ingestApi = {
  uploadFile: async (
    file: File,
    userId: string,
    description: string = "",
    company: string = "",
    year: string = ""
  ): Promise<IngestionResponse> => {
    const token = localStorage.getItem('finvox_token');
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("user_id", userId);
    
    if (description) formData.append("description", description);
    if (company) formData.append("company", company);
    if (year) formData.append("year", year);

    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}/ingestion/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      let errorMsg = response.statusText;
      try {
        const data = await response.json();
        if (data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
        }
      } catch (e) {
        // Ignored
      }
      throw new Error(errorMsg);
    }

    return response.json();
  }
};
