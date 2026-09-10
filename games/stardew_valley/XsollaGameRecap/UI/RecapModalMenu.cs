using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.UI;

internal sealed class RecapModalMenu : IClickableMenu
{
    private readonly Action closeAction;
    private RecapResponseDto? response;
    private string? error;
    private bool loading = true;

    private Rectangle panelBounds;
    private Rectangle resumeButtonBounds;
    private Rectangle card1Bounds;
    private Rectangle card2Bounds;
    private Rectangle card3Bounds;

    private int hoveredCard = -1;
    private bool isResumeHovered = false;

    public RecapModalMenu(Action closeAction)
        : base(0, 0, Game1.viewport.Width, Game1.viewport.Height, true)
    {
        this.closeAction = closeAction;
        CalculateLayout();

        // Audio cue on menu open
        Game1.playSound("crystal");
    }

    private void CalculateLayout()
    {
        // Fit comfortably on 1280x720, 1920x1080 and other standard resolutions
        int panelWidth = Math.Min(1180, Game1.viewport.Width - 60);
        int panelHeight = Math.Min(660, Game1.viewport.Height - 40);

        int panelX = (Game1.viewport.Width - panelWidth) / 2;
        int panelY = (Game1.viewport.Height - panelHeight) / 2;
        panelBounds = new Rectangle(panelX, panelY, panelWidth, panelHeight);

        // Synchronize IClickableMenu dimensions and initialize the native close button
        this.xPositionOnScreen = panelBounds.X;
        this.yPositionOnScreen = panelBounds.Y;
        this.width = panelBounds.Width;
        this.height = panelBounds.Height;
        this.initializeUpperRightCloseButton();

        // 3 Cards Layout - 440px height so text never spills out
        int paddingX = 24;
        int cardSpacing = 16;
        int availableWidth = panelWidth - (paddingX * 2) - (cardSpacing * 2);
        int cardWidth = availableWidth / 3;
        int cardY = panelBounds.Y + 98;
        int cardHeight = 440;

        card1Bounds = new Rectangle(panelBounds.X + paddingX, cardY, cardWidth, cardHeight);
        card2Bounds = new Rectangle(panelBounds.X + paddingX + cardWidth + cardSpacing, cardY, cardWidth, cardHeight);
        card3Bounds = new Rectangle(panelBounds.X + paddingX + (cardWidth + cardSpacing) * 2, cardY, cardWidth, cardHeight);

        // Resume button placed neatly below the cards with dedicated vertical space
        int btnWidth = 260;
        int btnHeight = 46;
        int btnY = cardY + cardHeight + 14;
        resumeButtonBounds = new Rectangle(
            panelBounds.X + (panelBounds.Width - btnWidth) / 2,
            btnY,
            btnWidth,
            btnHeight
        );
    }

    public void SetResponse(RecapResponseDto result)
    {
        this.response = result;
        this.loading = false;
        Game1.playSound("reward");
    }

    public void SetError(string message)
    {
        this.error = message;
        this.loading = false;
        Game1.playSound("cancel");
    }

    public override void performHoverAction(int x, int y)
    {
        base.performHoverAction(x, y);

        this.upperRightCloseButton?.tryHover(x, y);
        isResumeHovered = resumeButtonBounds.Contains(x, y);

        if (card1Bounds.Contains(x, y))
            hoveredCard = 1;
        else if (card2Bounds.Contains(x, y))
            hoveredCard = 2;
        else if (card3Bounds.Contains(x, y))
            hoveredCard = 3;
        else
            hoveredCard = -1;
    }

    public override void receiveLeftClick(int x, int y, bool playSound = true)
    {
        if (this.upperRightCloseButton != null && this.upperRightCloseButton.containsPoint(x, y))
        {
            if (playSound)
                Game1.playSound("bigDeSelect");
            closeAction();
            return;
        }

        if (resumeButtonBounds.Contains(x, y))
        {
            if (playSound)
                Game1.playSound("coin");
            closeAction();
            return;
        }

        base.receiveLeftClick(x, y, playSound);
    }

    public override void receiveKeyPress(Keys key)
    {
        if (key == Keys.Escape || key == Keys.F8)
        {
            Game1.playSound("bigDeSelect");
            closeAction();
            return;
        }

        base.receiveKeyPress(key);
    }

