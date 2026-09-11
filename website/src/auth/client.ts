// Xsolla Game Recap & SynapseX Authentication Client
export const AUTH_ENDPOINT = '';

export interface Credentials {
  email: string;
  password: string;
}

export interface AuthSession {
  token: string;
  user: string;
  email: string;
}

export async function signIn(credentials: Credentials): Promise<AuthSession> {
  // Brief verification simulation
  await new Promise((resolve) => setTimeout(resolve, 400));

  const email = credentials.email.trim();
  const username = email.split('@')[0] || 'Player';
  const user = username.charAt(0).toUpperCase() + username.slice(1);
  const token = `xsolla_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`;

  const session: AuthSession = { token, user, email };
  try {
    localStorage.setItem('xsolla_auth_session', JSON.stringify(session));
  } catch {
    // Ignore storage issues if private browsing
  }
  return session;
}

export function getCurrentSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem('xsolla_auth_session');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
