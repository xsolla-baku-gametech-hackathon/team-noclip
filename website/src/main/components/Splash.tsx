const BOX_COUNT = 5;

const Splash = () => (
  <div className="fixed inset-0 z-[100] pointer-events-none overflow-hidden flex flex-col w-screen h-screen">
    <div className="flex w-full h-1/2">
      {Array.from({ length: BOX_COUNT }).map((_, i) => (
        <div
          key={`top-${i}`}
          className="splash-box-top w-1/5 h-full bg-studio-accent"
          style={{ animationDelay: `${i * 0.05}s` }}
        />
      ))}
    </div>
    <div className="flex w-full h-1/2">
      {Array.from({ length: BOX_COUNT }).map((_, i) => (
        <div
          key={`bottom-${i}`}
          className="splash-box-bottom w-1/5 h-full bg-studio-accent"
          style={{ animationDelay: `${i * 0.05}s` }}
        />
      ))}
    </div>
  </div>
);

export default Splash;
