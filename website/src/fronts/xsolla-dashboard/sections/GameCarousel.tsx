import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Flame,
  PlayCircle,
  ChevronLeft,
  ChevronRight,
  Pickaxe,
  Sword,
  Leaf,
  Skull,
  Eye,
  type LucideIcon,
} from 'lucide-react';

interface Game {
  title: string;
  lastPlayed: string;
  image: string;
  previewBg: string;
  previewImageBg: string;
  icon: LucideIcon;
  iconGradient: string;
  story: string;
  ctaLabel: string;
}

const GAMES: Game[] = [
  {
    title: 'Minecraft',
    lastPlayed: 'Last played: 4 months ago',
    image: 'https://images.unsplash.com/photo-1612404730960-5c71577fca11?w=800&q=80',
    previewBg: 'from-blue-100 to-cyan-100',
    previewImageBg: 'bg-blue-300/30',
    icon: Pickaxe,
    iconGradient: 'from-sky-400 to-blue-600',
    story:
      "You'd just struck diamonds at Y-level -54 and were mid-build on a base overlooking the ravine when you logged off.",
    ctaLabel: 'Resume Mining',
  },
  {
    title: 'Hollow Knight',
    lastPlayed: 'Last played: 6 months ago',
    image: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=80',
    previewBg: 'from-purple-100 to-indigo-100',
    previewImageBg: 'bg-purple-300/30',
    icon: Sword,
    iconGradient: 'from-violet-400 to-indigo-600',
    story:
      "You were one dodge away from beating the Mantis Lords, sitting on 3 masks and no charms equipped for the fight.",
    ctaLabel: 'Resume Journey',
  },
  {
    title: 'Stardew Valley',
    lastPlayed: 'Last played: today',
    image: 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800&q=80',
    previewBg: 'from-amber-50 to-lime-100',
    previewImageBg: 'bg-lime-300/30',
    icon: Leaf,
    iconGradient: 'from-green-400 to-emerald-600',
    story:
      "It's Fall, Year 2. You were halfway through restoring the Greenhouse bundle and trying to romance Abigail before winter hits.",
    ctaLabel: 'Resume Playing',
  },
  {
    title: 'Undertale',
    lastPlayed: 'Last played: 1 year ago',
    image: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&q=80',
    previewBg: 'from-gray-100 to-slate-200',
    previewImageBg: 'bg-slate-400/30',
    icon: Skull,
    iconGradient: 'from-slate-500 to-slate-800',
    story:
      "You'd just spared Papyrus and were standing at the edge of Snowdin, deciding whether this run stays pacifist.",
    ctaLabel: 'Resume Run',
  },
  {
    title: 'Hello Neighbor',
    lastPlayed: 'Last played: 2 months ago',
    image: 'https://images.unsplash.com/photo-1605901309584-818e25960b8f?w=800&q=80',
    previewBg: 'from-amber-50 to-orange-100',
    previewImageBg: 'bg-orange-300/30',
    icon: Eye,
    iconGradient: 'from-red-400 to-rose-600',
    story:
      "You'd just picked the basement lock and heard footsteps on the stairs above — the neighbor was heading home early.",
    ctaLabel: 'Resume Sneaking',
  },
];

const TOTAL = GAMES.length;

const getOffset = (index: number, activeIndex: number) => {
  const raw = index - activeIndex;
  const half = Math.floor(TOTAL / 2);
  return ((raw + half + TOTAL) % TOTAL) - half;
};

const getCardTransform = (offset: number) => {
  const presets: Record<number, { x: number; z: number; rotateY: number; scale: number; opacity: number; zIndex: number }> = {
    [-2]: { x: -350, z: -200, rotateY: 25, scale: 0.8, opacity: 0.6, zIndex: 1 },
    [-1]: { x: -180, z: -100, rotateY: 15, scale: 0.9, opacity: 0.8, zIndex: 2 },
    [0]: { x: 0, z: 50, rotateY: 0, scale: 1, opacity: 1, zIndex: 3 },
    [1]: { x: 180, z: -100, rotateY: -15, scale: 0.9, opacity: 0.8, zIndex: 2 },
    [2]: { x: 350, z: -200, rotateY: -25, scale: 0.8, opacity: 0.6, zIndex: 1 },
  };
  return presets[offset];
};

const useOffsetScale = () => {
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const updateScale = () => setScale(window.innerWidth < 640 ? 0.55 : window.innerWidth < 1024 ? 0.8 : 1);
    updateScale();
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  return scale;
};

