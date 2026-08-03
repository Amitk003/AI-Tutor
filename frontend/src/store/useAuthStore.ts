import { create } from 'zustand';
import { apiClient } from '../api/client';

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, user: UserProfile) => void;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem('access_token'),
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: (token: string, user: UserProfile) => {
    localStorage.setItem('access_token', token);
    set({ token, user, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    set({ token: null, user: null, isAuthenticated: false, isLoading: false });
  },

  fetchCurrentUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    set({ isLoading: true });
    try {
      const res = await apiClient.get('/auth/me');
      set({ user: res.data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem('access_token');
      set({ token: null, user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
