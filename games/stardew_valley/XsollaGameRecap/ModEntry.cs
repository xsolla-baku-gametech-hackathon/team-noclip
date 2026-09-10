using System;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;
using XsollaGameRecap.Extraction;
using XsollaGameRecap.Models;
using XsollaGameRecap.Services;
using XsollaGameRecap.UI;

namespace XsollaGameRecap;

internal sealed class ModEntry : Mod
{
    private ModConfig config = null!;
    private GameStateExtractor extractor = null!;
    private RecapApiClient apiClient = null!;
    private bool requestInProgress;

    // Thread-safe dispatch fields marshalled into UpdateTicked
    private RecapResponseDto? pendingResponse;
    private string? pendingError;

    public override void Entry(IModHelper helper)
    {
        config = helper.ReadConfig<ModConfig>();
        extractor = new GameStateExtractor();
        apiClient = new RecapApiClient(config.ApiUrl, config.HttpTimeoutSeconds);

        // Register SMAPI Events
        helper.Events.Input.ButtonsChanged += OnButtonsChanged;
        helper.Events.Input.ButtonPressed += OnButtonPressed;
        helper.Events.GameLoop.UpdateTicked += OnUpdateTicked;
        helper.Events.GameLoop.SaveLoaded += OnSaveLoaded;
        helper.Events.Display.MenuChanged += OnMenuChanged;
        helper.Events.Display.RenderedActiveMenu += OnRenderedActiveMenu;

        // Register Console Commands for testing and quick access
        helper.ConsoleCommands.Add(
            "recap",
            "Opens the Xsolla Game Recap modal immediately.\n\nUsage: recap",
            (cmd, args) => OpenRecap()
        );

        helper.ConsoleCommands.Add(
            "recap_status",
            "Checks connection status to the Xsolla recap backend.\n\nUsage: recap_status",
            OnRecapStatusCommand
        );

        helper.ConsoleCommands.Add(
            "recap_reload",
            "Reloads mod configuration from config.json live without restarting the game.\n\nUsage: recap_reload",
            (cmd, args) =>
            {
                config = helper.ReadConfig<ModConfig>();
                apiClient = new RecapApiClient(config.ApiUrl, config.HttpTimeoutSeconds);
                Monitor.Log($"[Xsolla Game Recap] Config reloaded live! Keybind: {config.OpenRecapKey}, Backend: {config.ApiUrl}", LogLevel.Info);
            }
        );

        Monitor.Log($"Xsolla Game Recap initialized. Press {config.OpenRecapKey} in-game to view your recap.", LogLevel.Info);
    }

