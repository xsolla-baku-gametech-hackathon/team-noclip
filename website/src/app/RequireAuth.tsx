import { useEffect, useState, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { getMe, type CurrentUser } from '../auth/api';

interface Props {
  children: (user: CurrentUser) => ReactNode;
}

type Status = 'checking' | 'authed' | 'unauthed';

const RequireAuth = ({ children }: Props) => {
  const [status, setStatus] = useState<Status>('checking');
  const [user, setUser] = useState<CurrentUser | null>(null);

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then(({ user }) => {
        if (cancelled) return;
        setUser(user);
        setStatus('authed');
      })
      .catch(() => {
        if (cancelled) return;
        setStatus('unauthed');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (status === 'checking') {
    return (
      <div className="min-h-dvh bg-black flex items-center justify-center" style={{ fontFamily: '"Space Mono", monospace' }}>
        <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading interface…</p>
      </div>
    );
  }

  if (status === 'unauthed' || !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children(user)}</>;
};

export default RequireAuth;
