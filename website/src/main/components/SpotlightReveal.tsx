import { useEffect, useRef } from 'react';

interface SpotlightRevealProps {
  baseImage: string;
  revealImage: string;
}

const SPOTLIGHT_RADIUS = 260;

const SpotlightReveal = ({ baseImage, revealImage }: SpotlightRevealProps) => {
  const revealRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const reveal = revealRef.current;
    if (!reveal) return;

    const mouse = { x: -999, y: -999 };
    const smooth = { x: -999, y: -999 };
    let frameId: number;

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove);

    const loop = () => {
      smooth.x += (mouse.x - smooth.x) * 0.1;
      smooth.y += (mouse.y - smooth.y) * 0.1;

      const maskGradient = `radial-gradient(circle ${SPOTLIGHT_RADIUS}px at ${smooth.x.toFixed(1)}px ${smooth.y.toFixed(1)}px, black 0%, black 40%, rgba(0,0,0,0.75) 60%, rgba(0,0,0,0.4) 75%, rgba(0,0,0,0.12) 88%, transparent 100%)`;
      reveal.style.webkitMaskImage = maskGradient;
      reveal.style.maskImage = maskGradient;

      frameId = requestAnimationFrame(loop);
    };
    frameId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <>
      <div
        className="hero-base-img hero-image-animate absolute inset-0 z-[5]"
        style={{ backgroundImage: `url('${baseImage}')` }}
      />
      <div
        ref={revealRef}
        className="hero-reveal-img absolute inset-0 pointer-events-none z-[7]"
        style={{ backgroundImage: `url('${revealImage}')` }}
      />
    </>
  );
};

export default SpotlightReveal;
