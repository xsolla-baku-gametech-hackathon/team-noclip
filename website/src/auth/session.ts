// Local session storage for a signed-in user. There's no backend session
// yet, so this is the browser-local source of truth for "who's signed in" —
// same honest-affordance pattern as software/auth_state.py on the desktop side.

export interface Session {
  email: string;
  name: string;
  picture?: string;
  provider: 'google';
}

const KEY = 'synapsex_session';

export function getSession(): Session | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function setSession(session: Session) {
  try {
    localStorage.setItem(KEY, JSON.stringify(session));
  } catch {
    // Storage unavailable (private browsing, etc.) — session just won't persist.
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
