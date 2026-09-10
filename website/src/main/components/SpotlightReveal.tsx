import { useEffect, useRef } from 'react';

interface SpotlightRevealProps {
  baseImage: string;
  revealImage: string;
}

const SPOTLIGHT_RADIUS = 260;

const SpotlightReveal = ({ baseImage, revealImage }: SpotlightRevealProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const revealRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const reveal = revealRef.current;
    if (!canvas || !reveal) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const mouse = { x: -999, y: -999 };
    const smooth = { x: -999, y: -999 };
    let frameId: number;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    window.addEventListener('mousemove', handleMouseMove);

    const loop = () => {
      smooth.x += (mouse.x - smooth.x) * 0.1;
      smooth.y += (mouse.y - smooth.y) * 0.1;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const grad = ctx.createRadialGradient(smooth.x, smooth.y, 0, smooth.x, smooth.y, SPOTLIGHT_RADIUS);
      grad.addColorStop(0, 'rgba(255,255,255,1)');
      grad.addColorStop(0.4, 'rgba(255,255,255,1)');
      grad.addColorStop(0.6, 'rgba(255,255,255,0.75)');
      grad.addColorStop(0.75, 'rgba(255,255,255,0.4)');
      grad.addColorStop(0.88, 'rgba(255,255,255,0.12)');
      grad.addColorStop(1, 'rgba(255,255,255,0)');

      ctx.beginPath();
      ctx.arc(smooth.x, smooth.y, SPOTLIGHT_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      const dataUrl = canvas.toDataURL();
      reveal.style.webkitMaskImage = `url(${dataUrl})`;
      reveal.style.maskImage = `url(${dataUrl})`;
      reveal.style.webkitMaskSize = '100% 100%';
      reveal.style.maskSize = '100% 100%';

      frameId = requestAnimationFrame(loop);
    };
    frameId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  return (
    <>
      <div
        className="hero-base-img hero-image-animate absolute inset-0 z-[5]"
        style={{ backgroundImage: `url('${baseImage}')` }}
      />
      <canvas ref={canvasRef} className="hidden absolute inset-0 pointer-events-none" />
      <div
        ref={revealRef}
        className="hero-reveal-img absolute inset-0 pointer-events-none z-[7]"
        style={{ backgroundImage: `url('${revealImage}')` }}
      />
    </>
  );
};

export default SpotlightReveal;
