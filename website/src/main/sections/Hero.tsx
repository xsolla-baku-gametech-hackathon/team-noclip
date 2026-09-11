import { useNavigate } from 'react-router-dom';
import CTAButton from '../components/CTAButton';
import WordReveal from '../components/WordReveal';
import SpotlightReveal from '../components/SpotlightReveal';

const BASE_IMAGE =
  'https://soft-zoom-63098134.figma.site/_assets/v11/5c9f982199fde1d9b85a20e5396f0fa7bacaf9a3.png?w=2560';
const REVEAL_IMAGE =
  'https://soft-zoom-63098134.figma.site/_assets/v11/6be2165e31648955b4e071f4cf2a50bc572b9bfd.png?w=1536';

const HEADLINE = 'I build compelling visual stories & motion that make ideas shine.';

const Hero = () => {
  const navigate = useNavigate();

  return (
    <main className="hero relative w-full overflow-hidden bg-studio-bg min-h-screen md:h-screen md:min-h-[800px]">
      <div className="hero-big-text creator-text-animate absolute -bottom-[30px] md:-bottom-10 left-0 right-0 z-[2] pointer-events-none w-full text-center">
        <h2>Xsolla</h2>
      </div>

      <SpotlightReveal baseImage={BASE_IMAGE} revealImage={REVEAL_IMAGE} />

      <div className="hero-content relative z-[8] flex flex-col items-start w-full max-w-[1600px] mx-auto px-4 pt-[110px] pb-6 pointer-events-none md:absolute md:inset-0 md:justify-between md:px-10 md:pt-40 md:pb-24">
        <div className="flex flex-col items-start gap-[30px] w-full pointer-events-auto">
          <WordReveal
            text={HEADLINE}
            className="hero-headline text-[22px] md:text-[28px] font-medium leading-[120%] tracking-[-0.02em] text-studio-ink max-w-[447px]"
          />
          <div className="flex flex-wrap items-center gap-4">
            <CTAButton label="Install Xsolla Game Recap" size="large" className="cta-animate" />
            <button
              onClick={() => navigate('/login')}
              className="px-6 py-3.5 rounded-full bg-[#70e1ff] text-[#0d1117] font-bold text-[14px] hover:bg-[#38bdf8] transition-all flex items-center gap-2 shadow-lg shadow-[#70e1ff]/20 cursor-pointer"
            >
              <span>✨</span> Game Recap by Xsolla
            </button>
          </div>
        </div>
      </div>
    </main>
  );
};

export default Hero;
