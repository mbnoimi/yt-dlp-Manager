import { writable, derived } from 'svelte/store';
import { api } from '../api/client';

export interface User {
  id: number;
  username: string;
  email: string;
  avatar?: string;
  is_active: boolean;
  is_admin: boolean;
}

export const user = writable<User | null>(null);
export const isAuthenticated = derived(user, ($user) => $user !== null);
export const isAdmin = derived(user, ($user) => $user?.is_admin ?? false);

export async function loadUser() {
  const token = api.getToken();
  if (!token) {
    user.set(null);
    return;
  }

  try {
    const userData = await api.getMe();
    user.set(userData);
  } catch (error) {
    api.logout();
    user.set(null);
  }
}

export function logout() {
  api.logout();
  user.set(null);
}
