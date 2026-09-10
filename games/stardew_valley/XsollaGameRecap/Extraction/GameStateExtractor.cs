using System;
using System.Collections.Generic;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewValley;
using StardewValley.TerrainFeatures;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.Extraction;

internal sealed class GameStateExtractor
{
    public GameStateDto Extract()
    {
        if (!Context.IsWorldReady || Game1.player == null)
            throw new InvalidOperationException("Game world is not ready.");

        Farmer player = Game1.player;
        Farm farm = Game1.getFarm();

        var state = new GameStateDto();

        // 1. Player Info
        state.Player = new PlayerDto
        {
            Name = player.Name,
            FarmName = !string.IsNullOrWhiteSpace(player.farmName.Value) 
                ? $"{player.farmName.Value} Farm" 
                : "Farm",
            Gold = player.Money
        };

        // 2. Date & Time
        state.Date = new DateTimeDto
        {
            Season = Game1.currentSeason,
            Day = Game1.dayOfMonth,
            Year = Game1.year,
            TimeOfDay = Game1.timeOfDay
        };

        // 3. Farm & Crops
        ExtractFarmAndCrops(farm, state);

        // 4. Community Center
        state.CommunityCenter = BundleParser.Parse();

        // 5. Active Quests
        state.ActiveQuests = QuestResolver.ResolveAll();

        // 6. Social Dynamics
        state.Social = SocialResolver.ResolveAll();

        return state;
    }

    private void ExtractFarmAndCrops(Farm farm, GameStateDto state)
    {
        if (farm?.terrainFeatures == null) return;

        var farmDto = new FarmDto();
        var cropsList = new List<CropDto>();

        foreach (var pair in farm.terrainFeatures.Pairs)
        {
            if (pair.Value is not HoeDirt dirt || dirt.crop == null)
                continue;

            farmDto.CropCount++;

            if (dirt.crop.dead.Value)
            {
                farmDto.DeadCrops++;
            }
            else if (dirt.crop.currentPhase.Value >= dirt.crop.phaseDays.Count - 1 || 
                    (dirt.crop.fullyGrown.Value && dirt.crop.dayOfCurrentPhase.Value <= 0))
            {
                farmDto.ReadyToHarvest++;
            }

            if (!dirt.isWatered() && !dirt.crop.dead.Value)
            {
                farmDto.NeedsWater++;
            }

            // Resolve detailed crop info
            CropDto? cropDto = CropResolver.Resolve(dirt, pair.Key);
            if (cropDto != null)
            {
                cropsList.Add(cropDto);
            }
        }

        state.Farm = farmDto;
        state.Crops = cropsList;
    }
}