const GameCarousel = () => {
  const [activeIndex, setActiveIndex] = useState(2);
  const offsetScale = useOffsetScale();
  const activeGame = GAMES[activeIndex];
  const ActiveIcon = activeGame.icon;

  const goTo = (index: number) => setActiveIndex(((index % TOTAL) + TOTAL) % TOTAL);
  const goPrev = () => goTo(activeIndex - 1);
  const goNext = () => goTo(activeIndex + 1);

  return (
    <section className="pt-8 pb-12 flex flex-col items-center">
      <div className="text-center mb-10 px-4">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-slate-900 tracking-tight mb-4">
          Welcome Back,{' '}
          <span
            className="bg-gradient-to-r from-[#FF6B6B] to-[#FF8E53] bg-clip-text text-transparent"
            style={{ WebkitTextFillColor: 'transparent' }}
          >
            Player_One
          </span>
        </h1>
        <p className="text-base sm:text-lg text-slate-700 font-medium max-w-xl mx-auto">
          Select a game to view your "Previously On..." recap and jump right back into the action without the
          confusion.
        </p>
      </div>

      <div
        className="w-full max-w-5xl mx-auto flex items-center justify-center relative overflow-x-hidden"
        style={{ perspective: '1000px', height: '420px' }}
      >
        {GAMES.map((game, index) => {
          const offset = getOffset(index, activeIndex);
          const transform = getCardTransform(offset);
          const isActive = offset === 0;

          return (
            <motion.div
              key={game.title}
              className={`absolute w-[220px] h-[340px] sm:w-[260px] sm:h-[360px] md:w-[280px] md:h-[380px] rounded-3xl backdrop-blur-md flex flex-col p-5 sm:p-6 overflow-hidden cursor-pointer ${
                isActive
                  ? 'bg-white/95 border border-white/50 shadow-[0_30px_60px_rgba(0,0,0,0.15),0_0_0_4px_rgba(255,255,255,0.8)]'
                  : `bg-gradient-to-br ${game.previewBg} shadow-[0_20px_40px_rgba(0,0,0,0.1),inset_0_0_0_1px_rgba(255,255,255,0.5)]`
              }`}
              animate={{
                x: transform.x * offsetScale,
                z: transform.z * offsetScale,
                rotateY: transform.rotateY,
                scale: transform.scale,
                opacity: transform.opacity,
              }}
              style={{ zIndex: transform.zIndex }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              onClick={() => !isActive && goTo(index)}
            >
              {isActive ? (
                <div className="relative z-10 flex flex-col h-full">
                  <div className="flex justify-between items-start mb-6">
                    <div>
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-orange-100 text-orange-700 text-xs font-bold uppercase tracking-wider mb-2">
                        <Flame size={12} /> Ready
                      </span>
                      <h2 className="text-2xl font-black text-slate-900 leading-none">{game.title}</h2>
                    </div>
                    <div
                      className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${game.iconGradient} shadow-md flex items-center justify-center shrink-0`}
                    >
                      <ActiveIcon className="text-white" size={22} />
                    </div>
                  </div>

                  <div className="flex-1">
                    <h4 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-2">
                      Previously On...
                    </h4>
                    <p className="text-slate-700 font-medium leading-relaxed text-sm">{game.story}</p>
                  </div>

                  <div className="mt-auto pt-6">
                    <button className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-orange-500 to-pink-500 text-white font-bold text-sm shadow-[0_8px_16px_rgba(249,115,22,0.3)] hover:shadow-[0_12px_24px_rgba(249,115,22,0.4)] hover:-translate-y-1 transition-all flex items-center justify-center gap-2">
                      <PlayCircle size={18} />
                      {game.ctaLabel}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className={`h-40 rounded-xl ${game.previewImageBg} mb-4 overflow-hidden relative`}>
                    <img src={game.image} className="w-full h-full object-cover mix-blend-overlay" alt={game.title} />
                  </div>
                  <h3 className="font-bold text-lg text-slate-800">{game.title}</h3>
                  <p className="text-xs text-slate-500 mb-4">{game.lastPlayed}</p>
                </>
              )}
            </motion.div>
          );
        })}
      </div>

      <div className="flex items-center gap-4 mt-8">
        <button
          onClick={goPrev}
          className="w-10 h-10 rounded-full bg-white/60 hover:bg-white backdrop-blur-md shadow-sm flex items-center justify-center transition-all text-slate-700"
          aria-label="Previous game"
        >
          <ChevronLeft size={18} />
        </button>
        <div className="flex gap-2">
          {GAMES.map((game, index) => (
            <button
              key={game.title}
              onClick={() => goTo(index)}
              aria-label={`Go to ${game.title}`}
              className={`h-2 rounded-full transition-all ${
                index === activeIndex ? 'w-6 bg-orange-500' : 'w-2 bg-slate-400/30 hover:bg-slate-400/60'
              }`}
            />
          ))}
        </div>
        <button
          onClick={goNext}
          className="w-10 h-10 rounded-full bg-white/60 hover:bg-white backdrop-blur-md shadow-sm flex items-center justify-center transition-all text-slate-700"
          aria-label="Next game"
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </section>
  );
};

export default GameCarousel;
