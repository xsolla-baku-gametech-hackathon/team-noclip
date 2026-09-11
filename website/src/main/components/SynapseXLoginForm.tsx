import { useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';
import { signIn, signUp } from '../../auth/client';
import { signInWithGoogle } from '../../auth/google';
import { setSession } from '../../auth/session';
import { approveDevicePairing, establishSession } from '../../auth/api';

type Status = 'idle' | 'loading' | 'error';
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

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = 'Email is required.';
    else if (!EMAIL_PATTERN.test(email)) errors.email = 'Enter a valid email address.';
    if (!password) errors.password = 'Password is required.';
    else if (mode === 'signup' && password.length < 8) errors.password = 'Password must be at least 8 characters.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const afterSignedIn = async () => {
    if (pairingCode) {
      await approveDevicePairing(pairingCode);
    }
    navigate('/app');
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setStatus('loading');
    try {
      if (mode === 'signup') {
        await signUp({ email, password, name });
      } else {
        await signIn({ email, password });
      }
      setStatus('idle');
      await afterSignedIn();
    } catch (err) {
      setStatus('error');
      setFormError(err instanceof Error ? err.message : 'Something went wrong.');
    }
  };

  const handleGoogleClick = async () => {
    setGoogleError(null);
    setGoogleStatus('loading');
    try {
      const profile = await signInWithGoogle();
      await establishSession(profile.accessToken);
      setSession({ email: profile.email, name: profile.name, picture: profile.picture, provider: 'google' });

      setGoogleStatus('success');
      await afterSignedIn();
    } catch (err) {
      setGoogleStatus('error');
      setGoogleError(err instanceof Error ? err.message : 'Google sign-in failed.');
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5">
      {pairingCode && (
        <div className="text-[12px] text-white/50 border border-white/10 rounded-lg px-4 py-3">
          Signing in will link this browser to your desktop app.
          <span className="block text-white/30 mt-1 tracking-widest uppercase text-[10px]">Code {pairingCode}</span>
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
        <label htmlFor="password" className="text-white/30 text-[11px] tracking-[0.15em] uppercase">
          Password
        </label>
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
          <a href="#" className="text-[12px] text-white/30 hover:text-white/60 transition-colors">
            Forgot password?
          </a>
        </div>
      )}

      {formError && (
        <div role="alert" className="flex items-start gap-2 text-[12px] text-red-400">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span>{formError}</span>
        </div>
      )}

      <button type="submit" disabled={status === 'loading'} aria-busy={status === 'loading'} className="synapsex-primary-btn">
        {status === 'loading' ? (mode === 'signup' ? 'Creating account…' : 'Accessing…') : mode === 'signup' ? 'Create account' : 'Access interface'}
      </button>

      <div className="flex items-center gap-4 text-white/20 text-[10px] tracking-[0.18em] uppercase">
        <span className="flex-1 border-t border-white/10" />
        Or continue with
        <span className="flex-1 border-t border-white/10" />
      </div>

      <button
        type="button"
        onClick={handleGoogleClick}
        disabled={googleStatus === 'loading'}
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
  );
};

export default SynapseXLoginForm;
