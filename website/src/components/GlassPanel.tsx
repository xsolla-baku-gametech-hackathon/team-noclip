import type { ReactNode } from 'react';

interface GlassPanelProps {
  className?: string;
  children: ReactNode;
}

const GlassPanel = ({ className = '', children }: GlassPanelProps) => (
  <div className={`bg-white/70 backdrop-blur-md border border-white/50 shadow-[0_10px_30px_rgba(0,0,0,0.05)] ${className}`}>
    {children}
  </div>
);

export default GlassPanel;
