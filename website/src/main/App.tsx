import './index.css';
import Splash from './components/Splash';
import Logo from './components/Logo';
import BurgerMenu from './components/BurgerMenu';
import Hero from './sections/Hero';

function MainApp() {
  return (
    <div className="bg-studio-bg dark:bg-studio-bg-night text-studio-cream font-sans transition-colors duration-300">
      <Splash />

      <div className="logo-wrapper">
        <div className="pl-5 md:pl-10 text-white">
          <Logo />
        </div>
      </div>

      <BurgerMenu />

      <Hero />
    </div>
  );
}

export default MainApp;
