import { useState, type FormEvent } from 'react';
import { Eye, EyeOff, AlertCircle } from 'lucide-react';
import { signIn } from '../../auth/client';

type Status = 'idle' | 'loading' | 'error';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const SynapseXLoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [googleNotice, setGoogleNotice] = useState(false);

  const validate = () => {
    const errors: { email?: string; password?: string } = {};
    if (!email.trim()) errors.email = 'Email is required.';
    else if (!EMAIL_PATTERN.test(email)) errors.email = 'Enter a valid email address.';
    if (!password) errors.password = 'Password is required.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setStatus('loading');
    try {
      await signIn({ email, password });
      setStatus('idle');
    } catch (err) {
      setStatus('error');
      setFormError(err instanceof Error ? err.message : 'Something went wrong.');
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate className="w-full flex flex-col gap-5">
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
            autoComplete="current-password"
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

      {formError && (
        <div role="alert" className="flex items-start gap-2 text-[12px] text-red-400">
          <AlertCircle size={14} className="shrink-0 mt-0.5" />
          <span>{formError}</span>
        </div>
      )}

      <button type="submit" disabled={status === 'loading'} aria-busy={status === 'loading'} className="synapsex-primary-btn">
        {status === 'loading' ? 'Accessing…' : 'Access interface'}
      </button>

      <div className="flex items-center gap-4 text-white/20 text-[10px] tracking-[0.18em] uppercase">
        <span className="flex-1 border-t border-white/10" />
        Or continue with
        <span className="flex-1 border-t border-white/10" />
      </div>

      <button type="button" onClick={() => setGoogleNotice(true)} className="synapsex-secondary-btn">
        Continue with Google
      </button>
      {googleNotice && (
        <p className="text-[12px] text-white/30 text-center -mt-2">Not connected yet — no provider is configured.</p>
      )}

      <p className="text-[12px] text-white/30 text-center">
        New to SynapseX?{' '}
        <a href="#" className="text-white/70 hover:text-white transition-colors">
          Create an account
        </a>
      </p>
    </form>
  );
};

export default SynapseXLoginForm;
