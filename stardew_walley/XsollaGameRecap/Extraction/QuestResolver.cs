using System;
using System.Collections.Generic;
using StardewValley;
using StardewValley.Quests;
using StardewValley.SpecialOrders;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.Extraction;

internal static class QuestResolver
{
    public static List<QuestDto> ResolveAll()
    {
        var result = new List<QuestDto>();

        try
        {
            // 1. Regular active quests from player log
            if (Game1.player?.questLog != null)
            {
                foreach (Quest quest in Game1.player.questLog)
                {
                    if (quest == null || quest.completed.Value)
                        continue;

                    string title = !string.IsNullOrWhiteSpace(quest.questTitle) 
                        ? quest.questTitle 
                        : quest.GetName();

                    string description = !string.IsNullOrWhiteSpace(quest.currentObjective)
                        ? quest.currentObjective
                        : quest.questDescription;

                    int daysLeft = quest.dailyQuest.Value ? Math.Max(0, quest.daysLeft.Value) : -1;

                    result.Add(new QuestDto
                    {
                        Title = CleanText(title),
                        Description = CleanText(description),
                        DaysLeft = daysLeft,
                        IsSpecialOrder = false
                    });
                }
            }

            // 2. Special Orders
            if (Game1.player?.team?.specialOrders != null)
            {
                foreach (SpecialOrder order in Game1.player.team.specialOrders)
                {
                    if (order == null)
                        continue;

                    int daysRemaining = Math.Max(0, order.dueDate.Value - Game1.Date.TotalDays);

                    result.Add(new QuestDto
                    {
                        Title = CleanText(order.GetName()),
                        Description = CleanText(order.GetDescription()),
                        DaysLeft = daysRemaining,
                        IsSpecialOrder = true
                    });
                }
            }
        }
        catch (Exception)
        {
            // Fail gracefully
        }

        return result;
    }

    private static string CleanText(string? input)
    {
        if (string.IsNullOrWhiteSpace(input))
            return "";

        return input.Replace("\n", " ").Replace("\r", "").Trim();
    }
}
