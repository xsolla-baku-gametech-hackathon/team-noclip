import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { getMyMedia, type MediaItem } from '../../auth/api';

type Tab = 'all' | 'screenshot' | 'video';

function formatDate(iso: string | null): string {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

const Media = () => {
  const [tab, setTab] = useState<Tab>('all');
  const [media, setMedia] = useState<MediaItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lightbox, setLightbox] = useState<MediaItem | null>(null);

  useEffect(() => {
    setMedia(null);
    getMyMedia(tab === 'all' ? undefined : { type: tab })
      .then(({ media }) => setMedia(media))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load media.'));
  }, [tab]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex gap-2">
        {(['all', 'screenshot', 'video'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-full text-[12px] border transition-colors ${
              tab === t ? 'bg-white text-black border-white' : 'border-white/15 text-white/50 hover:text-white/80'
            }`}
          >
            {t === 'all' ? 'All' : t === 'screenshot' ? 'Screenshots' : 'Videos'}
          </button>
        ))}
      </div>

      {error && <p className="text-red-400 text-[13px]">{error}</p>}

      {!error && !media && <p className="text-white/30 text-[12px] tracking-[0.2em] uppercase">Loading…</p>}

      {media && media.length === 0 && (
        <p className="text-white/40 text-[14px]">
          {tab === 'video' ? 'No clips from your sessions yet.' : 'No captured moments yet.'}
        </p>
      )}

      {media && media.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {media.map((item) => (
            <button
              key={item.id}
              onClick={() => setLightbox(item)}
              className="relative aspect-video rounded-lg overflow-hidden bg-white/5 border border-white/10 hover:border-white/25 transition-colors group text-left"
            >
              {item.type === 'screenshot' ? (
                <img src={item.url} alt="" loading="lazy" className="w-full h-full object-cover" />
              ) : (
                <video src={item.url} preload="metadata" className="w-full h-full object-cover" />
              )}
              {item.type === 'video' && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 group-hover:bg-black/10 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-white/90 flex items-center justify-center">
                    <div className="w-0 h-0 border-y-[5px] border-y-transparent border-l-[8px] border-l-black ml-0.5" />
                  </div>
                </div>
              )}
              <div className="absolute bottom-0 left-0 right-0 px-2 py-1 bg-gradient-to-t from-black/70 to-transparent">
                <p className="text-[10px] text-white/80 truncate">
                  {item.game_title || 'Unknown'} · {formatDate(item.captured_at || item.created_at)}
                </p>
              </div>
            </button>
          ))}
        </div>
      )}

      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-6"
          role="dialog"
          aria-modal="true"
          onClick={() => setLightbox(null)}
        >
          <button
            aria-label="Close"
            className="absolute top-5 right-5 text-white/60 hover:text-white transition-colors"
            onClick={() => setLightbox(null)}
          >
            <X size={22} />
          </button>
          <div onClick={(e) => e.stopPropagation()} className="max-w-4xl max-h-[85vh] w-full">
            {lightbox.type === 'screenshot' ? (
              <img src={lightbox.url} alt="" className="w-full h-full object-contain max-h-[85vh]" />
            ) : (
              <video src={lightbox.url} controls autoPlay className="w-full h-full max-h-[85vh]" />
            )}
            <p className="text-white/40 text-[12px] mt-3 text-center">
              {lightbox.game_title || 'Unknown'} · {formatDate(lightbox.captured_at || lightbox.created_at)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Media;
