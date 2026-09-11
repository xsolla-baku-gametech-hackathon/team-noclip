# Repository Rules for AI Agents & Contributors

## Strict Git Branch Policy: MAIN ONLY
- **ALL changes MUST be committed and pushed directly to `main` (`origin/main`).**
- **NEVER create, checkout, or push to any other branch (including `dev`, feature branches, etc.).**
- All agents working on this codebase must strictly adhere to this rule.

## Tech Stack & Architecture
- **Desktop Application**: Python 3 / Tkinter / Win32 in `software/`.
  - Main launcher entrypoint: `software/main.py`
  - In-game GameBar HUD overlay: `software/gamebar.py`
  - Dedicated login window launcher: `software/login_window.py`
  - Recap Engine: `software/save_analyzer.py` & `software/ai_recap.py`
  - Packaging script: `software/build_exe.py` -> `software/XsollaGameRecap.exe` (must stay under 100MB).
- **Web Application**: Vite + React 19 + TypeScript + TailwindCSS in `website/`.
  - Deployed to: `https://team-noclip.vercel.app`
  - Serverless recap API: `website/api/recap.js`
  - Google Authentication: `website/src/auth/google.ts`
