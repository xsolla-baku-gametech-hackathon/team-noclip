import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getPublicShare, type PublicShare, ApiError } from '../../auth/api';

const SharePage = () => {
  const { shareId } = useParams<{ shareId: string }>();
  const [share, setShare] = useState<PublicShare | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!shareId) return;
    getPublicShare(shareId)
      .then(({ share }) => setShare(share))
      .catch((err) => {
        if (err instanceof ApiError) setError(err.message);
        else setError('Failed to load this share.');
      });
  }, [shareId]);

  return (
    <div className="min-h-dvh bg-black text-white px-6 py-16" style={{ fontFamily: '"Space Mono", monospace' }}>
      <div className="max-w-2xl mx-auto">
        <Link to="/" className="text-white/40 hover:text-white transition-colors text-[13px]">
          SynapseX
        </Link>

        {error && <p className="text-red-400 text-[13px] mt-10">{error}</p>}

        {!error && !share && <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase mt-10">Loading…</p>}

        {share && (
          <div className="mt-10 flex flex-col gap-10">
            <div>
              <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">{share.game_title}</p>
              <h1 className="text-[28px] font-light tracking-[-0.02em]">{share.title || 'Shared session'}</h1>
            </div>

            {share.recap && (
              <div className="flex flex-col gap-8">
                <div>
                  <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Previously On...</p>
                  <p className="text-white/80 text-[14px] leading-relaxed">{share.recap.previously_on}</p>
                </div>
                {share.recap.priorities.length > 0 && (
                  <div>
                    <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Critical Priorities</p>
                    <ul className="flex flex-col gap-1.5">
                      {share.recap.priorities.map((p, i) => (
                        <li key={i} className="text-white/70 text-[13px] flex gap-2">
                          <span className="text-white/20">—</span> {p}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {share.recap.inventory.length > 0 && (
                  <div>
                    <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Inventory &amp; Goals</p>
                    <ul className="flex flex-col gap-1.5">
                      {share.recap.inventory.map((item, i) => (
                        <li key={i} className="text-white/70 text-[13px] flex gap-2">
                          <span className="text-white/20">—</span> {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {share.media.length > 0 && (
              <div>
                <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-3">Media</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {share.media.map((m) => (
                    <div key={m.id} className="aspect-video rounded-lg overflow-hidden bg-white/5 border border-white/10">
                      {m.type === 'screenshot' ? (
                        <img src={m.url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <video src={m.url} controls className="w-full h-full object-cover" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SharePage;
