import { Outlet, NavLink, Link, useNavigate } from 'react-router-dom';
import { LayoutGrid, Gamepad2, Sparkles, Image, Share2, Settings as SettingsIcon, LogOut } from 'lucide-react';
import type { CurrentUser } from '../auth/api';
import { logout } from '../auth/api';
import { clearSession } from '../auth/session';

interface NavItem {
  label: string;
  to: string;
  icon: typeof LayoutGrid;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', to: '/app', icon: LayoutGrid },
  { label: 'My Games', to: '/app/games', icon: Gamepad2 },
  { label: 'Recaps', to: '/app/recaps', icon: Sparkles },
  { label: 'Media', to: '/app/media', icon: Image },
  { label: 'Cloud Sharing', to: '/app/sharing', icon: Share2 },
  { label: 'Settings', to: '/app/settings', icon: SettingsIcon },
];

const AppShell = ({ user }: { user: CurrentUser }) => {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // fall through — clear the local view state regardless
    }
    clearSession();
    navigate('/login');
  };

  return (
    <div className="min-h-dvh bg-black text-white flex flex-col md:flex-row" style={{ fontFamily: '"Space Mono", monospace' }}>
      <aside className="hidden md:flex md:w-60 md:flex-col md:border-r md:border-white/10 md:px-5 md:py-6 md:gap-8">
        <Link to="/app" className="text-[15px] font-medium tracking-tight px-2">
          SynapseX
        </Link>
        <nav className="flex flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              end={item.to === '/app'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-[13px] transition-colors ${
                  isActive ? 'bg-white/10 text-white' : 'text-white/50 hover:text-white/80 hover:bg-white/5'
                }`
              }
            >
              <item.icon size={16} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto flex items-center gap-3 px-2">
          {user.picture ? (
            <img src={user.picture} alt="" className="w-8 h-8 rounded-full" referrerPolicy="no-referrer" />
          ) : (
            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-[12px]">
              {user.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <p className="text-[12px] text-white truncate">{user.name}</p>
            <p className="text-[11px] text-white/30 truncate">{user.email}</p>
          </div>
          <button onClick={handleLogout} aria-label="Sign out" className="text-white/40 hover:text-white transition-colors">
            <LogOut size={15} />
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex md:hidden items-center justify-between px-5 py-4 border-b border-white/10">
          <Link to="/app" className="text-[15px] font-medium tracking-tight">
            SynapseX
          </Link>
          <button onClick={handleLogout} aria-label="Sign out" className="text-white/40 hover:text-white transition-colors">
            <LogOut size={16} />
          </button>
        </header>

        <main className="flex-1 px-5 py-8 md:px-10 md:py-12 pb-24 md:pb-12">
          <Outlet />
        </main>

        <nav className="md:hidden fixed bottom-0 left-0 right-0 border-t border-white/10 bg-black flex items-center justify-around py-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.label}
              to={item.to}
              end={item.to === '/app'}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 px-2.5 py-1.5 text-[9px] ${isActive ? 'text-white' : 'text-white/40'}`
              }
            >
              <item.icon size={17} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default AppShell;
