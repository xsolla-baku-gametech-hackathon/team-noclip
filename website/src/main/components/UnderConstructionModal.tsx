import { useEffect } from 'react';
import { X, HardHat } from 'lucide-react';

interface UnderConstructionModalProps {
  open: boolean;
  onClose: () => void;
}

const UnderConstructionModal = ({ open, onClose }: UnderConstructionModalProps) => {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center px-6 bg-black/50 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="under-construction-title"
      onClick={onClose}
    >
      <div
        className="relative max-w-sm w-full bg-studio-cream dark:bg-studio-surface-night rounded-3xl p-8 text-center shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute top-4 right-4 w-8 h-8 rounded-full flex items-center justify-center text-studio-ink/50 dark:text-studio-cream/50 hover:text-studio-ink dark:hover:text-studio-cream hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
        >
          <X size={16} />
        </button>

        <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-studio-accent/20 flex items-center justify-center">
          <HardHat className="text-studio-ink dark:text-studio-cream" size={22} />
        </div>

        <h2 id="under-construction-title" className="font-medium text-xl text-studio-ink dark:text-studio-cream mb-2">
          Still under construction
        </h2>
        <p className="text-sm text-studio-ink/60 dark:text-studio-cream/60 leading-relaxed">
          This page hasn't been built yet — but the confetti was ready before the content was. Check back soon.
        </p>
      </div>
    </div>
  );
};

export default UnderConstructionModal;
