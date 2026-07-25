import { apiClient } from './client';

export interface ChatSessionMeta {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionListResponse {
  sessions: ChatSessionMeta[];
}

export const chatSessionsApi = {
  /**
   * List all chat sessions for a user
   */
  listSessions: async (userId: string, limit: number = 100): Promise<ChatSessionListResponse> => {
    return apiClient.get(`/chat_sessions?user_id=${encodeURIComponent(userId)}&limit=${limit}`);
  },

  /**
   * Create a new chat session
   */
  createSession: async (userId: string, title?: string): Promise<ChatSessionMeta> => {
    return apiClient.post('/chat_sessions', {
      user_id: userId,
      title: title || undefined
    });
  },

  /**
   * Update the title of an existing chat session
   */
  updateSession: async (sessionId: string, title: string): Promise<ChatSessionMeta> => {
    // We use fetch directly here via a small wrapper since we need PATCH which isn't in apiClient
    const token = localStorage.getItem('finvox_token');
    const response = await fetch(`${apiClient.baseURL}/chat_sessions/${sessionId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      throw new Error(`API Error (${response.status}): ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Delete a chat session
   */
  deleteSession: async (sessionId: string): Promise<{ deleted: boolean; session_id: string }> => {
    const token = localStorage.getItem('finvox_token');
    const response = await fetch(`${apiClient.baseURL}/chat_sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      }
    });

    if (!response.ok) {
      throw new Error(`API Error (${response.status}): ${response.statusText}`);
    }
    return response.json();
  },

  /**
   * Get messages for a chat session
   */
  getMessages: async (sessionId: string): Promise<any[]> => {
    return apiClient.get(`/chat_sessions/${sessionId}/messages`);
  }
};
