import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getGameDetail, getGameSessions, getRecap, generateRecap, ApiError } from '../../auth/api';
import type { GameSummary, SessionSummary, Recap } from '../../auth/api';

function formatDuration(seconds: number | null): string {
  if (!seconds) return '—';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'long', day: 'numeric' });
}

const RecapPanel = ({ sessionId }: { sessionId: string }) => {
  const [recap, setRecap] = useState<Recap | null>(null);
  const [status, setStatus] = useState<'loading' | 'generating' | 'ready' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setStatus('loading');
    setRecap(null);
    getRecap(sessionId)
      .then(({ recap }) => {
        setRecap(recap);
        setStatus('ready');
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          generateRecap(sessionId)
            .then(({ recap }) => {
              setRecap(recap);
              setStatus('ready');
            })
            .catch((genErr) => {
              setError(genErr instanceof Error ? genErr.message : 'Failed to generate recap.');
              setStatus('error');
            });
          setStatus('generating');
          return;
        }
        setError(err instanceof Error ? err.message : 'Failed to load recap.');
        setStatus('error');
      });
  }, [sessionId]);

  if (status === 'loading') {
    return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>;
  }
  if (status === 'generating') {
    return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase animate-pulse">Rebuilding your last session…</p>;
  }
  if (status === 'error') {
    return <p className="text-red-400 text-[13px]">{error}</p>;
  }
  if (!recap) return null;

  return (
    <div className="flex flex-col gap-8 mt-6">
      <div>
        <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Previously On...</p>
        <p className="text-white/80 text-[14px] leading-relaxed">{recap.previously_on}</p>
      </div>
      {recap.priorities.length > 0 && (
        <div>
          <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Critical Priorities</p>
          <ul className="flex flex-col gap-1.5">
            {recap.priorities.map((p, i) => (
              <li key={i} className="text-white/70 text-[13px] flex gap-2">
                <span className="text-white/20">—</span> {p}
              </li>
            ))}
          </ul>
        </div>
      )}
      {recap.inventory.length > 0 && (
        <div>
          <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Inventory &amp; Goals</p>
          <ul className="flex flex-col gap-1.5">
            {recap.inventory.map((item, i) => (
              <li key={i} className="text-white/70 text-[13px] flex gap-2">
                <span className="text-white/20">—</span> {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

const GameDetail = () => {
  const { slug } = useParams<{ slug: string }>();
  const [game, setGame] = useState<GameSummary | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    Promise.all([getGameDetail(slug), getGameSessions(slug)])
      .then(([gameRes, sessionsRes]) => {
        setGame(gameRes.game);
        setSessions(sessionsRes.sessions);
        if (sessionsRes.sessions.length > 0) setSelectedSessionId(sessionsRes.sessions[0].id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load this game.'));
  }, [slug]);

  if (error) return <p className="text-red-400 text-[13px]">{error}</p>;
  if (!game || !sessions) return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>;

  return (
    <div className="flex flex-col gap-10">
      <header className="flex flex-col md:flex-row md:items-end gap-6">
        <div className="w-full md:w-48 h-28 rounded-xl overflow-hidden bg-white/5 shrink-0">
          {game.cover_image_url && <img src={game.cover_image_url} alt="" className="w-full h-full object-cover" />}
        </div>
        <div>
          <h1 className="text-[28px] md:text-[34px] font-light tracking-[-0.02em] mb-1">{game.title}</h1>
          <p className="text-white/30 text-[12px]">
            {game.total_sessions} session{game.total_sessions === 1 ? '' : 's'} synced
          </p>
        </div>
      </header>

      {sessions.length === 0 ? (
        <p className="text-white/40 text-[14px]">No captured moments yet.</p>
      ) : (
        <div className="grid md:grid-cols-[220px_1fr] gap-8">
          <div className="flex md:flex-col gap-2 overflow-x-auto md:overflow-visible">
            <p className="hidden md:block text-white/30 text-[11px] tracking-[0.2em] uppercase mb-1">Session Timeline</p>
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => setSelectedSessionId(s.id)}
                className={`text-left shrink-0 md:shrink px-3 py-2.5 rounded-lg border text-[13px] transition-colors whitespace-nowrap md:whitespace-normal ${
                  selectedSessionId === s.id
                    ? 'border-white/25 bg-white/5 text-white'
                    : 'border-white/10 text-white/50 hover:text-white/80'
                }`}
              >
                {formatDate(s.created_at)}
                <span className="block text-[11px] text-white/30 mt-0.5">{formatDuration(s.duration_seconds)}</span>
              </button>
            ))}
          </div>

          <div>{selectedSessionId && <RecapPanel key={selectedSessionId} sessionId={selectedSessionId} />}</div>
        </div>
      )}
    </div>
  );
};

export default GameDetail;
