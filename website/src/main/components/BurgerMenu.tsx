import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import confetti from 'canvas-confetti';
import CTAButton from './CTAButton';
import UnderConstructionModal from './UnderConstructionModal';

const NAV_LINKS = ['Work', 'About', 'Blog'];

const fireConfetti = () => {
  confetti({
    particleCount: 120,
    spread: 90,
    origin: { y: 0.6 },
    colors: ['#75C5DE', '#F4F1E8', '#111111'],
  });
};

const BurgerMenu = () => {
  const [open, setOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const navigate = useNavigate();

  const handleNavClick = () => {
    setOpen(false);
    fireConfetti();
    setModalOpen(true);
  };

  return (
    <>
      <div className="burger-wrapper">
        <div className="flex items-center gap-3 pl-5 pr-5 md:pr-10">
          <button
            className={`burger-btn ${open ? 'open' : ''}`}
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? 'Close menu' : 'Open menu'}
          >
            <span className="bar" />
            <span className="bar" />
          </button>
        </div>
      </div>

      <div className={`menu-panel ${open ? 'open' : ''}`}>
        <nav>
          {NAV_LINKS.map((link) => (
            <button key={link} onClick={handleNavClick} className="text-left">
              {link}
            </button>
          ))}
        </nav>

        <div className="mt-8">
          <CTAButton
            label="Login"
            size="small"
            onClick={() => {
              setOpen(false);
              navigate('/login');
            }}
          />
        </div>
      </div>

      <UnderConstructionModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
};

export default BurgerMenu;
