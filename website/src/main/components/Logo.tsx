import { Link } from 'react-router-dom';

const Logo = () => (
  <Link to="/" aria-label="Home">
    <img src="/xsolla-logo.png" alt="Xsolla" width={63} height={32} className="h-10 md:h-16 w-auto" />
  </Link>
);

export default Logo;