    public override void draw(SpriteBatch b)
    {
        CalculateLayout();

        // 1. Cinematic Dim Backdrop
        b.Draw(
            Game1.fadeToBlackRect,
            Game1.graphics.GraphicsDevice.Viewport.Bounds,
            Color.Black * 0.65f
        );

        // 2. Main Stardew Dialog Frame
        IClickableMenu.drawTextureBox(
            b,
            Game1.menuTexture,
            new Rectangle(0, 256, 60, 60),
            panelBounds.X,
            panelBounds.Y,
            panelBounds.Width,
            panelBounds.Height,
            Color.White
        );

        // 3. Header Banner
        Utility.drawTextWithShadow(
            b,
            "XSOLLA GAME RECAP",
            Game1.dialogueFont,
            new Vector2(panelBounds.X + 34, panelBounds.Y + 20),
            new Color(205, 45, 35) // Rich branded red
        );

        string farmerName = Game1.player?.Name ?? "Farmer";
        Utility.drawTextWithShadow(
            b,
            $"Contextual Memory Bridge for {farmerName} | Instant Resumption Assistant",
            Game1.smallFont,
            new Vector2(panelBounds.X + 36, panelBounds.Y + 62),
            new Color(95, 75, 60) // Clean warm brown
        );

        // 4. Content Area: The 3 Cards
        if (loading)
        {
            DrawLoading(b, panelBounds);
        }
        else if (error != null)
        {
            DrawError(b, panelBounds);
        }
        else if (response != null)
        {
            DrawCard1(b, card1Bounds, hoveredCard == 1);
            DrawCard2(b, card2Bounds, hoveredCard == 2);
            DrawCard3(b, card3Bounds, hoveredCard == 3);
        }

        // 5. Close Button (Native Stardew upper right red X button with hover animation)
        this.upperRightCloseButton?.draw(b);

        // 6. Resume Playing Button (Native Texture Box, centered, zero overlap)
        Color resumeBoxTint = isResumeHovered ? Color.Wheat : Color.White;
        IClickableMenu.drawTextureBox(
            b,
            Game1.menuTexture,
            new Rectangle(0, 256, 60, 60),
            resumeButtonBounds.X,
            resumeButtonBounds.Y,
            resumeButtonBounds.Width,
            resumeButtonBounds.Height,
            resumeBoxTint
        );

        string resumeText = "> Resume Playing <";
        Vector2 resumeTextSize = Game1.smallFont.MeasureString(resumeText);
        Vector2 resumeTextPos = new Vector2(
            resumeButtonBounds.X + (resumeButtonBounds.Width - resumeTextSize.X) / 2,
            resumeButtonBounds.Y + (resumeButtonBounds.Height - resumeTextSize.Y) / 2
        );
        Color resumeTextColor = isResumeHovered ? new Color(0, 110, 20) : new Color(55, 38, 25);
        Utility.drawTextWithShadow(b, resumeText, Game1.smallFont, resumeTextPos, resumeTextColor);

        // 7. Footer Attribution (Placed neatly below button with clear separation)
        string footer = "Xsolla Game Recap System • We don't make players remember their game. We make the game remember the player.";
        Vector2 footerSize = Game1.tinyFont.MeasureString(footer);
        Vector2 footerPos = new Vector2(
            panelBounds.X + (panelBounds.Width - footerSize.X) / 2,
            panelBounds.Bottom - 24
        );
        Utility.drawTextWithShadow(b, footer, Game1.tinyFont, footerPos, new Color(130, 105, 80) * 0.85f);

        drawMouse(b);
    }

    private void DrawCard1(SpriteBatch b, Rectangle card, bool isHovered)
    {
        // Native card box
        Color boxTint = isHovered ? Color.Wheat : Color.White;
        IClickableMenu.drawTextureBox(
            b,
            Game1.menuTexture,
            new Rectangle(0, 256, 60, 60),
            card.X,
            card.Y,
            card.Width,
            card.Height,
            boxTint
        );

        // Card Title (Clean, bold, fits perfectly without crossing border)
        Utility.drawTextWithShadow(
            b,
            "1. PREVIOUSLY ON...",
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 18),
            new Color(35, 85, 160) // Deep clear blue
        );

