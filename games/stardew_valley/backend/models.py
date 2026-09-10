from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from typing import List, Optional


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class PlayerDto(CamelModel):
    name: str = "Farmer"
    farm_name: str = "Standard Farm"
    gold: int = 0


class DateTimeDto(CamelModel):
    season: str = "Spring"
    day: int = 1
    year: int = 1
    time_of_day: int = 600


class FarmDto(CamelModel):
    crop_count: int = 0
    ready_to_harvest: int = 0
    needs_water: int = 0
    dead_crops: int = 0


class CropDto(CamelModel):
    crop_name: str = "Unknown Crop"
    state: str = "growing"  # "ready", "needs_water", "dead", "growing"
    x: int = 0
    y: int = 0


class CommunityCenterDto(CamelModel):
    complete: bool = False
    completed_bundles: int = 0
    total_bundles: int = 30
    missing_items: List[str] = Field(default_factory=list)


class QuestDto(CamelModel):
    title: str = "Active Quest"
    description: str = ""
    days_left: int = -1
    is_special_order: bool = False


class VillagerDto(CamelModel):
    name: str = ""
    hearts: int = 0
    birthday: str = ""


class SocialDto(CamelModel):
    low_heart_villagers: List[VillagerDto] = Field(default_factory=list)
    upcoming_birthdays: List[VillagerDto] = Field(default_factory=list)


class GameStateDto(CamelModel):
    player: PlayerDto = Field(default_factory=PlayerDto)
    date: DateTimeDto = Field(default_factory=DateTimeDto)
    farm: FarmDto = Field(default_factory=FarmDto)
    crops: List[CropDto] = Field(default_factory=list)
    community_center: CommunityCenterDto = Field(default_factory=CommunityCenterDto)
    active_quests: List[QuestDto] = Field(default_factory=list)
    social: SocialDto = Field(default_factory=SocialDto)


# Output DTOs (RecapResponse)

class PriorityDto(CamelModel):
    title: str
    description: str
    importance: str = "medium"  # "high", "medium", "low"


class GoalTrackerDto(CamelModel):
    active_quests: List[str] = Field(default_factory=list)
    missing_bundle_items: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)


class RecapResponseDto(CamelModel):
    success: bool = True
    previously_on: str
    critical_priorities: List[PriorityDto] = Field(default_factory=list)
    goal_tracker: GoalTrackerDto = Field(default_factory=GoalTrackerDto)
    error: Optional[str] = None
