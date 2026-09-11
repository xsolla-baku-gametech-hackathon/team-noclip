// Vercel Serverless Function & Dev API: Settings Endpoint
// Provides bidirectional settings synchronization for video recording FPS,
// video container format, and GameBar capture visibility between desktop and web.

let inMemorySettings = {
  recording_fps: 30,
  video_format: 'mp4',
  include_gamebar_in_recording: true,
  resolution: 'native',
  updated_at: new Date().toISOString()
};

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }

  if (req.method === 'GET') {
    res.status(200).json({
      success: true,
      settings: inMemorySettings
    });
    return;
  }

  if (req.method === 'POST') {
    const body = req.body || {};
    const newSettings = body.settings || body;

    if (typeof newSettings === 'object' && newSettings !== null) {
      if ('recording_fps' in newSettings) {
        const fps = parseInt(newSettings.recording_fps, 10);
        if (!isNaN(fps)) {
          inMemorySettings.recording_fps = Math.max(10, Math.min(120, fps));
        }
      }
      if ('video_format' in newSettings) {
        inMemorySettings.video_format = String(newSettings.video_format).toLowerCase();
      }
      if ('include_gamebar_in_recording' in newSettings) {
        inMemorySettings.include_gamebar_in_recording = Boolean(newSettings.include_gamebar_in_recording);
      }
      if ('resolution' in newSettings) {
        inMemorySettings.resolution = String(newSettings.resolution);
      }
      inMemorySettings.updated_at = new Date().toISOString();
    }

    res.status(200).json({
      success: true,
      settings: inMemorySettings
    });
    return;
  }

  res.status(405).json({ error: 'Method not allowed' });
}
