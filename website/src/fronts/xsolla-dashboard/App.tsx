import DecorativeBackground from './components/DecorativeBackground';
import DashboardNav from './sections/DashboardNav';
import GameCarousel from './sections/GameCarousel';
import DashboardPanels from './sections/DashboardPanels';

function App() {
  return (
    <div className="min-h-screen relative">
      <DecorativeBackground />
      <DashboardNav />
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pb-20">
        <GameCarousel />
        <DashboardPanels />
      </main>
    </div>
  );
}

export default App;
