import { motion } from 'framer-motion';

interface FloatingEmoji {
  emoji: string;
  className: string;
  size: string;
  delay: number;
}

const FLOATING_EMOJI: FloatingEmoji[] = [
  { emoji: '🍣', className: 'top-1/4 left-10', size: 'text-4xl', delay: 0 },
  { emoji: '🍰', className: 'top-1/3 right-20', size: 'text-5xl', delay: 1 },
  { emoji: '🎾', className: 'bottom-1/4 left-20', size: 'text-5xl', delay: 2 },
  { emoji: '🥐', className: 'bottom-1/3 right-32', size: 'text-4xl', delay: 1.5 },
];

const floatAnimation = {
  y: [0, -20, 0],
  rotate: [0, 10, 0],
};

const DecorativeBackground = () => (
  <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
    {FLOATING_EMOJI.map(({ emoji, className, size, delay }) => (
      <motion.div
        key={emoji}
        className={`absolute ${className} ${size}`}
        style={{ filter: 'drop-shadow(0 10px 15px rgba(0,0,0,0.1))' }}
        animate={floatAnimation}
        transition={{ duration: 6, delay, repeat: Infinity, ease: 'easeInOut' }}
      >
        {emoji}
      </motion.div>
    ))}
    <div className="absolute top-20 right-1/4 w-32 h-32 bg-white/20 rounded-full blur-2xl" />
    <div className="absolute bottom-20 left-1/4 w-48 h-48 bg-pink-400/20 rounded-full blur-3xl" />
  </div>
);

export default DecorativeBackground;
