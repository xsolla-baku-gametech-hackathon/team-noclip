// Google Identity Services (GIS) Real Authentication Handler

export interface GoogleUserProfile {
  token: string;
  user: string;
  email: string;
  avatar?: string;
}

declare global {
  interface Window {
    google?: any;
  }
}

export const DEFAULT_GOOGLE_CLIENT_ID = '476389939912-j9bti4788aqhd9nf8fuin8skg0d0j353.apps.googleusercontent.com';

export function getGoogleClientId(): string {
  const envId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID;
  if (envId && envId.trim()) return envId.trim();
  try {
    const localId = localStorage.getItem('xsolla_google_client_id');
    if (localId && localId.trim()) return localId.trim();
  } catch {
    // Ignore storage errors
  }
  return DEFAULT_GOOGLE_CLIENT_ID;
}

export function setGoogleClientId(clientId: string) {
  try {
    localStorage.setItem('xsolla_google_client_id', clientId.trim());
  } catch {
    // Ignore
  }
}

// Decode base64url JWT payload
function decodeJwt(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (err) {
    console.error('[GoogleAuth] Failed to decode ID token:', err);
    return null;
  }
}

export function promptGoogleLogin(
  clientId: string,
  onSuccess: (profile: GoogleUserProfile) => void,
  onError: (errorMsg: string) => void
) {
  if (!window.google?.accounts?.oauth2 && !window.google?.accounts?.id) {
    onError('Google Identity Services library is still loading. Please try again in a moment.');
    return;
  }

  // Method 1: Token Client (OAuth popup - highly reliable across all browsers)
  if (window.google.accounts.oauth2) {
    try {
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: 'email profile openid',
        callback: async (tokenResponse: any) => {
          if (tokenResponse.error) {
            onError(`Google login failed: ${tokenResponse.error}`);
            return;
          }

          if (tokenResponse.access_token) {
            try {
              const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
              });
              if (!res.ok) throw new Error(`HTTP ${res.status}`);
              const info = await res.json();

              const profile: GoogleUserProfile = {
                token: tokenResponse.access_token,
                user: info.name || info.given_name || info.email?.split('@')[0] || 'Player',
                email: info.email,
                avatar: info.picture,
              };

              onSuccess(profile);
            } catch (err) {
              onError('Failed to fetch Google profile information.');
            }
          }
        },
      });

      client.requestAccessToken({ prompt: 'select_account' });
      return;
    } catch (err: any) {
      console.warn('[GoogleAuth] Token client failed, falling back to One Tap / ID flow:', err);
    }
  }

  // Method 2: GIS ID flow fallback
  try {
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (res: any) => {
        if (!res.credential) {
          onError('No credential returned from Google.');
          return;
        }
        const payload = decodeJwt(res.credential);
        if (!payload) {
          onError('Failed to parse Google account token.');
          return;
        }

        const profile: GoogleUserProfile = {
          token: res.credential,
          user: payload.name || payload.given_name || payload.email?.split('@')[0] || 'Player',
          email: payload.email,
          avatar: payload.picture,
        };

        onSuccess(profile);
      },
    });

    window.google.accounts.id.prompt((notification: any) => {
      if (notification.isNotDisplayed()) {
        onError('Google prompt could not be displayed. Ensure popups are allowed.');
      }
    });
  } catch (err: any) {
    onError(err.message || 'Google Sign-In initialization failed.');
  }
}
