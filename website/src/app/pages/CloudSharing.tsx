import { useEffect, useState } from 'react';
import { Check, Copy, Share2 } from 'lucide-react';
import {
  getMyGames,
  getMyRecaps,
  getMyMedia,
  getMySharePackages,
  createSharePackage,
  type GameSummary,
  type RecapListItem,
  type MediaItem,
  type ShareListItem,
} from '../../auth/api';

const CloudSharing = () => {
  const [games, setGames] = useState<GameSummary[]>([]);
  const [recaps, setRecaps] = useState<RecapListItem[]>([]);
  const [media, setMedia] = useState<MediaItem[]>([]);
  const [shares, setShares] = useState<ShareListItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedGame, setSelectedGame] = useState('');
  const [selectedRecapId, setSelectedRecapId] = useState('');
  const [selectedMediaIds, setSelectedMediaIds] = useState<Set<string>>(new Set());
  const [creating, setCreating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMyGames(), getMyRecaps(), getMyMedia(), getMySharePackages()])
      .then(([g, r, m, s]) => {
        setGames(g.games);
        setRecaps(r.recaps);
        setMedia(m.media);
        setShares(s.shares);
        if (g.games.length > 0) setSelectedGame(g.games[0].slug);
        setLoaded(true);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load.'));
  }, []);

  const gameRecaps = recaps.filter((r) => r.game_slug === selectedGame);
  const gameMedia = media.filter((m) => m.game_slug === selectedGame);

  const toggleMedia = (id: string) => {
    setSelectedMediaIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleCreate = async () => {
    if (!selectedGame) return;
    setCreating(true);
    setError(null);
    try {
      const { share } = await createSharePackage({
        game_slug: selectedGame,
        recap_id: selectedRecapId || undefined,
        media_ids: Array.from(selectedMediaIds),
      });
      const { shares: refreshed } = await getMySharePackages();
      setShares(refreshed);
      setSelectedRecapId('');
      setSelectedMediaIds(new Set());
      handleCopy(share.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create share.');
    } finally {
      setCreating(false);
    }
  };

  const handleCopy = (shareId: string) => {
    const url = `${window.location.origin}/share/${shareId}`;
    navigator.clipboard?.writeText(url).catch(() => {});
    setCopiedId(shareId);
    setTimeout(() => setCopiedId((id) => (id === shareId ? null : id)), 2000);
  };

  if (!loaded) return <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>;

  if (games.length === 0) {
    return (
      <div className="max-w-md">
        <h1 className="text-[26px] font-light tracking-[-0.02em] mb-3">Nothing to share yet.</h1>
        <p className="text-white/40 text-[14px] leading-relaxed">
          Once a game syncs from the desktop app, you can bundle a recap and a few screenshots or clips into a
          shareable link here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-10 max-w-2xl">
      <section>
        <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-4">Create a share package</p>
        <div className="border border-white/10 rounded-2xl p-6 flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <label className="text-white/30 text-[11px] tracking-[0.15em] uppercase">Game</label>
            <select
              value={selectedGame}
              onChange={(e) => {
                setSelectedGame(e.target.value);
                setSelectedRecapId('');
                setSelectedMediaIds(new Set());
              }}
              className="synapsex-input"
              style={{ height: 44 }}
            >
              {games.map((g) => (
                <option key={g.slug} value={g.slug}>
                  {g.title}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-white/30 text-[11px] tracking-[0.15em] uppercase">Recap (optional)</label>
            <select value={selectedRecapId} onChange={(e) => setSelectedRecapId(e.target.value)} className="synapsex-input" style={{ height: 44 }}>
              <option value="">None</option>
              {gameRecaps.map((r) => (
                <option key={r.id} value={r.id}>
                  {new Date(r.generated_at).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          {gameMedia.length > 0 && (
            <div className="flex flex-col gap-2">
              <label className="text-white/30 text-[11px] tracking-[0.15em] uppercase">
                Media ({selectedMediaIds.size} selected)
              </label>
              <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
                {gameMedia.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => toggleMedia(m.id)}
                    className={`relative aspect-square rounded-lg overflow-hidden border-2 transition-colors ${
                      selectedMediaIds.has(m.id) ? 'border-white' : 'border-transparent'
                    }`}
                  >
                    {m.type === 'screenshot' ? (
                      <img src={m.url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <video src={m.url} className="w-full h-full object-cover" />
                    )}
                    {selectedMediaIds.has(m.id) && (
                      <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-white flex items-center justify-center">
                        <Check size={10} className="text-black" />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && <p className="text-red-400 text-[13px]">{error}</p>}

          <button onClick={handleCreate} disabled={creating} className="synapsex-primary-btn flex items-center justify-center gap-2">
            <Share2 size={14} />
            {creating ? 'Creating…' : 'Create share link'}
          </button>
        </div>
      </section>

      {shares.length > 0 && (
        <section>
          <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-4">Your shares</p>
          <div className="flex flex-col gap-2">
            {shares.map((s) => (
              <div key={s.id} className="border border-white/10 rounded-lg px-4 py-3 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-[13px] text-white truncate">{s.game_title}</p>
                  <p className="text-[11px] text-white/30">
                    {s.has_recap ? 'Recap · ' : ''}
                    {s.media_ids.length} media · {new Date(s.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => handleCopy(s.id)}
                  className="shrink-0 flex items-center gap-1.5 text-[12px] text-white/50 hover:text-white transition-colors"
                >
                  {copiedId === s.id ? <Check size={13} /> : <Copy size={13} />}
                  {copiedId === s.id ? 'Copied' : 'Copy link'}
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default CloudSharing;
