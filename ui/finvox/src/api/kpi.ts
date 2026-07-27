import { apiClient } from './client';

export interface KPI {
  id: string;
  user_id: string;
  kpi_name: string;
  formula: string;
  target_value?: string;
  description?: string;
}

export interface KPICreateParams {
  user_id: string;
  kpi_name: string;
  formula: string;
  target_value?: string;
  description?: string;
}

export interface KPIUpdateParams {
  kpi_name?: string;
  formula?: string;
  target_value?: string;
  description?: string;
}

export const kpiApi = {
  /**
   * Fetch all KPIs for a user
   */
  getKPIs: async (userId: string): Promise<KPI[]> => {
    return await apiClient.get(`/kpis?user_id=${encodeURIComponent(userId)}`);
  },

  /**
   * Create a new KPI
   */
  createKPI: async (params: KPICreateParams): Promise<KPI> => {
    return await apiClient.post('/kpis', params);
  },

  /**
   * Update an existing KPI
   */
  updateKPI: async (kpiId: string, userId: string, params: KPIUpdateParams): Promise<KPI> => {
    return await apiClient.put(`/kpis/${encodeURIComponent(kpiId)}?user_id=${encodeURIComponent(userId)}`, params);
  },

  /**
   * Delete a KPI
   */
  deleteKPI: async (kpiId: string, userId: string): Promise<{ success: boolean; message: string }> => {
    return await apiClient.delete(`/kpis/${encodeURIComponent(kpiId)}?user_id=${encodeURIComponent(userId)}`);
  }
};