        // Subtitle badge (Placed 24px below title with ZERO overlap)
        Utility.drawTextWithShadow(
            b,
            "NARRATIVE SUMMARY",
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 44),
            new Color(115, 90, 70)
        );

        // Subtle divider
        b.Draw(
            Game1.staminaRect,
            new Rectangle(card.X + 20, card.Y + 70, card.Width - 40, 1),
            new Color(185, 155, 120) * 0.6f
        );

        // Narrative Body Text (cleanly wrapped with generous padding)
        int textWidth = card.Width - 44;
        string narrative = response?.PreviouslyOn ?? "Welcome back to your farm! Review your daily status to plan your chores.";
        string wrapped = Game1.parseText(narrative, Game1.smallFont, textWidth);
        Utility.drawTextWithShadow(
            b,
            wrapped,
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 84),
            new Color(45, 30, 18) // Classic Stardew dark walnut
        );
    }

    private void DrawCard2(SpriteBatch b, Rectangle card, bool isHovered)
    {
        // Native card box
        Color boxTint = isHovered ? Color.Wheat : Color.White;
        IClickableMenu.drawTextureBox(
            b,
            Game1.menuTexture,
            new Rectangle(0, 256, 60, 60),
            card.X,
            card.Y,
            card.Width,
            card.Height,
            boxTint
        );

        // Card Title
        Utility.drawTextWithShadow(
            b,
            "2. CRITICAL TODAY",
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 18),
            new Color(185, 50, 38) // Deep clear red
        );

        // Subtitle badge (Zero overlap)
        Utility.drawTextWithShadow(
            b,
            "TOP PRIORITIES",
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 44),
            new Color(115, 90, 70)
        );

        // Subtle divider
        b.Draw(
            Game1.staminaRect,
            new Rectangle(card.X + 20, card.Y + 70, card.Width - 40, 1),
            new Color(185, 155, 120) * 0.6f
        );

        int curY = card.Y + 84;
        int textWidth = card.Width - 44;
        int maxCardY = card.Bottom - 24;

        if (response?.CriticalPriorities == null || response.CriticalPriorities.Count == 0)
        {
            Utility.drawTextWithShadow(
                b,
                "No critical alerts for today.\nTake a relaxing stroll through Pelican Town!",
                Game1.smallFont,
                new Vector2(card.X + 22, curY),
                new Color(90, 70, 55)
            );
            return;
        }

        // Display priorities neatly without EVER spilling out
        var priorities = response.CriticalPriorities.Take(3).ToList();
        for (int i = 0; i < priorities.Count; i++)
        {
            var p = priorities[i];
            string tag = p.Importance.ToUpperInvariant();

            Color tagColor = p.Importance.ToLowerInvariant() switch
            {
                "high" => new Color(185, 45, 35),
                "medium" => new Color(175, 100, 20),
                _ => new Color(45, 90, 155)
            };

            string titleLine = $"[{tag}] {p.Title.ToUpperInvariant()}";
            string descWrapped = Game1.parseText(p.Description, Game1.smallFont, textWidth);
            int itemHeight = 22 + (int)Game1.smallFont.MeasureString(descWrapped).Y + 10;

            // Safe boundary check: do not draw if it would cross outside card bottom
            if (curY + itemHeight > maxCardY)
                break;

            // Header line: e.g. [HIGH] WATER DRY CROPS
            Utility.drawTextWithShadow(b, titleLine, Game1.smallFont, new Vector2(card.X + 22, curY), tagColor);
            curY += 22;

            // Description line wrapped
            Utility.drawTextWithShadow(b, descWrapped, Game1.smallFont, new Vector2(card.X + 22, curY), new Color(45, 30, 18));
            curY += (int)Game1.smallFont.MeasureString(descWrapped).Y + 10;

            // Separator between priorities
            if (i < priorities.Count - 1 && curY + 20 < maxCardY)
            {
                b.Draw(
                    Game1.staminaRect,
                    new Rectangle(card.X + 22, curY - 4, card.Width - 44, 1),
                    new Color(185, 155, 120) * 0.35f
                );
                curY += 6;
            }
        }
    }

    private void DrawCard3(SpriteBatch b, Rectangle card, bool isHovered)
    {
        // Native card box
        Color boxTint = isHovered ? Color.Wheat : Color.White;
        IClickableMenu.drawTextureBox(
            b,
            Game1.menuTexture,
            new Rectangle(0, 256, 60, 60),
            card.X,
            card.Y,
            card.Width,
            card.Height,
            boxTint
        );

        // Card Title
        Utility.drawTextWithShadow(
            b,
            "3. GOALS TRACKER",
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 18),
            new Color(35, 125, 60) // Deep clear forest green
        );

        // Subtitle badge (Zero overlap)
        Utility.drawTextWithShadow(
            b,
            "ONGOING OBJECTIVES",
            Game1.smallFont,
            new Vector2(card.X + 22, card.Y + 44),
            new Color(115, 90, 70)
        );

        // Subtle divider
        b.Draw(
            Game1.staminaRect,
            new Rectangle(card.X + 20, card.Y + 70, card.Width - 40, 1),
            new Color(185, 155, 120) * 0.6f
        );

        int curY = card.Y + 84;
        int textWidth = card.Width - 44;
        int maxCardY = card.Bottom - 24;

        // Section: QUESTS
        Utility.drawTextWithShadow(
            b,
            "QUESTS:",
            Game1.smallFont,
            new Vector2(card.X + 22, curY),
            new Color(135, 80, 25)
        );
        curY += 22;

        if (response?.GoalTracker.ActiveQuests != null && response.GoalTracker.ActiveQuests.Count > 0)
        {
            foreach (var q in response.GoalTracker.ActiveQuests.Take(3))
            {
                if (curY + 22 > maxCardY) break;
                string wrappedQ = Game1.parseText($"* {q}", Game1.smallFont, textWidth);
                Utility.drawTextWithShadow(b, wrappedQ, Game1.smallFont, new Vector2(card.X + 22, curY), new Color(45, 30, 18));
                curY += (int)Game1.smallFont.MeasureString(wrappedQ).Y + 4;
            }
        }
        else
        {
            Utility.drawTextWithShadow(b, "* No active quests", Game1.smallFont, new Vector2(card.X + 22, curY), new Color(110, 90, 75));
            curY += 22;
        }

        if (curY + 30 < maxCardY)
        {
            curY += 6;
            b.Draw(
                Game1.staminaRect,
                new Rectangle(card.X + 22, curY, card.Width - 44, 1),
                new Color(185, 155, 120) * 0.35f
            );
            curY += 10;

            // Section: MILESTONES & CC BUNDLES
            Utility.drawTextWithShadow(
                b,
                "MILESTONES:",
                Game1.smallFont,
                new Vector2(card.X + 22, curY),
                new Color(135, 80, 25)
            );
            curY += 22;

            if (response?.GoalTracker.Milestones != null && response.GoalTracker.Milestones.Count > 0)
            {
                foreach (var m in response.GoalTracker.Milestones.Take(2))
                {
                    if (curY + 22 > maxCardY) break;
                    string wrappedM = Game1.parseText($"* {m}", Game1.smallFont, textWidth);
                    Utility.drawTextWithShadow(b, wrappedM, Game1.smallFont, new Vector2(card.X + 22, curY), new Color(45, 30, 18));
                    curY += (int)Game1.smallFont.MeasureString(wrappedM).Y + 4;
                }
            }

            if (response?.GoalTracker.MissingBundleItems != null && response.GoalTracker.MissingBundleItems.Count > 0 && curY + 22 <= maxCardY)
            {
                string itemsStr = "* Missing CC: " + string.Join(", ", response.GoalTracker.MissingBundleItems.Take(3));
                string wrappedItems = Game1.parseText(itemsStr, Game1.smallFont, textWidth);
                Utility.drawTextWithShadow(b, wrappedItems, Game1.smallFont, new Vector2(card.X + 22, curY), new Color(75, 55, 40));
            }
        }
    }

    private void DrawLoading(SpriteBatch b, Rectangle panel)
    {
        int dotsCount = (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 300) % 4;
        string dots = new string('.', dotsCount);

        Utility.drawTextWithShadow(
            b,
            $"Remembering your farm and consulting AI memory bridge{dots}",
            Game1.smallFont,
            new Vector2(panel.X + 36, panel.Y + 140),
            new Color(60, 40, 25)
        );

        Utility.drawTextWithShadow(
            b,
            "Analyzing crop hydration, active quests, community center progress, and social connections...",
            Game1.smallFont,
            new Vector2(panel.X + 36, panel.Y + 175),
            new Color(110, 85, 70)
        );
    }

    private void DrawError(SpriteBatch b, Rectangle panel)
    {
        Utility.drawTextWithShadow(
            b,
            $"Recap Notice: {error ?? "Backend connection unavailable."}",
            Game1.smallFont,
            new Vector2(panel.X + 36, panel.Y + 140),
            new Color(185, 45, 35)
        );

        Utility.drawTextWithShadow(
            b,
            "Run 'run_backend.bat' to start the local FastAPI recap service at http://127.0.0.1:8000.",
            Game1.smallFont,
            new Vector2(panel.X + 36, panel.Y + 175),
            new Color(60, 40, 25)
        );
    }
}
