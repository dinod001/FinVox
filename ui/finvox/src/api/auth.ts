import { apiClient } from './client';

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_id: string;
}

export const authApi = {
  /**
   * Register a new user
   * @param username The user's full name or chosen username
   * @param email The user's email address
   * @param password The chosen password
   */
  register: async (username: string, email: string, password: string): Promise<AuthResponse> => {
    return apiClient.post('/auth/register', {
      username,
      email,
      password,
    });
  },

  /**
   * Log in an existing user
   * @param usernameOrEmail The user's email or username
   * @param password The user's password
   */
  login: async (usernameOrEmail: string, password: string): Promise<AuthResponse> => {
    return apiClient.post('/auth/login', {
      username: usernameOrEmail, // The backend checks this against both username and email columns
      password,
    });
  }
};
