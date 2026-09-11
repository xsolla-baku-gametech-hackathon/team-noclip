import { useState, type FormEvent } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';
import CTAButton from './CTAButton';
import { signIn } from '../../auth/client';

type Status = 'idle' | 'loading' | 'error';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remember, setRemember] = useState(false);
  const [status, setStatus] = useState<Status>('idle');
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const [formError, setFormError] = useState<string | null>(null);

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
    <form onSubmit={handleSubmit} noValidate className="w-full max-w-sm flex flex-col gap-5">
      <div className="field-reveal flex flex-col gap-2" style={{ animationDelay: '0.1s' }}>
        <label htmlFor="email" className="text-sm font-medium text-studio-ink dark:text-studio-cream">
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
          className="auth-input"
          placeholder="you@example.com"
        />
        {fieldErrors.email && (
          <p id="email-error" className="text-xs text-red-600 dark:text-red-400">
            {fieldErrors.email}
          </p>
        )}
      </div>

      <div className="field-reveal flex flex-col gap-2" style={{ animationDelay: '0.2s' }}>
        <label htmlFor="password" className="text-sm font-medium text-studio-ink dark:text-studio-cream">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          aria-invalid={Boolean(fieldErrors.password)}
          aria-describedby={fieldErrors.password ? 'password-error' : undefined}
          className="auth-input"
          placeholder="••••••••"
        />
        {fieldErrors.password && (
          <p id="password-error" className="text-xs text-red-600 dark:text-red-400">
            {fieldErrors.password}
          </p>
        )}
      </div>

      <div className="field-reveal flex items-center justify-between" style={{ animationDelay: '0.3s' }}>
        <label className="flex items-center gap-2 text-sm text-studio-muted cursor-pointer">
          <input
            type="checkbox"
            checked={remember}
            onChange={(e) => setRemember(e.target.checked)}
            className="auth-checkbox"
          />
          Remember me
        </label>
        <a href="#" className="text-sm text-studio-muted hover:text-studio-ink dark:hover:text-studio-cream transition-colors">
          Forgot password?
        </a>
      </div>

      {formError && (
        <div
          role="alert"
          className="field-reveal flex items-start gap-2 text-sm text-red-600 dark:text-red-400"
        >
          <AlertCircle size={16} className="shrink-0 mt-0.5" />
          <span>{formError}</span>
        </div>
      )}

      <div className="field-reveal flex justify-center" style={{ animationDelay: '0.4s' }}>
        <CTAButton
          label={status === 'loading' ? 'Signing in…' : 'Sign In'}
          size="large"
          type="submit"
          disabled={status === 'loading'}
          ariaBusy={status === 'loading'}
        />
      </div>

      {status === 'loading' && (
        <div className="flex items-center justify-center gap-2 text-xs text-studio-muted" aria-hidden="true">
          <Loader2 size={14} className="animate-spin" />
          Checking credentials…
        </div>
      )}

      <p className="field-reveal text-sm text-studio-muted text-center" style={{ animationDelay: '0.5s' }}>
        Don't have an account?{' '}
        <a href="#" className="text-studio-ink dark:text-studio-cream font-medium hover:underline">
          Create account
        </a>
      </p>
    </form>
  );
};

export default LoginForm;
