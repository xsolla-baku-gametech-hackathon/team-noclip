from backend.models import (
    GameStateDto,
    RecapResponseDto,
    PriorityDto,
    GoalTrackerDto,
)


def generate_heuristic_recap(state: GameStateDto) -> RecapResponseDto:
    """
    Deterministic recap generator that executes in <1ms without any external API calls.
    Follows all prompt engineering constraints:
    - 2-sentence 'previouslyOn'
    - Up to 3 sorted critical priorities
    - Compact goal tracker
    """
    # 1. Previously On (Strictly 2 sentences)
    farm_name = state.player.farm_name or "your farm"
    s1 = (
        f"You returned to {farm_name} on {state.date.season} {state.date.day} of Year {state.date.year} "
        f"with {state.player.gold:,}g in savings."
    )
    
    if state.farm.crop_count > 0:
        s2 = (
            f"Your fields have {state.farm.crop_count} crops underway, while the Community Center "
            f"stands at {state.community_center.completed_bundles}/{state.community_center.total_bundles} bundles restored."
        )
    else:
        s2 = (
            f"Your fields are currently clear for new planting, and the Community Center "
            f"has {state.community_center.completed_bundles}/{state.community_center.total_bundles} bundles completed."
        )
    previously_on = f"{s1} {s2}"

    # 2. Critical Priorities (Priority Hierarchy: High -> Medium -> Low, max 3)
    priorities = []

    # Priority A: Dead or Ready Crops (Urgent farm management)
    if state.farm.dead_crops > 0 and state.farm.ready_to_harvest > 0:
        priorities.append(
            PriorityDto(
                title="Harvest & Clear Fields",
                description=f"{state.farm.ready_to_harvest} crops are ready for picking today, and {state.farm.dead_crops} dead crops need clearing.",
                importance="high",
            )
        )
    elif state.farm.ready_to_harvest > 0:
        priorities.append(
            PriorityDto(
                title="Harvest Ready Crops",
                description=f"{state.farm.ready_to_harvest} crops are ripe and ready to harvest today.",
                importance="high",
            )
        )
    elif state.farm.dead_crops > 0:
        priorities.append(
            PriorityDto(
                title="Clear Dead Crops",
                description=f"{state.farm.dead_crops} dead crops are occupying valuable tilled soil.",
                importance="high",
            )
        )

    # Priority B: Watering needs
    if state.farm.needs_water > 0:
        priorities.append(
            PriorityDto(
                title="Water Dry Crops",
                description=f"{state.farm.needs_water} active crops still need water before you sleep.",
                importance="high",
            )
        )

    # Priority C: Urgent Quests or Birthdays
    urgent_quests = [q for q in state.active_quests if 0 <= q.days_left <= 1]
    if urgent_quests:
        q = urgent_quests[0]
        urgency_str = "expires TODAY" if q.days_left == 0 else "expires tomorrow"
        priorities.append(
            PriorityDto(
                title=f"Expiring Quest: {q.title}",
                description=f"{q.description} ({urgency_str}).",
                importance="high",
            )
        )

    if len(priorities) < 3 and state.social.upcoming_birthdays:
        bday = state.social.upcoming_birthdays[0]
        priorities.append(
            PriorityDto(
                title=f"{bday.name}'s Birthday",
                description=f"{bday.name} celebrates a birthday on {bday.birthday}. Prepare a loved gift!",
                importance="medium",
            )
        )

    # Priority D: Community Center items
    if len(priorities) < 3 and state.community_center.missing_items:
        items = ", ".join(state.community_center.missing_items[:3])
        priorities.append(
            PriorityDto(
                title="Community Center Needs",
                description=f"Collect seasonal bundle requirements: {items}.",
                importance="medium",
            )
        )

    # Priority E: General quests
    if len(priorities) < 3:
        general_quests = [q for q in state.active_quests if q not in urgent_quests]
        if general_quests:
            q = general_quests[0]
            dl_str = f"{q.days_left} days left" if q.days_left > 0 else "No time limit"
            priorities.append(
                PriorityDto(
                    title=f"Quest: {q.title}",
                    description=f"{q.description} ({dl_str}).",
                    importance="medium",
                )
            )

    # Priority F: Low-heart friendship
    if len(priorities) < 3 and state.social.low_heart_villagers:
        villager = state.social.low_heart_villagers[0]
        priorities.append(
            PriorityDto(
                title=f"Befriend {villager.name}",
                description=f"You have {villager.hearts} hearts with {villager.name}. Stop by to chat or offer a gift.",
                importance="low",
            )
        )

    # Final padding if farm is empty
    if len(priorities) < 3:
        priorities.append(
            PriorityDto(
                title="Visit Pelican Town",
                description="Check the bulletin board outside Pierre's shop for new requests and seasonal seeds.",
                importance="low",
            )
        )

    # 3. Goal Tracker
    formatted_quests = []
    for q in state.active_quests[:5]:
        if q.days_left == 0:
            formatted_quests.append(f"{q.title} (Expires TODAY)")
        elif q.days_left > 0:
            formatted_quests.append(f"{q.title} ({q.days_left}d left)")
        else:
            formatted_quests.append(q.title)

    missing_bundle_items = state.community_center.missing_items[:5]

    milestones = []
    if state.community_center.complete:
        milestones.append("Community Center: Fully Restored!")
    else:
        milestones.append(
            f"Community Center: {state.community_center.completed_bundles}/{state.community_center.total_bundles} Bundles Completed"
        )
    milestones.append(f"Date: {state.date.season} Year {state.date.year}")

    return RecapResponseDto(
        success=True,
        previously_on=previously_on,
        critical_priorities=priorities[:3],
        goal_tracker=GoalTrackerDto(
            active_quests=formatted_quests,
            missing_bundle_items=missing_bundle_items,
            milestones=milestones,
        ),
        error=None,
    )
