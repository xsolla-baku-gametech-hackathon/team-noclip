import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { getMyGames, type GameSummary } from '../../auth/api';

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

const Overview = () => {
  const [games, setGames] = useState<GameSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyGames()
      .then(({ games }) => setGames(games))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load your games.'));
  }, []);

  if (error) {
    return <p className="text-red-400 text-[13px]">{error}</p>;
  }

  if (!games) {
    return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>;
  }

  if (games.length === 0) {
    return (
      <div className="max-w-lg">
        <h1 className="text-[28px] font-light tracking-[-0.02em] mb-3">Your game memory starts here.</h1>
        <p className="text-white/40 text-[14px] leading-relaxed">
          Launch a game with the Xsolla Game Recap desktop app running, and finish a session — it'll show up here
          automatically once it syncs.
        </p>
      </div>
    );
  }

  const [mostRecent, ...rest] = games;

  return (
    <div className="flex flex-col gap-12">
      <section>
        <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-4">Continue where you left off</p>
        <div className="border border-white/10 rounded-2xl p-6 md:p-8 flex flex-col md:flex-row md:items-center gap-6 md:gap-10">
          <div className="w-full md:w-56 h-32 rounded-xl overflow-hidden bg-white/5 shrink-0">
            {mostRecent.cover_image_url && (
              <img src={mostRecent.cover_image_url} alt="" className="w-full h-full object-cover" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-[26px] md:text-[32px] font-light tracking-[-0.02em] mb-2">{mostRecent.title}</h1>
            <p className="text-white/40 text-[13px] mb-1">Last played {timeAgo(mostRecent.last_played_at)}</p>
            <p className="text-white/30 text-[12px]">
              {mostRecent.total_sessions} session{mostRecent.total_sessions === 1 ? '' : 's'} synced
            </p>
          </div>
          <Link
            to={`/app/games/${mostRecent.slug}`}
            className="synapsex-primary-btn w-full md:w-auto px-8 flex items-center justify-center gap-2 whitespace-nowrap"
          >
            View Recap <ArrowUpRight size={14} />
          </Link>
        </div>
      </section>

      {rest.length > 0 && (
        <section>
          <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-4">Recent activity</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            {rest.map((game) => (
              <Link
                key={game.id}
                to={`/app/games/${game.slug}`}
                className="border border-white/10 rounded-xl overflow-hidden hover:border-white/25 transition-colors group"
              >
                <div className="h-24 bg-white/5">
                  {game.cover_image_url && (
                    <img src={game.cover_image_url} alt="" className="w-full h-full object-cover" />
                  )}
                </div>
                <div className="p-3">
                  <p className="text-[13px] truncate group-hover:text-white text-white/80">{game.title}</p>
                  <p className="text-[11px] text-white/30 mt-0.5">{timeAgo(game.last_played_at)}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default Overview;
