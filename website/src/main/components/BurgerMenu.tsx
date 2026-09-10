import { useState } from 'react';
import CTAButton from './CTAButton';

const NAV_LINKS = ['Work', 'About', 'Blog'];
const SOCIALS = ['Pinterest', 'Behance', 'Letterboxd'];
const CONTACT_EMAIL = 'hello@example.com';

const BurgerMenu = () => {
  const [open, setOpen] = useState(false);

  return (
    <>
      <div className="burger-wrapper">
        <div className="pl-5 pr-5 md:pr-10">
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
            <a key={link} href={`#${link.toLowerCase()}`} onClick={() => setOpen(false)}>
              {link}
            </a>
          ))}
        </nav>

        <div className="flex flex-col gap-5 mt-8">
          <a href={`mailto:${CONTACT_EMAIL}`} className="menu-email text-lg md:text-xl no-underline">
            {CONTACT_EMAIL}
          </a>
          <div className="menu-socials flex gap-6">
            {SOCIALS.map((social) => (
              <a key={social} href="#" className="text-sm underline">
                {social}
              </a>
            ))}
          </div>
        </div>

        <div className="mt-8">
          <CTAButton label="Let's talk" size="small" />
        </div>
      </div>
    </>
  );
};

export default BurgerMenu;
