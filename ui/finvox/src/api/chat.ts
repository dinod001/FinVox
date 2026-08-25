import { apiClient } from './client';

export interface ChatStreamCallbacks {
  onStageStart?: (stage: string, label: string) => void;
  onStageDone?: (stage: string, ms?: number) => void;
  onToken?: (token: string) => void;
  onFinal?: (downloadReport: boolean) => void;
  onDone?: () => void;
  onError?: (error: Error) => void;
}

export const chatApi = {
  /**
   * Send a message and stream the response via Server-Sent Events (SSE)
   */
  sendMessageStream: async (
    userId: string, 
    sessionId: string, 
    message: string, 
    callbacks: ChatStreamCallbacks
  ) => {
    try {
      const payload = {
        user_id: userId,
        session_id: sessionId,
        message: message
      };

      // Since we need to read the body stream, we use fetch directly
      // instead of the apiClient wrapper.
      const baseUrl = apiClient.baseURL;
      const token = localStorage.getItem('finvox_token');
      
      const response = await fetch(`${baseUrl}/chat/stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`API Error (${response.status}): ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let done = false;
      let buffer = '';

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        
        if (value) {
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last incomplete line in the buffer

          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.replace('data: ', '').trim();
              if (!dataStr) continue;
              
              try {
                const data = JSON.parse(dataStr);
                
                // Route the events to the appropriate callback
                if (data.type === 'stage_start' || data.type === 'tool_invoke') {
                  callbacks.onStageStart?.(data.stage || data.route, data.label || 'Processing...');
                } else if (data.type === 'stage_done' || data.type === 'tool_done') {
                  callbacks.onStageDone?.(data.stage || data.route, data.ms);
                } else if (data.type === 'token') {
                  callbacks.onToken?.(data.content || data.token || "");
                } else if (data.type === 'done' || data.type === 'final') {
                  callbacks.onFinal?.(data.download_report ?? false);
                  callbacks.onDone?.();
                }
              } catch (e) {
                console.error("Error parsing SSE JSON:", e, dataStr);
              }
            }
          }
        }
      }
    } catch (error: any) {
      callbacks.onError?.(error);
    }
  }
};
