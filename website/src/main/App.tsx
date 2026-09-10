import './index.css';
import Splash from './components/Splash';
import Logo from './components/Logo';
import BurgerMenu from './components/BurgerMenu';
import Hero from './sections/Hero';

function MainApp() {
  return (
    <div className="bg-studio-bg text-studio-cream font-sans">
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
