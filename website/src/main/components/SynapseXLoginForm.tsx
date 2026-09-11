import { useState, useMemo, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle, Laptop, KeyRound, X } from 'lucide-react';
import { signIn, signUp, getDeviceRedirectToken } from '../../auth/client';
import { promptGoogleLogin, getGoogleClientId, setGoogleClientId, type GoogleUserProfile } from '../../auth/google';
import { setSession } from '../../auth/session';
import { approveDevicePairing, establishSession } from '../../auth/api';

type Status = 'idle' | 'loading' | 'redirecting' | 'error';
type GoogleStatus = 'idle' | 'loading' | 'error' | 'success';
type Mode = 'login' | 'signup';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const GoogleLogo = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
    <path
      fill="#4285F4"
      d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.9c1.7-1.57 2.7-3.88 2.7-6.62Z"
    />
    <path
      fill="#34A853"
      d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.9-2.26c-.8.54-1.83.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.95v2.33A9 9 0 0 0 9 18Z"
    />
    <path
      fill="#FBBC05"
      d="M3.95 10.7A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.17.28-1.7V4.97H.95A9 9 0 0 0 0 9c0 1.45.35 2.83.95 4.03l3-2.33Z"
    />
    <path
      fill="#EA4335"
      d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .95 4.97l3 2.33C4.66 5.17 6.65 3.58 9 3.58Z"
    />
  </svg>
);

