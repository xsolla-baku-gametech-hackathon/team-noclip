import { Link } from 'react-router-dom';
import Logo from '../components/Logo';
import ThemeToggle from '../components/ThemeToggle';
import WordReveal from '../components/WordReveal';
import LoginForm from '../components/LoginForm';

// Same graphic asset used in Hero.tsx and GameCarousel.tsx — reused here per design direction.
const HERO_IMAGE =
  'https://soft-zoom-63098134.figma.site/_assets/v11/5c9f982199fde1d9b85a20e5396f0fa7bacaf9a3.png?w=2560';

const LoginPage = () => (
  <div className="min-h-screen flex flex-col bg-studio-bg dark:bg-studio-bg-night transition-colors duration-300">
    <header className="flex items-center justify-between px-5 md:px-10 py-6">
      <Logo />
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="text-sm font-medium text-studio-ink dark:text-studio-cream hover:opacity-70 transition-opacity"
        >
          Back to home
        </Link>
        <ThemeToggle />
      </div>
    </header>

    <div className="flex-1 grid md:grid-cols-2">
      <div className="relative h-[32vh] md:h-auto overflow-hidden">
        <div
          className="auth-image-animate absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url('${HERO_IMAGE}')`, backgroundPosition: '60% 20%' }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-studio-bg dark:from-studio-bg-night via-transparent to-transparent md:bg-gradient-to-r md:from-studio-bg md:dark:from-studio-bg-night md:via-transparent md:to-transparent" />

        <div className="absolute inset-0 flex flex-col justify-end p-6 md:p-12">
          <WordReveal
            text="Continue your journey."
            baseDelay={0.2}
            className="font-medium text-3xl md:text-5xl leading-[1.05] tracking-tight text-studio-ink dark:text-studio-cream max-w-md"
          />
          <p className="field-reveal mt-4 text-sm md:text-base text-studio-ink/70 dark:text-studio-cream/70 max-w-sm" style={{ animationDelay: '0.5s' }}>
            Your quests, priorities, and progress are exactly where you left them.
          </p>
        </div>
      </div>

      <div className="flex flex-col items-center justify-center px-6 py-12 md:p-16">
        <div className="w-full max-w-sm">
          <h1 className="field-reveal font-medium text-2xl md:text-3xl text-studio-ink dark:text-studio-cream mb-8">
            Sign in
          </h1>
          <LoginForm />
        </div>
      </div>
    </div>
  </div>
);

export default LoginPage;
