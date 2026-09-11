import { Link } from 'react-router-dom';
import { motion, useReducedMotion } from 'framer-motion';
import SynapseXLoginForm from '../components/SynapseXLoginForm';

const EASE = [0.25, 0.46, 0.45, 0.94] as const;

const SynapseXLogo = () => (
  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M9 1L16 5V13L9 17L2 13V5L9 1Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
    <circle cx="9" cy="9" r="2.5" fill="currentColor" />
  </svg>
);

const LoginPage = () => {
  const reduceMotion = useReducedMotion();

  const fadeUp = (delay: number) => ({
    initial: reduceMotion ? false : { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.8, delay, ease: EASE },
  });

  return (
    <div
      className="min-h-dvh bg-black flex flex-col items-center justify-center px-6 py-16 overflow-x-hidden"
      style={{ fontFamily: '"Space Mono", monospace' }}
    >
      <div className="w-full max-w-md">
        <motion.div {...fadeUp(0)}>
          <Link to="/" className="inline-flex items-center gap-2 text-white/70 hover:text-white transition-colors">
            <SynapseXLogo />
            <span className="text-[15px] font-medium tracking-tight">SynapseX</span>
          </Link>
        </motion.div>

        <motion.p
          {...fadeUp(0.1)}
          className="text-white/30 text-[11px] sm:text-[12px] tracking-[0.2em] uppercase mt-6 mb-10"
        >
          Secure Access
        </motion.p>

        <motion.h1
          {...fadeUp(0.2)}
          className="text-white font-light text-[clamp(30px,5vw,48px)] leading-[1.15] tracking-[-0.02em] mb-4"
        >
          Enter the interface.
        </motion.h1>

        <motion.p {...fadeUp(0.3)} className="text-white/40 text-[14px] sm:text-[15px] leading-relaxed max-w-[360px] mb-10">
          Access your SynapseX interface and connected systems.
        </motion.p>

        <motion.div {...fadeUp(0.4)}>
          <SynapseXLoginForm />
        </motion.div>

        <motion.div {...fadeUp(0.6)} className="mt-16 text-center">
          <p className="text-white/15 text-[10px] tracking-[0.15em] uppercase">SynapseX Labs / Secure Channel</p>
          <p className="text-white/15 text-[10px] tracking-[0.15em] uppercase mt-1">© 2026 SynapseX Labs</p>
        </motion.div>
      </div>
    </div>
  );
};

export default LoginPage;
