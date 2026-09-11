// Real Google Sign-In via Google Identity Services' OAuth2 token client —
// a public-client implicit flow built for SPAs. No client secret is needed
// or ever exposed; only a public Client ID from Google Cloud Console.
//
// Setup (one-time, in Google Cloud Console -> APIs & Services -> Credentials):
//   1. Create an OAuth 2.0 Client ID of type "Web application".
//   2. Add Authorized JavaScript origins for both http://localhost:5183 (dev)
//      and your deployed Vercel domain.
//   3. Copy the Client ID into VITE_GOOGLE_CLIENT_ID — in website/.env.local
//      for local dev, and as a Vercel Environment Variable for production.

export interface GoogleProfile {
  email: string;
  name: string;
  picture?: string;
  accessToken: string;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: { access_token?: string; error?: string; error_description?: string }) => void;
            error_callback?: (error: { type?: string; message?: string }) => void;
          }) => { requestAccessToken: () => void };
        };
      };
    };
  }
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const SCRIPT_ID = 'google-identity-services';

let scriptPromise: Promise<void> | null = null;

function loadGoogleScript(): Promise<void> {
  if (scriptPromise) return scriptPromise;
  scriptPromise = new Promise((resolve, reject) => {
    if (document.getElementById(SCRIPT_ID)) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.id = SCRIPT_ID;
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google Identity Services.'));
    document.head.appendChild(script);
  });
  return scriptPromise;
}

export function isGoogleSignInConfigured(): boolean {
  return Boolean(GOOGLE_CLIENT_ID);
}

export async function signInWithGoogle(): Promise<GoogleProfile> {
  if (!GOOGLE_CLIENT_ID) {
    throw new Error(
      "Google Sign-In isn't configured yet — set VITE_GOOGLE_CLIENT_ID (see src/auth/google.ts for setup steps)."
    );
  }

  await loadGoogleScript();

  const google = window.google;
  if (!google?.accounts?.oauth2) {
    throw new Error('Google Identity Services failed to load.');
  }

  const accessToken = await new Promise<string>((resolve, reject) => {
    const client = google.accounts.oauth2.initTokenClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: 'openid email profile',
      callback: (response) => {
        if (response.error || !response.access_token) {
          reject(new Error(response.error_description || response.error || 'Google sign-in failed.'));
          return;
        }
        resolve(response.access_token);
      },
      error_callback: (error) => {
        reject(new Error(error?.message || 'Google sign-in was cancelled.'));
      },
    });
    client.requestAccessToken();
  });

  const res = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) {
    throw new Error('Signed in with Google, but fetching your profile failed.');
  }

  const data = await res.json();
  return { email: data.email, name: data.name, picture: data.picture, accessToken };
}
