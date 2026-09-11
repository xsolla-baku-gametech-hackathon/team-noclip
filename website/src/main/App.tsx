import './index.css';
import Splash from './components/Splash';
import Logo from './components/Logo';
import BurgerMenu from './components/BurgerMenu';
import Hero from './sections/Hero';
import GameCarousel from './sections/GameCarousel';

function MainApp() {
  return (
    <div className="bg-studio-bg dark:bg-studio-bg-night text-studio-cream font-sans transition-colors duration-300">
      <Splash />

      <div className="logo-wrapper">
        <div className="pl-5 md:pl-10">
          <div className="inline-flex items-center rounded-full bg-studio-cream dark:bg-studio-surface-night px-5 py-3 md:px-7 md:py-4 transition-colors duration-300">
            <Logo />
          </div>
        </div>
      </div>

      <BurgerMenu />

      <Hero />

      <GameCarousel />
    </div>
  );
}

export default MainApp;
