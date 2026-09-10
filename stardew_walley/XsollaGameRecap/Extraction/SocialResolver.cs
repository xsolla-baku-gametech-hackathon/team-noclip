using System;
using System.Collections.Generic;
using System.Linq;
using StardewValley;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.Extraction;

internal static class SocialResolver
{
    public static SocialDto ResolveAll()
    {
        var result = new SocialDto();

        try
        {
            var uniqueVillagers = Game1.locations
                .SelectMany(location => location.characters)
                .Where(npc => npc != null && npc.IsVillager && npc.Age != 2 && npc is not StardewValley.Characters.Child && !npc.IsMonster)
                .GroupBy(npc => npc.Name)
                .Select(group => group.First())
                .ToList();

            string currentSeason = Game1.currentSeason;
            int currentDay = Game1.dayOfMonth;

            foreach (NPC npc in uniqueVillagers)
            {
                int hearts = Game1.player.getFriendshipHeartLevelForNPC(npc.Name);

                // Low heart villagers (<= 2 hearts)
                if (hearts <= 2)
                {
                    result.LowHeartVillagers.Add(new VillagerDto
                    {
                        Name = npc.displayName ?? npc.Name,
                        Hearts = hearts,
                        Birthday = !string.IsNullOrEmpty(npc.Birthday_Season) 
                            ? $"{npc.Birthday_Season} {npc.Birthday_Day}" 
                            : ""
                    });
                }

                // Birthday check (today or tomorrow)
                if (string.Equals(npc.Birthday_Season, currentSeason, StringComparison.OrdinalIgnoreCase))
                {
                    if (npc.Birthday_Day == currentDay || npc.Birthday_Day == currentDay + 1)
                    {
                        result.UpcomingBirthdays.Add(new VillagerDto
                        {
                            Name = npc.displayName ?? npc.Name,
                            Hearts = hearts,
                            Birthday = $"{npc.Birthday_Season} {npc.Birthday_Day}"
                        });
                    }
                }
            }

            // Cap lists to keep JSON payload lean
            result.LowHeartVillagers = result.LowHeartVillagers.Take(5).ToList();
            result.UpcomingBirthdays = result.UpcomingBirthdays.Take(3).ToList();
        }
        catch (Exception)
        {
            // Fail gracefully
        }

        return result;
    }
}
