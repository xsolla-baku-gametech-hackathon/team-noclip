using System.Collections.Generic;

namespace XsollaGameRecap.Models;

public sealed class GameStateDto
{
    public PlayerDto Player { get; set; } = new();
    public DateTimeDto Date { get; set; } = new();
    public FarmDto Farm { get; set; } = new();
    public List<CropDto> Crops { get; set; } = new();
    public CommunityCenterDto CommunityCenter { get; set; } = new();
    public List<QuestDto> ActiveQuests { get; set; } = new();
    public SocialDto Social { get; set; } = new();
}

public sealed class PlayerDto
{
    public string Name { get; set; } = "";
    public string FarmName { get; set; } = "";
    public int Gold { get; set; }
}

public sealed class DateTimeDto
{
    public string Season { get; set; } = "";
    public int Day { get; set; }
    public int Year { get; set; }
    public int TimeOfDay { get; set; }
}

public sealed class FarmDto
{
    public int CropCount { get; set; }
    public int ReadyToHarvest { get; set; }
    public int NeedsWater { get; set; }
    public int DeadCrops { get; set; }
}

public sealed class CropDto
{
    public string CropName { get; set; } = "";
    public string State { get; set; } = ""; // "ready", "needs_water", "dead", "growing"
    public int X { get; set; }
    public int Y { get; set; }
}

public sealed class CommunityCenterDto
{
    public bool Complete { get; set; }
    public int CompletedBundles { get; set; }
    public int TotalBundles { get; set; }
    public List<string> MissingItems { get; set; } = new();
}

public sealed class QuestDto
{
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public int DaysLeft { get; set; } = -1; // -1 for indefinite, 0 for today, 1+ for days remaining
    public bool IsSpecialOrder { get; set; }
}

public sealed class SocialDto
{
    public List<VillagerDto> LowHeartVillagers { get; set; } = new();
    public List<VillagerDto> UpcomingBirthdays { get; set; } = new();
}

public sealed class VillagerDto
{
    public string Name { get; set; } = "";
    public int Hearts { get; set; }
    public string Birthday { get; set; } = "";
}
