// Real email/password auth, backed by api/auth/login.js and api/auth/signup.js
// — same users table and session cookie as Google Sign-In (api/auth/session.js).
import { apiFetch } from './api';
import type { CurrentUser } from './api';

export interface Credentials {
  email: string;
  password: string;
}

export async function signIn({ email, password }: Credentials): Promise<CurrentUser> {
  const { user } = await apiFetch<{ user: CurrentUser }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  return user;
}

export async function signUp({ email, password, name }: Credentials & { name?: string }): Promise<CurrentUser> {
  const { user } = await apiFetch<{ user: CurrentUser }>('/api/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, password, name }),
  });
  return user;
}
