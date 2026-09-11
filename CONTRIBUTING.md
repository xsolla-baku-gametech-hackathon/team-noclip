# How to Contribute

Hey team! Welcome to the Team Noclip repo. 

To keep things running smoothly (and to make sure we rack up those teamwork points for the hackathon), let's stick to a few basic rules when adding code.

## The Basic Flow

1. **Find or open an issue:** Don't just start coding in the void. Make sure there's an issue for whatever you're working on—whether it's a new feature, a bug fix, or just some cleanup.
2. **Assign yourself:** Claim the issue so we don't accidentally step on each other's toes.
3. **Branch out:** Create a new branch for your work branching off from `dev`. Try to name it something like:
   - `feature/12-add-login`
   - `bugfix/15-fix-crash`
   - `chore/2-update-readme`
4. **Commit often:** Save your progress with small commits. It makes it way easier to figure out what broke if something goes wrong, and it shows we're actively collaborating.
5. **Open a PR to `dev`:** Once you're done (or if you just want some feedback early on), open a Pull Request to the `dev` branch. **Never merge your day-to-day work straight into `main`!**
   - Tag the issue in the description (like `Closes #12`).
6. **Get a review:** Tag someone else on the team to look over your code.
7. **Merge to `dev`:** After it's approved and looks good, hit merge and delete your branch.
8. **Releasing to `main`:** We only merge `dev` into `main` when `dev` is totally stable. If you are opening a PR to merge `dev` into `main`, you **must** assign our team leader (@Aliyyiakbar) to review and approve it.

## Commit Messages

Just keep them simple and tell us what you actually did.

**Good:**
> Add login button to the website header

**Bad:**
> fixed stuff

## What goes where?

- `website/`: Put all the website stuff here.
- `games/`: Drop the game projects in here.
- `software/`: General software, scripts, or apps like the Game Recap app go here.
- `.github/`: This just holds our templates for issues and PRs. Don't worry about it too much.

Let's build something awesome!
