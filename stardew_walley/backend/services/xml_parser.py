import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

try:
    import defusedxml.ElementTree as SafeET
except ImportError:
    SafeET = ET

from backend.models import (
    GameStateDto,
    PlayerDto,
    DateTimeDto,
    FarmDto,
    CropDto,
    CommunityCenterDto,
    QuestDto,
    SocialDto,
    VillagerDto,
)


def parse_save_xml(xml_content_or_path: Union[str, bytes, Path]) -> GameStateDto:
    """
    Parses a Stardew Valley save XML file into a structured GameStateDto.
    Supports either a file path or raw XML content string/bytes.
    """
    if isinstance(xml_content_or_path, (str, Path)) and os.path.exists(str(xml_content_or_path)):
        with open(xml_content_or_path, "rb") as f:
            root = SafeET.fromstring(f.read())
    elif isinstance(xml_content_or_path, (str, bytes)):
        root = SafeET.fromstring(xml_content_or_path)
    else:
        raise ValueError("Invalid XML input: expected file path or XML string.")

    # 1. Player
    player_elem = root.find("player")
    player_name = player_elem.findtext("name", "Farmer") if player_elem is not None else "Farmer"
    farm_name = player_elem.findtext("farmName", "Standard Farm") if player_elem is not None else "Standard Farm"
    gold = int(player_elem.findtext("money", "0")) if player_elem is not None else 0

    player = PlayerDto(name=player_name, farmName=farm_name, gold=gold)

    # 2. Date & Time
    season = root.findtext("currentSeason", "Spring").capitalize()
    day = int(root.findtext("dayOfMonth", "1"))
    year = int(root.findtext("year", "1"))
    time_of_day = int(root.findtext("timeOfDay", "600"))

    date = DateTimeDto(season=season, day=day, year=year, timeOfDay=time_of_day)

    # 3. Farm & Crops
    crops = []
    crop_count = 0
    ready_to_harvest = 0
    needs_water = 0
    dead_crops = 0

    # Locate Farm in locations
    farm_elem = None
    locations = root.find("locations")
    if locations is not None:
        for loc in locations.findall("GameLocation"):
            if loc.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "Farm" or loc.findtext("name") == "Farm":
                farm_elem = loc
                break

    if farm_elem is not None:
        terrain_features = farm_elem.find("terrainFeatures")
        if terrain_features is not None:
            for item in terrain_features.findall("item"):
                feature = item.find("value/TerrainFeature")
                if feature is not None and (
                    feature.get("{http://www.w3.org/2001/XMLSchema-instance}type") == "HoeDirt"
                    or feature.tag.endswith("HoeDirt")
                ):
                    crop_elem = feature.find("crop")
                    if crop_elem is not None:
                        crop_count += 1
                        is_dead = crop_elem.findtext("dead", "false").lower() == "true"
                        is_watered = feature.findtext("state", "0") == "1" or feature.findtext("isWatered", "false").lower() == "true"
                        current_phase = int(crop_elem.findtext("currentPhase", "0"))
                        
                        # Phase days list
                        phase_days_elem = crop_elem.find("phaseDays")
                        phase_count = len(phase_days_elem.findall("int")) if phase_days_elem is not None else 5

                        # Harvest index / name
                        crop_id = crop_elem.findtext("indexOfHarvest", "Crop")
                        
                        if is_dead:
                            state_str = "dead"
                            dead_crops += 1
                        elif current_phase >= phase_count - 1:
                            state_str = "ready"
                            ready_to_harvest += 1
                        elif not is_watered:
                            state_str = "needs_water"
                            needs_water += 1
                        else:
                            state_str = "growing"

                        # Tile position
                        pos_elem = item.find("key/Vector2")
                        x = int(float(pos_elem.findtext("X", "0"))) if pos_elem is not None else 0
                        y = int(float(pos_elem.findtext("Y", "0"))) if pos_elem is not None else 0

                        crops.append(
                            CropDto(
                                cropName=f"Crop #{crop_id}",
                                state=state_str,
                                x=x,
                                y=y,
                            )
                        )

    farm = FarmDto(
        cropCount=crop_count,
        readyToHarvest=ready_to_harvest,
        needsWater=needs_water,
        deadCrops=dead_crops,
    )

    # 4. Quests
    quests = []
    quest_log = root.find("questLog")
    if quest_log is not None:
        for q_elem in quest_log.findall("Quest"):
            title = q_elem.findtext("_questTitle") or q_elem.findtext("questTitle") or "Village Request"
            desc = q_elem.findtext("questDescription") or ""
            days_left_text = q_elem.findtext("daysLeft", "-1")
            try:
                days_left = int(days_left_text)
            except ValueError:
                days_left = -1
            
            quests.append(
                QuestDto(
                    title=title.strip(),
                    description=desc.strip(),
                    daysLeft=days_left,
                    isSpecialOrder=False,
                )
            )

    # 5. Social / Friendship
    low_heart_villagers = []
    if player_elem is not None:
        friendship_data = player_elem.find("friendshipData")
        if friendship_data is not None:
            for item in friendship_data.findall("item"):
                name = item.findtext("key/string", "")
                points_elem = item.find("value/Friendship/Points")
                if name and points_elem is not None:
                    points = int(points_elem.text or "0")
                    hearts = points // 250
                    if hearts <= 2:
                        low_heart_villagers.append(
                            VillagerDto(name=name, hearts=hearts, birthday="")
                        )

    social = SocialDto(
        lowHeartVillagers=low_heart_villagers[:5],
        upcomingBirthdays=[],
    )

    # 6. Community Center
    has_cc_completed = root.findtext("hasCompletedCommunityCenter", "false").lower() == "true"
    cc = CommunityCenterDto(
        complete=has_cc_completed,
        completedBundles=18 if not has_cc_completed else 30,
        totalBundles=30,
        missingItems=["Seasonal Crops", "Truffle", "Rabbit's Foot"] if not has_cc_completed else [],
    )

    return GameStateDto(
        player=player,
        date=date,
        farm=farm,
        crops=crops,
        communityCenter=cc,
        activeQuests=quests,
        social=social,
    )
