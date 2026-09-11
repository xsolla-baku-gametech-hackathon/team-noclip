# How to Contribute — Team Noclip

Welcome to the Team Noclip repository.

## 🚨 CRITICAL RULE: MAIN BRANCH ONLY

**ALL development must occur directly on the `main` branch.**
- **Do NOT create or switch to other branches** (e.g. `dev`, feature branches, bugfix branches).
- **Do NOT open PRs across branches** — commit and push directly to `origin/main`.
- This applies to all human contributors and all AI assistants / pair programmers.

## Workflow

1. **Pull before starting:** Always run `git pull origin main` to ensure your local copy is up to date.
2. **Commit directly to `main`:** Make concise, meaningful commits directly on `main`.
3. **Verify tests:** Run unit/integration tests before pushing.
4. **Push to `main`:** Push your work directly to `origin/main`.

## Repository Structure

- `website/`: SynapseX & Xsolla Web portal, Google OAuth authentication, serverless recap API.
- `software/`: Xsolla Game Recap desktop application, GameBar HUD overlay, local detector, and standalone `XsollaGameRecap.exe`.
- `games/`: Hooked game integrations and mod hooks.

Let's build something awesome!
