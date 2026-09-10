using System.Collections.Generic;

namespace XsollaGameRecap.Models;

public sealed class RecapResponseDto
{
    public bool Success { get; set; } = true;
    public string PreviouslyOn { get; set; } = "";
    public List<PriorityDto> CriticalPriorities { get; set; } = new();
    public GoalTrackerDto GoalTracker { get; set; } = new();
    public string? Error { get; set; }
}

public sealed class PriorityDto
{
    public string Title { get; set; } = "";
    public string Description { get; set; } = "";
    public string Importance { get; set; } = "medium"; // "high", "medium", "low"
}

public sealed class GoalTrackerDto
{
    public List<string> ActiveQuests { get; set; } = new();
    public List<string> MissingBundleItems { get; set; } = new();
    public List<string> Milestones { get; set; } = new();
}
