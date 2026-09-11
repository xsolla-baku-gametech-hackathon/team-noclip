import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';
import { getMyGames, type GameSummary } from '../../auth/api';

type Filter = 'all' | 'recap-available';
type Sort = 'recent' | 'most-played' | 'alphabetical';

const MyGames = () => {
  const [games, setGames] = useState<GameSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [sort, setSort] = useState<Sort>('recent');

  useEffect(() => {
    getMyGames()
      .then(({ games }) => setGames(games))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load your games.'));
  }, []);

  const visible = useMemo(() => {
    if (!games) return [];
    let list = games;
    if (query.trim()) {
      const q = query.toLowerCase();
      list = list.filter((g) => g.title.toLowerCase().includes(q));
    }
    if (filter === 'recap-available') {
      list = list.filter((g) => g.recap_count > 0);
    }
    return [...list].sort((a, b) => {
      if (sort === 'alphabetical') return a.title.localeCompare(b.title);
      if (sort === 'most-played') return b.total_sessions - a.total_sessions;
      return new Date(b.last_played_at).getTime() - new Date(a.last_played_at).getTime();
    });
  }, [games, query, filter, sort]);

  if (error) return <p className="text-red-400 text-[13px]">{error}</p>;
  if (!games) return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your games"
            className="synapsex-input pl-9"
            style={{ height: 40 }}
          />
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as Filter)}
          className="synapsex-input"
          style={{ height: 40, width: 'auto' }}
        >
          <option value="all">All games</option>
          <option value="recap-available">Recap available</option>
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as Sort)}
          className="synapsex-input"
          style={{ height: 40, width: 'auto' }}
        >
          <option value="recent">Recently played</option>
          <option value="most-played">Most played</option>
          <option value="alphabetical">A–Z</option>
        </select>
      </div>

      {games.length === 0 ? (
        <p className="text-white/40 text-[14px] max-w-md">
          Your game memory starts here — finish a session with the desktop app running and it'll appear in this
          collection.
        </p>
      ) : visible.length === 0 ? (
        <p className="text-white/40 text-[14px]">No games match that search.</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {visible.map((game) => (
            <Link
              key={game.id}
              to={`/app/games/${game.slug}`}
              className="border border-white/10 rounded-xl overflow-hidden hover:border-white/25 transition-colors group"
            >
              <div className="h-28 bg-white/5">
                {game.cover_image_url && <img src={game.cover_image_url} alt="" className="w-full h-full object-cover" />}
              </div>
              <div className="p-3">
                <p className="text-[13px] truncate group-hover:text-white text-white/80">{game.title}</p>
                <p className="text-[11px] text-white/30 mt-0.5">
                  {game.total_sessions} session{game.total_sessions === 1 ? '' : 's'}
                  {game.recap_count > 0 ? ' · recap ready' : ''}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyGames;
