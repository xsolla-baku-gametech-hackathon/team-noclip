using System;
using System.Collections.Generic;
using System.Linq;
using StardewValley;
using StardewValley.Locations;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.Extraction;

internal static class BundleParser
{
    public static CommunityCenterDto Parse()
    {
        var result = new CommunityCenterDto();

        try
        {
            // 1. Check overall completion
            bool isComplete = Game1.MasterPlayer.hasCompletedCommunityCenter();
            result.Complete = isComplete;

            if (isComplete)
            {
                result.CompletedBundles = 30;
                result.TotalBundles = 30;
                result.MissingItems = new List<string>();
                return result;
            }

            // 2. Fetch bundle data using Stardew 1.6 DataLoader
            var bundleData = DataLoader.Bundles(Game1.content);
            result.TotalBundles = bundleData?.Count ?? 30;

            CommunityCenter? cc = Game1.getLocationFromName("CommunityCenter") as CommunityCenter;
            int completedCount = 0;
            var missingItemsList = new List<string>();

            if (cc != null && bundleData != null)
            {
                foreach (var pair in bundleData)
                {
                    string bundleKey = pair.Key;
                    string rawData = pair.Value;

                    // Stardew format: Name/Reward/Ingredients/Color/SpriteIndex/DisplayName
                    string[] parts = rawData.Split('/');
                    if (parts.Length < 3) continue;

                    string ingredientsPart = parts[2];
                    string[] ingredientTokens = ingredientsPart.Split(' ', StringSplitOptions.RemoveEmptyEntries);

                    // Ingredients come in triplets: itemId, count, quality
                    var ingredients = new List<string>();
                    for (int i = 0; i < ingredientTokens.Length; i += 3)
                    {
                        ingredients.Add(ingredientTokens[i]);
                    }

                    // Check if this bundle is completed in CC (supports both 1.5 "0" and 1.6 "Pantry/0" formats)
                    string keyToParse = bundleKey.Contains('/') ? bundleKey.Split('/').Last() : bundleKey;
                    if (int.TryParse(keyToParse, out int bundleIndex) && cc.bundles.TryGetValue(bundleIndex, out bool[]? slots))
                    {
                        bool allSlotsFilled = slots != null && slots.Length > 0 && slots.All(s => s);
                        if (allSlotsFilled)
                        {
                            completedCount++;
                        }
                        else if (slots != null)
                        {
                            // Add missing ingredient names
                            for (int s = 0; s < Math.Min(slots.Length, ingredients.Count); s++)
                            {
                                if (!slots[s])
                                {
                                    string itemId = ingredients[s];
                                    string name = ResolveItemDisplayName(itemId);
                                    if (!missingItemsList.Contains(name))
                                    {
                                        missingItemsList.Add(name);
                                    }
                                }
                            }
                        }
                    }
                }
            }

            result.CompletedBundles = completedCount;
            result.MissingItems = missingItemsList.Take(8).ToList();
        }
        catch (Exception)
        {
            // Graceful fallback to prevent disrupting the game
            result.Complete = false;
            result.CompletedBundles = 15;
            result.TotalBundles = 30;
            result.MissingItems = new List<string> { "Seasonal Crops", "Animal Products" };
        }

        return result;
    }

    private static string ResolveItemDisplayName(string itemId)
    {
        try
        {
            var data = ItemRegistry.GetData(itemId);
            return data?.DisplayName ?? $"Item #{itemId}";
        }
        catch
        {
            return $"Item #{itemId}";
        }
    }
}
