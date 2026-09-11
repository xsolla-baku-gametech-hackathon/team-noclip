import { useState, useMemo, type FormEvent } from 'react';
import { Eye, EyeOff, AlertCircle, Laptop, KeyRound, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { signIn } from '../../auth/client';
import { promptGoogleLogin, getGoogleClientId, setGoogleClientId } from '../../auth/google';

type Status = 'idle' | 'loading' | 'redirecting' | 'error';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const SynapseXLoginForm = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);

  // Google OAuth Config Modal
  const [showClientIdModal, setShowClientIdModal] = useState(false);
  const [inputClientId, setInputClientId] = useState('');

  // Check for desktop loopback redirect URL
  const redirectUrl = useMemo(() => {
    try {
      return new URLSearchParams(window.location.search).get('redirect');
    } catch {
      return null;
    }
  }, []);

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = 'Email is required.';
    else if (!EMAIL_PATTERN.test(email)) errors.email = 'Enter a valid email address.';
    if (!password) errors.password = 'Password is required.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSuccessfulAuth = (session: { token: string; user: string; email: string }) => {
    if (redirectUrl) {
      setStatus('redirecting');
      const delimiter = redirectUrl.includes('?') ? '&' : '?';
      const target = `${redirectUrl}${delimiter}token=${encodeURIComponent(session.token)}&user=${encodeURIComponent(session.user)}&email=${encodeURIComponent(session.email)}`;
      setTimeout(() => {
        window.location.href = target;
      }, 500);
    } else {
      setStatus('idle');
      navigate('/');
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setStatus('loading');
    try {
      const session = await signIn({ email, password });
      handleSuccessfulAuth(session);
    } catch (err) {
      setStatus('error');
      setFormError(err instanceof Error ? err.message : 'Something went wrong.');
    }
  };

  const executeGoogleLogin = (clientId: string) => {
    setStatus('loading');
    setFormError(null);

    promptGoogleLogin(
      clientId,
      (profile) => {
        handleSuccessfulAuth({
          token: profile.token,
          user: profile.user,
          email: profile.email,
        });
      },
      (errorMsg) => {
        setStatus('error');
        setFormError(errorMsg);
      }
    );
  };

  const handleGoogleAuth = () => {
    setFormError(null);
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
      setFormError('Please enter a valid Google Client ID.');
      return;
    }
    setGoogleClientId(clean);
    setShowClientIdModal(false);
    executeGoogleLogin(clean);
  };

  return (
    <>
      <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5">
        {redirectUrl && (
          <div className="flex items-center gap-2.5 p-3 rounded bg-[#70e1ff]/10 border border-[#70e1ff]/30 text-[12px] text-[#70e1ff]">
            <Laptop size={16} className="shrink-0" />
            <span>Connecting to desktop app <strong>Xsolla Game Recap</strong></span>
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
            onChange={(e) => {
              setEmail(e.target.value);
              if (fieldErrors.email) setFieldErrors((prev) => ({ ...prev, email: undefined }));
            }}
            placeholder="player@xsolla.com"
            className="synapsex-input"
            aria-invalid={!!fieldErrors.email}
          />
          {fieldErrors.email && (
            <p className="text-[12px] text-red-400 flex items-center gap-1.5">
              <AlertCircle size={13} />
              {fieldErrors.email}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-[10px]">
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="text-white/30 text-[11px] tracking-[0.15em] uppercase">
              Password
            </label>
            <a href="#" className="text-white/40 hover:text-white text-[11px] transition-colors">
              Forgot password?
            </a>
          </div>
          <div className="relative">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (fieldErrors.password) setFieldErrors((prev) => ({ ...prev, password: undefined }));
              }}
              placeholder="••••••••••••"
              className="synapsex-input pr-12"
              aria-invalid={!!fieldErrors.password}
            />
            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white transition-colors"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {fieldErrors.password && (
            <p className="text-[12px] text-red-400 flex items-center gap-1.5">
              <AlertCircle size={13} />
              {fieldErrors.password}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between pt-1">
          <label className="flex items-center gap-2 cursor-pointer text-white/50 text-[12px] select-none">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="w-3.5 h-3.5 rounded border border-white/20 bg-white/5 checked:bg-[#70e1ff] checked:border-[#70e1ff] transition-all"
            />
            <span>Remember device</span>
          </label>
        </div>

        {formError && (
          <div className="p-3 rounded bg-red-500/10 border border-red-500/30 text-red-300 text-[12px] flex items-start gap-2">
            <AlertCircle size={15} className="shrink-0 mt-0.5" />
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
            ? 'Accessing…'
            : 'Access interface'}
        </button>

        <div className="flex items-center gap-4 text-white/20 text-[10px] tracking-[0.18em] uppercase">
          <span className="flex-1 border-t border-white/10" />
          Or continue with
          <span className="flex-1 border-t border-white/10" />
        </div>

        <button
          type="button"
          onClick={handleGoogleAuth}
          disabled={status === 'loading' || status === 'redirecting'}
          className="synapsex-secondary-btn flex items-center justify-center gap-3 relative overflow-hidden group hover:border-[#70e1ff]/40 transition-all"
        >
          <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span className="text-[13px] font-medium text-white/90 group-hover:text-white">
            Continue with Google
          </span>
        </button>

        <p className="text-[12px] text-white/30 text-center">
          New to SynapseX?{' '}
          <a href="#" className="text-white/70 hover:text-white transition-colors">
            Create an account
          </a>
        </p>
      </form>

      {/* Google Client ID Setup Modal */}
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
                <label className="text-[11px] uppercase tracking-wider text-white/40">
                  Google Client ID
                </label>
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
                <strong>Tip:</strong> You can also set this once in your Vercel Project Environment Variables as <code>VITE_GOOGLE_CLIENT_ID</code>.
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
                  Connect & Sign In
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
