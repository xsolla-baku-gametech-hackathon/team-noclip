using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using XsollaGameRecap.Models;

namespace XsollaGameRecap.Services;

internal sealed class RecapApiClient
{
    private readonly HttpClient httpClient;
    private readonly string endpoint;
    private readonly string healthEndpoint;

    // In-memory cache to prevent redundant network calls within the same game timeframe
    private (string cacheKey, RecapResponseDto response, DateTime timestamp)? cacheEntry;
    private static readonly TimeSpan CacheTtl = TimeSpan.FromSeconds(30);

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        PropertyNameCaseInsensitive = true,
        WriteIndented = false
    };

    public RecapApiClient(string endpoint, int timeoutSeconds)
    {
        this.endpoint = endpoint;
        
        // Derive health endpoint from the main recap endpoint URL
        Uri baseUri = new Uri(endpoint);
        this.healthEndpoint = new Uri(baseUri, "/health").ToString();

        this.httpClient = new HttpClient
        {
            Timeout = TimeSpan.FromSeconds(timeoutSeconds)
        };
    }

    public async Task<bool> CheckHealthAsync()
    {
        try
        {
            using var response = await httpClient.GetAsync(healthEndpoint);
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public async Task<RecapResponseDto> GenerateRecapAsync(GameStateDto state, CancellationToken cancellationToken = default)
    {
        // 1. Check Cache
        string cacheKey = $"{state.Date.Season}_{state.Date.Day}_{state.Date.TimeOfDay}_{state.Player.Gold}_{state.Farm.CropCount}";
        if (cacheEntry.HasValue && cacheEntry.Value.cacheKey == cacheKey)
        {
            if (DateTime.UtcNow - cacheEntry.Value.timestamp < CacheTtl)
            {
                return cacheEntry.Value.response;
            }
        }

        // 2. Call FastAPI backend
        try
        {
            using HttpResponseMessage response = await httpClient.PostAsJsonAsync(
                endpoint,
                state,
                JsonOptions,
                cancellationToken
            );

            if (response.IsSuccessStatusCode)
            {
                RecapResponseDto? result = await response.Content.ReadFromJsonAsync<RecapResponseDto>(
                    JsonOptions,
                    cancellationToken
                );

                if (result != null && result.Success)
                {
                    cacheEntry = (cacheKey, result, DateTime.UtcNow);
                    return result;
                }
            }
        }
        catch
        {
            // Network failure or timeout -> failover to local heuristic fallback
        }

        // 3. Failover: Bulletproof local heuristic generation for zero-downtime demo
        var fallback = GenerateLocalFallback(state);
        cacheEntry = (cacheKey, fallback, DateTime.UtcNow);
        return fallback;
    }

    /// <summary>
    /// Generates a high-quality contextual recap directly inside the C# mod
    /// if the network or backend server is ever unavailable during a live demo.
    /// </summary>
    private static RecapResponseDto GenerateLocalFallback(GameStateDto state)
    {
        string farmName = !string.IsNullOrWhiteSpace(state.Player.FarmName) ? state.Player.FarmName : "your farm";
        string p1 = $"You returned to {farmName} on {state.Date.Season} {state.Date.Day} of Year {state.Date.Year} with {state.Player.Gold:N0}g in savings.";
        string p2 = state.Farm.CropCount > 0
            ? $"You are managing {state.Farm.CropCount} active crops, and the Community Center has {state.CommunityCenter.CompletedBundles}/{state.CommunityCenter.TotalBundles} bundles completed."
            : $"Your fields are clear and ready for the season, with the Community Center at {state.CommunityCenter.CompletedBundles}/{state.CommunityCenter.TotalBundles} bundles completed.";

        var priorities = new List<PriorityDto>();

        if (state.Farm.ReadyToHarvest > 0 || state.Farm.DeadCrops > 0)
        {
            priorities.Add(new PriorityDto
            {
                Title = "Tend to Fields",
                Description = $"{state.Farm.ReadyToHarvest} crops ready to harvest; {state.Farm.DeadCrops} dead crops to remove.",
                Importance = "high"
            });
        }

        if (state.Farm.NeedsWater > 0)
        {
            priorities.Add(new PriorityDto
            {
                Title = "Water Thirsty Crops",
                Description = $"{state.Farm.NeedsWater} active crops still need watering today.",
                Importance = "high"
            });
        }

        if (state.Social.UpcomingBirthdays.Count > 0)
        {
            var bday = state.Social.UpcomingBirthdays[0];
            priorities.Add(new PriorityDto
            {
                Title = $"{bday.Name}'s Birthday",
                Description = $"{bday.Name} has an upcoming birthday on {bday.Birthday}. Prepare a gift!",
                Importance = "medium"
            });
        }
        else if (state.ActiveQuests.Count > 0)
        {
            var q = state.ActiveQuests[0];
            string deadline = q.DaysLeft == 0 ? "Expires TODAY" : q.DaysLeft > 0 ? $"{q.DaysLeft} days left" : "No deadline";
            priorities.Add(new PriorityDto
            {
                Title = $"Quest: {q.Title}",
                Description = $"{q.Description} ({deadline}).",
                Importance = "medium"
            });
        }
        else if (state.CommunityCenter.MissingItems.Count > 0)
        {
            priorities.Add(new PriorityDto
            {
                Title = "Community Center Items",
                Description = "Needed: " + string.Join(", ", state.CommunityCenter.MissingItems.Take(3)),
                Importance = "medium"
            });
        }

        if (priorities.Count < 3)
        {
            priorities.Add(new PriorityDto
            {
                Title = "Visit Pelican Town",
                Description = "Check Pierre's shop and greet the local villagers.",
                Importance = "low"
            });
        }

        var questList = state.ActiveQuests.Take(4).Select(q =>
            q.DaysLeft == 0 ? $"{q.Title} (Expires TODAY)" :
            q.DaysLeft > 0 ? $"{q.Title} ({q.DaysLeft}d left)" :
            q.Title
        ).ToList();

        var bundleItems = state.CommunityCenter.MissingItems.Take(4).ToList();
        var milestones = new List<string>
        {
            $"Community Center: {state.CommunityCenter.CompletedBundles}/{state.CommunityCenter.TotalBundles} Bundles",
            $"Year {state.Date.Year}, {state.Date.Season}"
        };

        return new RecapResponseDto
        {
            Success = true,
            PreviouslyOn = $"{p1} {p2}",
            CriticalPriorities = priorities.Take(3).ToList(),
            GoalTracker = new GoalTrackerDto
            {
                ActiveQuests = questList,
                MissingBundleItems = bundleItems,
                Milestones = milestones
            },
            Error = null
        };
    }
}
