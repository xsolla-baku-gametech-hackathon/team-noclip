import { useState } from 'react';
import { Sun, Moon } from 'lucide-react';

const readInitialIsDark = () =>
  typeof document !== 'undefined' && document.documentElement.classList.contains('dark');

const ThemeToggle = () => {
  const [isDark, setIsDark] = useState(readInitialIsDark);

  const toggle = () => {
    const next = !isDark;
    document.documentElement.classList.toggle('dark', next);
    try {
      localStorage.setItem('theme', next ? 'dark' : 'light');
    } catch {
      /* localStorage unavailable — theme just won't persist */
    }
    setIsDark(next);
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className="theme-toggle-btn"
    >
      {isDark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
};

export default ThemeToggle;