const SynapseXLoginForm = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const pairingCode = searchParams.get('pair');

  // Desktop loopback login (auth_server.py) passes ?redirect=http://127.0.0.1:PORT/callback.
  // Mutually exclusive with the pairing-code flow above — the desktop app uses one or the other.
  const redirectUrl = useMemo(() => {
    try {
      return new URLSearchParams(window.location.search).get('redirect');
    } catch {
      return null;
    }
  }, []);

  const [mode, setMode] = useState<Mode>('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [googleStatus, setGoogleStatus] = useState<GoogleStatus>('idle');
  const [googleError, setGoogleError] = useState<string | null>(null);

  // Google OAuth Client ID setup modal — lets a tester provide their own
  // Client ID at runtime instead of requiring VITE_GOOGLE_CLIENT_ID to be
  // set at build time.
  const [showClientIdModal, setShowClientIdModal] = useState(false);
  const [inputClientId, setInputClientId] = useState('');

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = 'Email is required.';
    else if (!EMAIL_PATTERN.test(email)) errors.email = 'Enter a valid email address.';
    if (!password) errors.password = 'Password is required.';
    else if (mode === 'signup' && password.length < 8) errors.password = 'Password must be at least 8 characters.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // After a REAL sign-in (password or Google, both already established a
  // server session by this point): link the desktop app via whichever
  // mechanism brought us here, then land the browser somewhere sensible.
  const afterSignedIn = async (user: { name: string; email: string }) => {
    if (pairingCode) {
      await approveDevicePairing(pairingCode);
      navigate('/app');
      return;
    }

    if (redirectUrl) {
      setStatus('redirecting');
      const token = await getDeviceRedirectToken();
      const delimiter = redirectUrl.includes('?') ? '&' : '?';
      const target = `${redirectUrl}${delimiter}token=${encodeURIComponent(token)}&user=${encodeURIComponent(user.name)}&email=${encodeURIComponent(user.email)}`;
      setTimeout(() => {
        window.location.href = target;
      }, 500);
      return;
    }

    navigate('/app');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setStatus('loading');
    try {
      const user = mode === 'signup' ? await signUp({ email, password, name }) : await signIn({ email, password });
      setStatus('idle');
      await afterSignedIn(user);
    } catch (err) {
      setStatus('error');
      setFormError(err instanceof Error ? err.message : 'Something went wrong.');
    }
  };

  // Google's client SDK hands back a real access token/ID token here —
  // establishSession() is what turns that into an actual server-verified
  // session (Postgres user + signed cookie), same as the password path.
  const finishGoogleLogin = async (profile: GoogleUserProfile) => {
    setGoogleStatus('loading');
    try {
      await establishSession(profile.token);
      setSession({ email: profile.email, name: profile.user, picture: profile.avatar, provider: 'google' });
      setGoogleStatus('success');
      await afterSignedIn({ name: profile.user, email: profile.email });
    } catch (err) {
      setGoogleStatus('error');
      setGoogleError(err instanceof Error ? err.message : 'Google sign-in failed.');
    }
  };

  const executeGoogleLogin = (clientId: string) => {
    setGoogleError(null);
    promptGoogleLogin(
      clientId,
      (profile) => {
        void finishGoogleLogin(profile);
      },
      (errorMsg) => {
        setGoogleStatus('error');
        setGoogleError(errorMsg);
      }
    );
  };

  const handleGoogleClick = () => {
    setGoogleError(null);
    const existingId = getGoogleClientId();
    if (!existingId) {
      setShowClientIdModal(true);
      return;
    }
    executeGoogleLogin(existingId);
  };

  const handleSaveClientIdAndLogin = (e: FormEvent) => {
    e.preventDefault();
    const clean = inputClientId.trim();
    if (!clean) {
      setGoogleError('Please enter a valid Google Client ID.');
      return;
    }
    setGoogleClientId(clean);
    setShowClientIdModal(false);
    executeGoogleLogin(clean);
  };

  return (
    <>
      <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5">
        {pairingCode && (
          <div className="text-[12px] text-white/50 border border-white/10 rounded-lg px-4 py-3">
            Signing in will link this browser to your desktop app.
            <span className="block text-white/30 mt-1 tracking-widest uppercase text-[10px]">Code {pairingCode}</span>
          </div>
        )}

        {redirectUrl && (
          <div className="flex items-center gap-2.5 p-3 rounded bg-[#70e1ff]/10 border border-[#70e1ff]/30 text-[12px] text-[#70e1ff]">
            <Laptop size={16} className="shrink-0" />
            <span>
              Connecting to desktop app <strong>Xsolla Game Recap</strong>
            </span>
          </div>
        )}

        {mode === 'signup' && (
          <div className="flex flex-col gap-[10px]">
            <label htmlFor="name" className="text-white/30 text-[11px] tracking-[0.15em] uppercase">
              Name
            </label>
            <input
              id="name"
              type="text"
              autoComplete="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="synapsex-input"
              placeholder="Your name"
            />
          </div>
        )}

        <div className="flex flex-col gap-[10px]">
          <label htmlFor="email" className="text-white/30 text-[11px] tracking-[0.15em] uppercase">
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-invalid={Boolean(fieldErrors.email)}
            aria-describedby={fieldErrors.email ? 'email-error' : undefined}
            className="synapsex-input"
            placeholder="you@example.com"
          />
          {fieldErrors.email && (
            <p id="email-error" className="text-[12px] text-red-400">
              {fieldErrors.email}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-[10px]">
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="text-white/30 text-[11px] tracking-[0.15em] uppercase">
              Password
            </label>
            {mode === 'login' && (
              <a href="#" className="text-white/40 hover:text-white text-[11px] transition-colors">
                Forgot password?
              </a>
            )}
          </div>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={Boolean(fieldErrors.password)}
              aria-describedby={fieldErrors.password ? 'password-error' : undefined}
              className="synapsex-input pr-11"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {fieldErrors.password && (
            <p id="password-error" className="text-[12px] text-red-400">
              {fieldErrors.password}
            </p>
          )}
        </div>

        {mode === 'login' && (
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-[12px] text-white/30 hover:text-white/60 transition-colors cursor-pointer">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="synapsex-checkbox"
              />
              Remember me
            </label>
          </div>
        )}

        {formError && (
          <div role="alert" className="flex items-start gap-2 text-[12px] text-red-400">
            <AlertCircle size={14} className="shrink-0 mt-0.5" />
            <span>{formError}</span>
          </div>
        )}

        <button
          type="submit"
          disabled={status === 'loading' || status === 'redirecting'}
          aria-busy={status === 'loading' || status === 'redirecting'}
          className="synapsex-primary-btn"
        >
          {status === 'redirecting'
            ? 'Returning to Game…'
            : status === 'loading'
            ? mode === 'signup'
              ? 'Creating account…'
              : 'Accessing…'
            : mode === 'signup'
            ? 'Create account'
            : 'Access interface'}
        </button>

        <div className="flex items-center gap-4 text-white/20 text-[10px] tracking-[0.18em] uppercase">
          <span className="flex-1 border-t border-white/10" />
          Or continue with
          <span className="flex-1 border-t border-white/10" />
        </div>

        <button
          type="button"
          onClick={handleGoogleClick}
          disabled={googleStatus === 'loading' || status === 'redirecting'}
          aria-busy={googleStatus === 'loading'}
          className="synapsex-secondary-btn flex items-center justify-center gap-3"
        >
          <GoogleLogo />
          {googleStatus === 'loading' ? 'Connecting…' : 'Continue with Google'}
        </button>
        {googleStatus === 'error' && googleError && (
          <p role="alert" className="text-[12px] text-red-400 text-center -mt-2">
            {googleError}
          </p>
        )}

        <p className="text-[12px] text-white/30 text-center">
          {mode === 'login' ? (
            <>
              New to SynapseX?{' '}
              <button
                type="button"
                onClick={() => {
                  setMode('signup');
                  setFormError(null);
                  setFieldErrors({});
                }}
                className="text-white/70 hover:text-white transition-colors"
              >
                Create an account
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => {
                  setMode('login');
                  setFormError(null);
                  setFieldErrors({});
                }}
                className="text-white/70 hover:text-white transition-colors"
              >
                Sign in
              </button>
            </>
          )}
        </p>
      </form>

      {showClientIdModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="relative w-full max-w-md p-6 rounded-xl bg-[#0d1117] border border-[#30363d] shadow-2xl">
            <button
              onClick={() => setShowClientIdModal(false)}
              className="absolute top-4 right-4 text-white/40 hover:text-white transition-colors"
            >
              <X size={18} />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-[#70e1ff]/10 border border-[#70e1ff]/20 flex items-center justify-center text-[#70e1ff]">
                <KeyRound size={20} />
              </div>
              <div>
                <h3 className="text-[15px] font-semibold text-white">Google OAuth Setup</h3>
                <p className="text-[12px] text-white/50">Enter your Google Cloud Client ID</p>
              </div>
            </div>

            <p className="text-[12px] text-white/70 leading-relaxed mb-4">
              To enable real Google Sign-In, paste your <strong>OAuth 2.0 Web Client ID</strong> from Google Cloud Console.
            </p>

            <form onSubmit={handleSaveClientIdAndLogin} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-[11px] uppercase tracking-wider text-white/40">Google Client ID</label>
                <input
                  type="text"
                  value={inputClientId}
                  onChange={(e) => setInputClientId(e.target.value)}
                  placeholder="xxxx-xxxxxxxx.apps.googleusercontent.com"
                  className="w-full px-3 py-2.5 rounded bg-[#161b22] border border-[#30363d] text-[12px] text-white focus:outline-none focus:border-[#70e1ff] font-mono"
                  autoFocus
                />
              </div>

              <div className="text-[11px] text-white/40 bg-white/5 p-3 rounded leading-normal">
                <strong>Tip:</strong> You can also set this once in your Vercel Project Environment Variables as{' '}
                <code>VITE_GOOGLE_CLIENT_ID</code>.
              </div>

              <div className="flex gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setShowClientIdModal(false)}
                  className="flex-1 py-2.5 px-4 rounded border border-white/10 text-white/70 hover:bg-white/5 text-[13px] font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2.5 px-4 rounded bg-[#70e1ff] text-[#0d1117] font-semibold text-[13px] hover:bg-[#38bdf8] transition-colors"
                >
                  Connect &amp; Sign In
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};

export default SynapseXLoginForm;
