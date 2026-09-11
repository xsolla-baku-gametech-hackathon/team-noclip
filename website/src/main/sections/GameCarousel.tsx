import { useState, useEffect, useCallback } from 'react';
import { motion, useReducedMotion, type PanInfo } from 'framer-motion';
import { Flame, ChevronLeft, ChevronRight, Pickaxe, Sword, Leaf, Skull, Eye, type LucideIcon } from 'lucide-react';
import CTAButton from '../components/CTAButton';

interface Game {
  title: string;
  lastPlayed: string;
  image: string;
  icon: LucideIcon;
  story: string;
  ctaLabel: string;
}

// Same graphic asset used in the Hero section — kept identical here per design direction.
const HERO_IMAGE = 'https://soft-zoom-63098134.figma.site/_assets/v11/5c9f982199fde1d9b85a20e5396f0fa7bacaf9a3.png?w=2560';

const GAMES: Game[] = [
  {
    title: 'Minecraft',
    lastPlayed: 'Last played: 4 months ago',
    image: HERO_IMAGE,
    icon: Pickaxe,
    story:
      "You'd just struck diamonds at Y-level -54 and were mid-build on a base overlooking the ravine when you logged off.",
    ctaLabel: 'Resume Mining',
  },
  {
    title: 'Hollow Knight',
    lastPlayed: 'Last played: 6 months ago',
    image: HERO_IMAGE,
    icon: Sword,
    story:
      "You were one dodge away from beating the Mantis Lords, sitting on 3 masks and no charms equipped for the fight.",
    ctaLabel: 'Resume Journey',
  },
  {
    title: 'Stardew Valley',
    lastPlayed: 'Last played: today',
    image: HERO_IMAGE,
    icon: Leaf,
    story:
      "It's Fall, Year 2. You were halfway through restoring the Greenhouse bundle and trying to romance Abigail before winter hits.",
    ctaLabel: 'Resume Playing',
  },
  {
    title: 'Undertale',
    lastPlayed: 'Last played: 1 year ago',
    image: HERO_IMAGE,
    icon: Skull,
    story:
      "You'd just spared Papyrus and were standing at the edge of Snowdin, deciding whether this run stays pacifist.",
    ctaLabel: 'Resume Run',
  },
  {
    title: 'Hello Neighbor',
    lastPlayed: 'Last played: 2 months ago',
    image: HERO_IMAGE,
    icon: Eye,
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

interface CardTransform {
  x: number;
  scale: number;
  opacity: number;
  zIndex: number;
}

const getCardTransform = (offset: number): CardTransform => {
  const presets: Record<number, CardTransform> = {
    [-2]: { x: -460, scale: 0.78, opacity: 0.35, zIndex: 1 },
    [-1]: { x: -260, scale: 0.88, opacity: 0.7, zIndex: 2 },
    [0]: { x: 0, scale: 1, opacity: 1, zIndex: 3 },
    [1]: { x: 260, scale: 0.88, opacity: 0.7, zIndex: 2 },
    [2]: { x: 460, scale: 0.78, opacity: 0.35, zIndex: 1 },
  };
  return presets[offset];
};

const useOffsetScale = () => {
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const updateScale = () => setScale(window.innerWidth < 640 ? 0.5 : window.innerWidth < 1024 ? 0.75 : 1);
    updateScale();
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  return scale;
};

const DRAG_THRESHOLD = 60;

const GameCarousel = () => {
  const [activeIndex, setActiveIndex] = useState(2);
  const offsetScale = useOffsetScale();
  const reduceMotion = useReducedMotion();

  const goTo = useCallback((index: number) => setActiveIndex(((index % TOTAL) + TOTAL) % TOTAL), []);
  const goPrev = useCallback(() => goTo(activeIndex - 1), [activeIndex, goTo]);
  const goNext = useCallback(() => goTo(activeIndex + 1), [activeIndex, goTo]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && ['INPUT', 'TEXTAREA'].includes(target.tagName)) return;
      if (e.key === 'ArrowLeft') goPrev();
      if (e.key === 'ArrowRight') goNext();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goPrev, goNext]);

  const handleDragEnd = (_e: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    if (info.offset.x < -DRAG_THRESHOLD) goNext();
    else if (info.offset.x > DRAG_THRESHOLD) goPrev();
  };

  const transition = reduceMotion
    ? { opacity: { duration: 0.2 }, default: { duration: 0 } }
    : { duration: 0.5, ease: [0.16, 1, 0.3, 1] as const };

  return (
    <section className="pt-8 pb-12 flex flex-col items-center" aria-roledescription="carousel" aria-label="Your games">
      <div className="text-center mb-10 px-4">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-medium text-studio-ink dark:text-studio-cream tracking-tight mb-4">
          Welcome Back, <span className="text-studio-accent">Player_One</span>
        </h1>
        <p className="text-base sm:text-lg text-studio-ink/70 dark:text-studio-cream/70 max-w-xl mx-auto">
          Select a game to view your "Previously On..." recap and jump right back into the action without the
          confusion.
        </p>
      </div>

      <motion.div
        className="w-full max-w-5xl mx-auto flex items-center justify-center relative overflow-x-hidden cursor-grab active:cursor-grabbing"
        style={{ height: '440px', touchAction: 'pan-y' }}
        drag="x"
        dragConstraints={{ left: 0, right: 0 }}
        dragElastic={0.15}
        onDragEnd={handleDragEnd}
      >
        {GAMES.map((game, index) => {
          const offset = getOffset(index, activeIndex);
          const transform = getCardTransform(offset);
          const isActive = offset === 0;
          const ActiveIcon = game.icon;

          return (
            <motion.div
              key={game.title}
              className={`absolute w-[240px] h-[380px] sm:w-[300px] sm:h-[420px] md:w-[340px] md:h-[440px] rounded-3xl flex flex-col overflow-hidden cursor-pointer select-none border ${
                isActive
                  ? 'bg-white/95 dark:bg-studio-surface-night/95 border-studio-ink/10 dark:border-studio-cream/10 shadow-[0_30px_60px_rgba(0,0,0,0.15)]'
                  : 'bg-studio-ink/[0.04] dark:bg-studio-cream/[0.04] border-studio-ink/10 dark:border-studio-cream/10 shadow-[0_20px_40px_rgba(0,0,0,0.08)]'
              }`}
              animate={{
                x: transform.x * offsetScale,
                scale: transform.scale,
                opacity: transform.opacity,
              }}
              style={{ zIndex: transform.zIndex }}
              transition={transition}
              onClick={() => !isActive && goTo(index)}
            >
              <div className="relative h-44 sm:h-52 shrink-0 overflow-hidden">
                <img
                  src={game.image}
                  loading="lazy"
                  className="w-full h-full object-cover"
                  style={{ objectPosition: '50% 15%' }}
                  alt=""
                />
                <div className="absolute inset-0 bg-gradient-to-t from-white/95 dark:from-studio-surface-night/95 via-transparent to-black/10" />
                <span className="absolute top-3 left-3 inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white/90 dark:bg-studio-surface-night/90 text-studio-ink dark:text-studio-cream text-[10px] font-bold uppercase tracking-wider">
                  <Flame size={11} className="text-studio-accent" /> Ready
                </span>
                <div className="absolute bottom-3 right-3 w-9 h-9 rounded-xl bg-studio-accent/20 backdrop-blur flex items-center justify-center">
                  <ActiveIcon className="text-studio-ink dark:text-studio-cream" size={16} />
                </div>
              </div>

              {isActive ? (
                <div className="relative z-10 flex flex-col flex-1 p-5 sm:p-6">
                  <h2 className="text-xl sm:text-2xl font-medium text-studio-ink dark:text-studio-cream leading-tight mb-3">
                    {game.title}
                  </h2>

                  <div className="flex-1">
                    <h4 className="text-xs font-bold text-studio-ink/40 dark:text-studio-cream/40 uppercase tracking-widest mb-2">
                      Previously On...
                    </h4>
                    <p className="text-studio-ink/80 dark:text-studio-cream/80 leading-relaxed text-sm">
                      {game.story}
                    </p>
                  </div>

                  <div className="mt-4 flex">
                    <CTAButton label={game.ctaLabel} size="small" />
                  </div>
                </div>
              ) : (
                <div className="p-5 sm:p-6">
                  <h3 className="font-medium text-base text-studio-ink dark:text-studio-cream">{game.title}</h3>
                  <p className="text-xs text-studio-ink/50 dark:text-studio-cream/50 mt-1">{game.lastPlayed}</p>
                </div>
              )}
            </motion.div>
          );
        })}
      </motion.div>

      <div className="flex items-center gap-4 mt-8">
        <button
          onClick={goPrev}
          className="w-10 h-10 rounded-full border border-studio-ink/10 dark:border-studio-cream/10 bg-studio-bg dark:bg-studio-bg-night hover:bg-studio-ink/5 dark:hover:bg-studio-cream/5 flex items-center justify-center transition-colors text-studio-ink dark:text-studio-cream"
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
              aria-current={index === activeIndex}
              className={`h-2 rounded-full transition-all ${
                index === activeIndex
                  ? 'w-6 bg-studio-ink dark:bg-studio-cream'
                  : 'w-2 bg-studio-ink/20 dark:bg-studio-cream/20 hover:bg-studio-ink/40 dark:hover:bg-studio-cream/40'
              }`}
            />
          ))}
        </div>
        <button
          onClick={goNext}
          className="w-10 h-10 rounded-full border border-studio-ink/10 dark:border-studio-cream/10 bg-studio-bg dark:bg-studio-bg-night hover:bg-studio-ink/5 dark:hover:bg-studio-cream/5 flex items-center justify-center transition-colors text-studio-ink dark:text-studio-cream"
          aria-label="Next game"
        >
          <ChevronRight size={18} />
        </button>
      </div>
    </section>
  );
};

export default GameCarousel;
