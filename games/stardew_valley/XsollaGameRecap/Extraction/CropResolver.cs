using Microsoft.Xna.Framework;
using StardewValley;
using StardewValley.TerrainFeatures;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.Extraction;

internal static class CropResolver
{
    public static CropDto? Resolve(HoeDirt dirt, Vector2 position)
    {
        if (dirt.crop == null)
            return null;

        Crop crop = dirt.crop;
        string rawId = crop.indexOfHarvest.Value;

        // Resolve display name using Stardew 1.6 ItemRegistry
        string displayName;
        try
        {
            var itemData = ItemRegistry.GetData(rawId);
            displayName = itemData?.DisplayName ?? $"Crop #{rawId}";
        }
        catch
        {
            displayName = $"Crop #{rawId}";
        }

        // Determine growth and watering state
        string state;
        int phaseCount = crop.phaseDays != null ? crop.phaseDays.Count : 5;
        if (crop.dead.Value)
        {
            state = "dead";
        }
        else if ((phaseCount > 0 && crop.currentPhase.Value >= phaseCount - 1) || 
                (crop.fullyGrown.Value && crop.dayOfCurrentPhase.Value <= 0))
        {
            state = "ready";
        }
        else if (!dirt.isWatered())
        {
            state = "needs_water";
        }
        else
        {
            state = "growing";
        }

        return new CropDto
        {
            CropName = displayName,
            State = state,
            X = (int)position.X,
            Y = (int)position.Y
        };
    }
}
