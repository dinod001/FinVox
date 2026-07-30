import { apiClient } from './client';

export interface Deadline {
  id: string;
  title: string;
  due_date: string;
  recurring_type: string;
  description?: string;
  created_at: string;
}

export const deadlinesApi = {
  getUpcoming: async (days: number = 14): Promise<Deadline[]> => {
    return await apiClient.get(`/api/deadlines/upcoming?days=${days}`);
  },
  getAll: async (): Promise<Deadline[]> => {
    return await apiClient.get('/api/deadlines');
  },
  create: async (data: Omit<Deadline, 'id' | 'created_at'>): Promise<Deadline> => {
    return await apiClient.post('/api/deadlines', data);
  },
  update: async (id: string, data: Omit<Deadline, 'id' | 'created_at'>): Promise<Deadline> => {
    return await apiClient.put(`/api/deadlines/${id}`, data);
  },
  delete: async (id: string): Promise<{success: boolean}> => {
    return await apiClient.delete(`/api/deadlines/${id}`);
  },
  complete: async (id: string): Promise<{action: string; next_date?: string}> => {
    return await apiClient.post(`/api/deadlines/${id}/complete`);
  }
};
