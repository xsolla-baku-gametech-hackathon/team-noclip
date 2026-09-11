// Thin fetch wrapper for /api/me/* — always sends the session cookie, and
// gives callers a typed way to distinguish "not signed in" from any other
// failure so pages can redirect to /login instead of showing a generic error.

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  });

  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    // no body
  }

  if (!res.ok) {
    const message =
      body && typeof body === 'object' && 'error' in body ? String((body as { error: unknown }).error) : res.statusText;
    throw new ApiError(res.status, message);
  }

  return body as T;
}

export interface CurrentUser {
  id: string;
  email: string;
  name: string;
  picture: string | null;
}

export interface GameSummary {
  id: string;
  slug: string;
  title: string;
  cover_image_url: string | null;
  first_played_at: string;
  last_played_at: string;
  total_sessions: number;
  recap_count: number;
}

export interface SessionSummary {
  id: string;
  window_title: string | null;
  started_at: string | null;
  ended_at: string | null;
  duration_seconds: number | null;
  created_at: string;
  has_recap: boolean;
}

export interface Recap {
  previously_on: string;
  priorities: string[];
  inventory: string[];
  generated_at: string;
}

export interface RecapListItem extends Recap {
  id: string;
  session_id: string;
  game_title: string;
  game_slug: string;
}

export interface MediaItem {
  id: string;
  type: 'screenshot' | 'video';
  url: string;
  mime_type: string | null;
  size_bytes: number | null;
  duration_seconds: number | null;
  captured_at: string | null;
  created_at: string;
  game_title: string | null;
  game_slug: string | null;
}

export interface ShareListItem {
  id: string;
  title: string | null;
  media_ids: string[];
  created_at: string;
  game_title: string;
  game_slug: string;
  has_recap: boolean;
}

export interface PublicShare {
  title: string | null;
  game_title: string;
  recap: { previously_on: string; priorities: string[]; inventory: string[] } | null;
  media: Array<{ id: string; type: 'screenshot' | 'video'; url: string; duration_seconds: number | null; captured_at: string | null }>;
  created_at: string;
}

// URLs below use static filenames (api/auth.js, api/device.js, api/me.js,
// api/share.js) with a query param picking the route, not bracket-named
// path segments — this specific Vercel deployment doesn't register
// bracket-named dynamic route files ([id].js, [...x].js) as functions at
// all, verified directly against production. See api/auth.js for the story.

export const establishSession = (accessToken: string) =>
  apiFetch<{ user: CurrentUser }>('/api/auth?action=session', {
    method: 'POST',
    body: JSON.stringify({ access_token: accessToken }),
  });

export const logout = () => apiFetch<{ ok: true }>('/api/auth?action=logout', { method: 'POST' });

export const approveDevicePairing = (code: string) =>
  apiFetch<{ ok: true }>('/api/device?action=approve', {
    method: 'POST',
    body: JSON.stringify({ code }),
  });

export const getMe = () => apiFetch<{ user: CurrentUser }>('/api/me');
export const getMyGames = () => apiFetch<{ games: GameSummary[] }>('/api/me?resource=games');
export const getGameDetail = (slug: string) =>
  apiFetch<{ game: GameSummary }>(`/api/me?resource=game&slug=${encodeURIComponent(slug)}`);
export const getGameSessions = (slug: string) =>
  apiFetch<{ sessions: SessionSummary[] }>(`/api/me?resource=game-sessions&slug=${encodeURIComponent(slug)}`);
export const getRecap = (sessionId: string) =>
  apiFetch<{ recap: Recap }>(`/api/me?resource=session-recap&session_id=${encodeURIComponent(sessionId)}`);
export const generateRecap = (sessionId: string) =>
  apiFetch<{ recap: Recap }>(`/api/me?resource=session-recap&session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });

export const getMyRecaps = () => apiFetch<{ recaps: RecapListItem[] }>('/api/me?resource=recaps');

export const getMyMedia = (params?: { type?: 'screenshot' | 'video'; game?: string }) => {
  const qs = new URLSearchParams({ resource: 'media' });
  if (params?.type) qs.set('type', params.type);
  if (params?.game) qs.set('game', params.game);
  return apiFetch<{ media: MediaItem[]; next_offset: number | null }>(`/api/me?${qs.toString()}`);
};

export const getMySharePackages = () => apiFetch<{ shares: ShareListItem[] }>('/api/me?resource=share-packages');

export const createSharePackage = (input: { game_slug: string; recap_id?: string; media_ids?: string[]; title?: string }) =>
  apiFetch<{ share: { id: string; created_at: string } }>('/api/me?resource=share-packages', {
    method: 'POST',
    body: JSON.stringify(input),
  });

export const getPublicShare = (shareId: string) =>
  apiFetch<{ share: PublicShare }>(`/api/share?id=${encodeURIComponent(shareId)}`);
