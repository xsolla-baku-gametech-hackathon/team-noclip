using StardewModdingAPI;
using StardewModdingAPI.Utilities;

namespace XsollaGameRecap;

internal sealed class ModConfig
{
    public KeybindList OpenRecapKey { get; set; } = KeybindList.Parse("F8");
    public string ApiUrl { get; set; } = "http://127.0.0.1:8000/api/recap";
    public int HttpTimeoutSeconds { get; set; } = 10;
    public bool EnableLogging { get; set; } = true;
}