    private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        // Check backend connectivity in the background when player loads their save
        Task.Run(async () =>
        {
            bool isOnline = await apiClient.CheckHealthAsync();
            if (isOnline)
            {
                Monitor.Log($"[Xsolla Game Recap] Backend verified online at {config.ApiUrl}. Ready for instant recap!", LogLevel.Info);
            }
            else
            {
                Monitor.Log($"[Xsolla Game Recap] Note: Backend offline at {config.ApiUrl}. Mod will use bulletproof local fallback.", LogLevel.Warn);
            }
        });
    }

    private void OnButtonsChanged(object? sender, ButtonsChangedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (config.OpenRecapKey.JustPressed())
        {
            if (Game1.activeClickableMenu is RecapModalMenu)
            {
                CloseRecap();
            }
            else
            {
                OpenRecap();
            }
        }
    }

    private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (e.Button == SButton.MouseLeft && Game1.activeClickableMenu is GameMenu menu)
        {
            Rectangle tabBounds = GetXsollaTabBounds(menu);
            if (tabBounds.Contains(Game1.getMouseX(), Game1.getMouseY()))
            {
                Helper.Input.Suppress(e.Button);
                Game1.playSound("crystal");
                OpenRecap();
            }
        }
    }

    private void OnRenderedActiveMenu(object? sender, RenderedActiveMenuEventArgs e)
    {
        if (Game1.activeClickableMenu is not GameMenu menu)
            return;

        Rectangle tabBounds = GetXsollaTabBounds(menu);
        bool isHover = tabBounds.Contains(Game1.getMouseX(), Game1.getMouseY());

        // Background card
        Color bgColor = isHover ? new Color(185, 35, 45, 250) : new Color(35, 25, 30, 240);
        e.SpriteBatch.Draw(Game1.staminaRect, tabBounds, bgColor);

        // Border
        Color borderColor = isHover ? Color.Gold : new Color(255, 75, 75);
        int borderThickness = isHover ? 3 : 2;
        DrawBorder(e.SpriteBatch, tabBounds, borderThickness, borderColor);

        // Text
        string text = "XSOLLA RECAP";
        Vector2 textSize = Game1.smallFont.MeasureString(text);
        Vector2 textPos = new Vector2(
            tabBounds.X + (tabBounds.Width - textSize.X) / 2,
            tabBounds.Y + (tabBounds.Height - textSize.Y) / 2
        );

        // Shadow & text
        e.SpriteBatch.DrawString(Game1.smallFont, text, textPos + new Vector2(1, 1), Color.Black * 0.7f);
        e.SpriteBatch.DrawString(Game1.smallFont, text, textPos, isHover ? Color.White : Color.Wheat);

        // Hover tooltip
        if (isHover)
        {
            IClickableMenu.drawHoverText(
                e.SpriteBatch,
                "Xsolla Game Recap (F8)\nContext & Critical Priorities",
                Game1.smallFont
            );
        }
    }

    private Rectangle GetXsollaTabBounds(GameMenu menu)
    {
        int w = 175;
        int h = 48;
        int y = menu.yPositionOnScreen - 52;
        int x = menu.xPositionOnScreen + menu.width - w - 16;
        if (menu.tabs != null && menu.tabs.Count > 0)
        {
            var lastTab = menu.tabs[menu.tabs.Count - 1];
            y = lastTab.bounds.Y + 6;
            if (lastTab.bounds.Right + 14 + w <= menu.xPositionOnScreen + menu.width)
            {
                x = lastTab.bounds.Right + 14;
            }
        }
        return new Rectangle(x, y, w, h);
    }

    private static void DrawBorder(SpriteBatch b, Rectangle rect, int thickness, Color color)
    {
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        b.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }

    private void OnMenuChanged(object? sender, MenuChangedEventArgs e)
    {
        // Handled dynamically via RenderedActiveMenu
    }

    private void OnRecapStatusCommand(string command, string[] args)
    {
        Monitor.Log("Checking Xsolla Recap backend status...", LogLevel.Info);
        Task.Run(async () =>
        {
            bool isOnline = await apiClient.CheckHealthAsync();
            if (isOnline)
            {
                Monitor.Log($"SUCCESS: Backend at {config.ApiUrl} is ONLINE.", LogLevel.Info);
            }
            else
            {
                Monitor.Log($"WARNING: Backend at {config.ApiUrl} is UNREACHABLE. Local fallback active.", LogLevel.Warn);
            }
        });
    }

    private void OpenRecap()
    {
        if (requestInProgress)
            return;

        if (Game1.activeClickableMenu != null && Game1.activeClickableMenu is not GameMenu)
            return;

        if (!Context.IsWorldReady)
        {
            Monitor.Log("Cannot open recap: No game world is currently loaded.", LogLevel.Warn);
            return;
        }

        requestInProgress = true;
        pendingResponse = null;
        pendingError = null;

        // Open modal in loading state immediately for instant feedback
        RecapModalMenu menu = new RecapModalMenu(CloseRecap);
        Game1.activeClickableMenu = menu;

        // 1. Extract game state safely on the game thread
        GameStateDto state;
        try
        {
            state = extractor.Extract();
        }
        catch (Exception ex)
        {
            Monitor.Log($"Failed to extract live game state: {ex}", LogLevel.Error);
            menu.SetError("Failed to extract game state from world.");
            requestInProgress = false;
            return;
        }

        // 2. Asynchronously request recap from backend (with local failover)
        Task.Run(async () =>
        {
            try
            {
                RecapResponseDto response = await apiClient.GenerateRecapAsync(state);
                pendingResponse = response;
            }
            catch (Exception ex)
            {
                Monitor.Log($"Error during recap generation: {ex}", LogLevel.Error);
                pendingError = "Unable to process recap.";
            }
            finally
            {
                requestInProgress = false;
            }
        });
    }

    private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (Game1.activeClickableMenu is not RecapModalMenu menu)
            return;

        if (pendingResponse != null)
        {
            RecapResponseDto resp = pendingResponse;
            pendingResponse = null;
            menu.SetResponse(resp);
        }

        if (pendingError != null)
        {
            string err = pendingError;
            pendingError = null;
            menu.SetError(err);
        }
    }

    private void CloseRecap()
    {
        if (Game1.activeClickableMenu is RecapModalMenu)
        {
            Game1.activeClickableMenu = null;
        }
    }
}
