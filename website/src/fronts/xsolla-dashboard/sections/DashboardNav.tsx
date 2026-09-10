import { Gamepad2, Bell } from 'lucide-react';
import GlassPanel from '../components/GlassPanel';

const NAV_LINKS = ['Games', 'Analytics', 'Settings'];

const DashboardNav = () => (
  <nav className="relative z-50 flex items-center justify-between px-6 sm:px-10 py-6">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 bg-white rounded-xl shadow-lg flex items-center justify-center">
        <Gamepad2 className="text-orange-500" size={22} />
      </div>
      <span className="font-black text-xl tracking-tight text-slate-800 hidden sm:inline">Xsolla Recap</span>
    </div>

    <GlassPanel className="hidden md:flex items-center gap-6 px-6 py-3 rounded-full">
      {NAV_LINKS.map((link) => (
        <a
          key={link}
          href="#"
          className="text-sm font-semibold text-slate-700 hover:text-orange-500 transition-colors"
        >
          {link}
        </a>
      ))}
    </GlassPanel>

    <div className="flex items-center gap-4">
      <button className="w-10 h-10 rounded-full bg-white/80 hover:bg-white shadow-sm flex items-center justify-center transition-all">
        <Bell className="text-slate-600" size={18} />
      </button>
      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-orange-400 to-pink-500 border-2 border-white shadow-md" />
    </div>
  </nav>
);

export default DashboardNav;
