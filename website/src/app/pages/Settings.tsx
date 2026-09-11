import { useState, useEffect } from 'react';
import { Film, Monitor, Sliders, RefreshCw, CheckCircle2, Info } from 'lucide-react';

interface RecordingSettings {
  recording_fps: number;
  video_format: string;
  include_gamebar_in_recording: boolean;
  resolution: string;
  updated_at?: string;
}

const FPS_OPTIONS = [
  { value: 20, label: '20 FPS', desc: 'Eco / Low CPU footprint' },
  { value: 30, label: '30 FPS', desc: 'Standard Gaming (Recommended)' },
  { value: 60, label: '60 FPS', desc: 'Ultra Smooth / High Performance' },
];

const Settings = () => {
  const [settings, setSettings] = useState<RecordingSettings>({
    recording_fps: 30,
    video_format: 'mp4',
    include_gamebar_in_recording: true,
    resolution: 'native',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/settings')
      .then((res) => res.json())
      .then((data) => {
        if (data.settings) {
          setSettings(data.settings);
        }
      })
      .catch((err) => {
        console.warn('Failed to fetch settings from API, using defaults:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  const saveSettings = async (nextSettings: RecordingSettings) => {
    setSettings(nextSettings);
    setSaving(true);
    setSavedMessage(null);

    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: nextSettings }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.settings) setSettings(data.settings);
        setSavedMessage('✓ Settings synced with desktop app');
        setTimeout(() => setSavedMessage(null), 3000);
      }
    } catch (err) {
      console.error('Failed to sync settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleFpsChange = (fps: number) => {
    saveSettings({ ...settings, recording_fps: fps });
  };

  const handleGameBarToggle = () => {
    saveSettings({
      ...settings,
      include_gamebar_in_recording: !settings.include_gamebar_in_recording,
    });
  };

  return (
    <div className="max-w-3xl flex flex-col gap-8">
      <div>
        <p className="text-white/30 text-[11px] tracking-[0.2em] uppercase mb-2">Desktop & Cloud Sync</p>
        <h1 className="text-[28px] md:text-[34px] font-light tracking-[-0.02em] text-white">
          Capture & Recording Settings
        </h1>
        <p className="text-white/50 text-[14px] leading-relaxed mt-2">
          Configure video recording framerates, video format, and GameBar capture behavior.
          Settings automatically synchronize with your desktop GameBar overlay in real time.
        </p>
      </div>

      {savedMessage && (
        <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-[12px] text-emerald-400 animate-fade-in">
          <CheckCircle2 size={16} className="shrink-0" />
          <span>{savedMessage}</span>
        </div>
      )}

      {/* FPS FORMAT CARD */}
      <section className="border border-white/10 rounded-2xl p-6 md:p-8 flex flex-col gap-6 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#70e1ff]/10 border border-[#70e1ff]/20 flex items-center justify-center text-[#70e1ff]">
            <Film size={20} />
          </div>
          <div>
            <h2 className="text-[17px] font-medium text-white">Recording Framerate (FPS)</h2>
            <p className="text-white/40 text-[12px]">Choose your target framerate for video recordings</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {FPS_OPTIONS.map((opt) => {
            const isSelected = settings.recording_fps === opt.value;
            return (
              <button
                key={opt.value}
                onClick={() => handleFpsChange(opt.value)}
                disabled={loading || saving}
                className={`p-4 rounded-xl text-left border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#70e1ff]/15 border-[#70e1ff] text-white shadow-lg shadow-[#70e1ff]/10'
                    : 'bg-white/5 border-white/10 hover:border-white/20 text-white/70'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[15px] font-bold">{opt.label}</span>
                  {isSelected && <span className="w-2 h-2 rounded-full bg-[#70e1ff]" />}
                </div>
                <p className="text-[11px] text-white/50 leading-relaxed">{opt.desc}</p>
              </button>
            );
          })}
        </div>
      </section>

      {/* GAMEBAR CAPTURE VISIBILITY CARD */}
      <section className="border border-white/10 rounded-2xl p-6 md:p-8 flex flex-col gap-6 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
            <Monitor size={20} />
          </div>
          <div>
            <h2 className="text-[17px] font-medium text-white">GameBar Recording Visibility</h2>
            <p className="text-white/40 text-[12px]">Show or hide the GameBar overlay inside recorded video clips</p>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/10">
          <div className="flex flex-col gap-1 pr-4">
            <span className="text-[14px] font-medium text-white">
              Include GameBar overlay in recording
            </span>
            <span className="text-[12px] text-white/40 leading-relaxed">
              When active, the HUD is visible in recordings. You can press <strong>Ctrl+Shift+X</strong> at any time to hide the GameBar from your screen and remove it from the recording.
            </span>
          </div>

          <button
            onClick={handleGameBarToggle}
            disabled={loading || saving}
            className={`w-12 h-7 rounded-full transition-colors relative cursor-pointer shrink-0 ${
              settings.include_gamebar_in_recording ? 'bg-[#70e1ff]' : 'bg-white/20'
            }`}
          >
            <span
              className={`absolute top-1 w-5 h-5 rounded-full bg-black transition-transform ${
                settings.include_gamebar_in_recording ? 'left-6' : 'left-1'
              }`}
            />
          </button>
        </div>

        <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-[#70e1ff]/10 border border-[#70e1ff]/20 text-[12px] text-[#70e1ff]/90">
          <Info size={16} className="shrink-0 mt-0.5" />
          <span>
            <strong>Pro Tip:</strong> With this setting enabled, whenever you press <code>Ctrl+Shift+X</code> in-game, the GameBar minimizes and naturally disappears from the video recording!
          </span>
        </div>
      </section>

      {/* VIDEO CONTAINER FORMAT CARD */}
      <section className="border border-white/10 rounded-2xl p-6 md:p-8 flex flex-col gap-6 bg-white/[0.02]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Sliders size={20} />
          </div>
          <div>
            <h2 className="text-[17px] font-medium text-white">Encoding & Sync Status</h2>
            <p className="text-white/40 text-[12px]">Container format and desktop synchronization</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[13px]">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1">
            <span className="text-[11px] text-white/40 uppercase tracking-wider">Video Container</span>
            <span className="text-white font-medium">MP4 (H.264 / mp4v)</span>
          </div>

          <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex flex-col gap-1">
            <span className="text-[11px] text-white/40 uppercase tracking-wider">Cloud Sync Status</span>
            <span className="text-emerald-400 font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Connected to Desktop Client
            </span>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={() => saveSettings(settings)}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#70e1ff] text-[#0d1117] font-bold text-[13px] hover:bg-[#38bdf8] transition-colors cursor-pointer"
          >
            <RefreshCw size={14} className={saving ? 'animate-spin' : ''} />
            <span>{saving ? 'Syncing…' : 'Sync with Desktop'}</span>
          </button>
        </div>
      </section>
    </div>
  );
};

export default Settings;
