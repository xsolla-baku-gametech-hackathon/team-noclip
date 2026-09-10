# ⚡ Xsolla Game Recap - In-Game Overlay & GameBar

Hey team! Here is our in-game software for the **Xsolla Baku GameTech Hackathon**.

It works just like **Nvidia GeForce Experience** or **Xbox Game Bar**, built specifically to hook into your games, capture epic moments, and generate Spotify Wrapped-style gaming recaps that sync straight with our SaaS website.

---

## 🚀 Key Features

1. **Automatic Game Watcher (Official + Cracked Games)**:
   - Silently monitors your active games in the background.
   - Works with official Steam/Epic releases **AND** cracked, standalone, or modded versions.
   - Detects games by process name (`stardew valley.exe`, `undertale.exe`, etc.) **and** window titles (so even if the cracked exe has a weird name like `Game.exe`, it still catches it!).
   - Easily add any custom game executable right from the in-game dashboard.

2. **"Xsolla Game Recap is Watching" Animated Toast**:
   - The moment a supported game boots up, a sleek cyberpunk notification smoothly slides in from the top of your screen:
     ```
     ⚡ Xsolla Game Recap is Watching...
     Hooked: Stardew Valley • Shortcut: [Ctrl + Shift + X]
     ```
   - Uses special Windows non-activating window flags (`WS_EX_NOACTIVATE`) so it **never steals focus or minimizes your game**!
   - Stays visible for 4 seconds with a subtle cybernetic audio cue, then smoothly glides back out.

3. **In-Game GameBar Dashboard (`Ctrl + Shift + X` or `Alt + X`)**:
   - Press **`Ctrl + Shift + X`** (or **`Alt + X`**) anytime during gameplay to pop up the GameBar directly over the game.
   - Press **`ESC`** or hit the shortcut again to return to your game.
   - **Live Event Timeline**: See your milestones as they happen.
   - **Manual Highlight Logger**: Type any memory or achievement (e.g., *"Beat Sans with 1 HP left!"*) and hit Log.
   - **Instant Screenshot Capture**: Grabs high-res snapshots and tags them to your recap.
   - **Xsolla Story Recap Generator**: Compiles session stats, play time, gamer persona, and XP points into a shareable recap card.
   - **SaaS Cloud Bridge**: 1-click button to push your recap session directly to our SaaS website!

---

## 🎮 Supported Out of the Box

- **Stardew Valley** (`Stardew Valley.exe`, `smapi.exe`)
- **Undertale** (`UNDERTALE.exe`, `DELTARUNE.exe`)
- **Hades / Hades II** (`Hades.exe`, `Hades2.exe`)
- **Hollow Knight** (`hollow_knight.exe`)
- **Minecraft** (`javaw.exe`, `Minecraft.exe`, TLauncher, CurseForge)
- **Cyberpunk 2077** (`Cyberpunk2077.exe`)
- **Grand Theft Auto V** (`GTA5.exe`)
- **Elden Ring** (`eldenring.exe`)
- *Plus any custom or cracked game you register with 1 click!*

---

## 🛠️ How to Run

### Option 1: Native C++ Launcher (`.exe`)
Just double-click **`xsolla_launcher.exe`**! 
It launches the app silently in the background with zero ugly terminal windows.

### Option 2: Standalone Bundled Executable (`.exe`)
Run **`dist/XsollaGameRecap.exe`** (everything bundled into a single file).

### Option 3: Double-Click Batch File
Double-click **`run_overlay.bat`**.

### Option 4: Python CLI
```bash
# Start background watcher
python main.py

# Launch directly into demo mode (simulates a game launch & shows the toast + GameBar)
python main.py --demo

# Open the GameBar dashboard immediately
python main.py --open-gamebar
```

---

## 🧪 Testing & Demos for Judges

Want to showcase the app without needing to install Stardew Valley right this second? We've got you covered:
1. Run `python main.py --demo` (or click *"Simulate Stardew Valley"* inside the GameBar).
2. Watch the animated **"Xsolla Game Recap is Watching"** toast slide down from the top!
3. Press **`Ctrl + Shift + X`** to toggle the GameBar.
4. Click *"⭐ Add Sample Event"* or *"📸 Instant Screenshot"* to see live timeline updates.
5. Click *"✨ Xsolla Story Recap"* -> *"☁️ Sync to SaaS Web App"*!

Let's win this hackathon! 🏆
