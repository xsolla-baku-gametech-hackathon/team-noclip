import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMyRecaps, type RecapListItem } from '../../auth/api';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' });
}

const Recaps = () => {
  const [recaps, setRecaps] = useState<RecapListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyRecaps()
      .then(({ recaps }) => setRecaps(recaps))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load recaps.'));
  }, []);

  if (error) return <p className="text-red-400 text-[13px]">{error}</p>;
  if (!recaps) return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>;

  if (recaps.length === 0) {
    return (
      <div className="max-w-md">
        <h1 className="text-[26px] font-light tracking-[-0.02em] mb-3">No recaps yet.</h1>
        <p className="text-white/40 text-[14px] leading-relaxed">
          Play a session and your first recap will appear here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 max-w-2xl">
      <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">All Recaps</p>
      {recaps.map((recap) => (
        <Link
          key={recap.id}
          to={`/app/games/${recap.game_slug}`}
          className="border border-white/10 rounded-xl p-5 hover:border-white/25 transition-colors"
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-[15px] text-white">{recap.game_title}</p>
            <p className="text-[11px] text-white/30">{formatDate(recap.generated_at)}</p>
          </div>
          <p className="text-[13px] text-white/60 leading-relaxed line-clamp-2">{recap.previously_on}</p>
        </Link>
      ))}
    </div>
  );
};

export default Recaps;
