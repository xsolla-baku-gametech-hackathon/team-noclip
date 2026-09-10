import time
import pytest

from backend.models import GameStateDto, RecapResponseDto
from backend.services.cache_service import StateCacheService
from backend.services.xml_parser import parse_save_xml
from backend.tests.mock_data import MOCK_GAME_STATE, SAMPLE_STARDEW_XML


def test_xml_parser_detailed_fields():
    state = parse_save_xml(SAMPLE_STARDEW_XML)
    
    # Player
    assert state.player.name == "Aykhan"
    assert state.player.farm_name == "Misty Farm"
    assert state.player.gold == 12450

    # Date
    assert state.date.season == "Summer"
    assert state.date.day == 18
    assert state.date.year == 2
    assert state.date.time_of_day == 930

    # Farm and Crops
    assert state.farm.crop_count == 1
    assert state.farm.ready_to_harvest == 1
    assert state.farm.dead_crops == 0
    assert len(state.crops) == 1
    assert state.crops[0].state == "ready"
    assert state.crops[0].x == 12
    assert state.crops[0].y == 18

    # Quests
    assert len(state.active_quests) == 1
    assert state.active_quests[0].title == "Robin's Request"
    assert state.active_quests[0].days_left == 2

    # Social
    assert len(state.social.low_heart_villagers) == 1
    assert state.social.low_heart_villagers[0].name == "Penny"
    assert state.social.low_heart_villagers[0].hearts == 2


def test_cache_service_hit_and_miss():
    cache = StateCacheService(default_ttl_seconds=5.0)
    state = GameStateDto.model_validate(MOCK_GAME_STATE)

    # Initial get -> Miss
    assert cache.get(state) is None
    assert cache.size == 0

    # Set mock response
    mock_response = RecapResponseDto(
        success=True,
        previouslyOn="Cached recap sentence one. Cached recap sentence two.",
        criticalPriorities=[],
        goalTracker={"activeQuests": [], "missingBundleItems": [], "milestones": []},
    )
    cache.set(state, mock_response)

    # Subsequent get -> Hit
    cached = cache.get(state)
    assert cached is not None
    assert cached.previously_on == mock_response.previously_on
    assert cache.size == 1


def test_cache_service_state_change_invalidation():
    cache = StateCacheService(default_ttl_seconds=10.0)
    state1 = GameStateDto.model_validate(MOCK_GAME_STATE)

    mock_resp1 = RecapResponseDto(
        success=True,
        previouslyOn="Day 18 recap. Everything is fine.",
        criticalPriorities=[],
        goalTracker={"activeQuests": [], "missingBundleItems": [], "milestones": []},
    )
    cache.set(state1, mock_resp1)

    # Modify state (e.g. day advanced or crops watered)
    modified_dict = dict(MOCK_GAME_STATE)
    modified_dict["farm"] = dict(MOCK_GAME_STATE["farm"])
    modified_dict["farm"]["needsWater"] = 0
    state2 = GameStateDto.model_validate(modified_dict)

    # Fingerprint must be different
    assert cache.compute_fingerprint(state1) != cache.compute_fingerprint(state2)
    assert cache.get(state2) is None
    assert cache.get(state1) is not None


def test_cache_service_ttl_expiration():
    cache = StateCacheService(default_ttl_seconds=0.1)
    state = GameStateDto.model_validate(MOCK_GAME_STATE)

    mock_resp = RecapResponseDto(
        success=True,
        previouslyOn="Expiring recap. Gone in a flash.",
        criticalPriorities=[],
        goalTracker={"activeQuests": [], "missingBundleItems": [], "milestones": []},
    )
    cache.set(state, mock_resp, ttl_seconds=0.05)
    time.sleep(0.08)

    # Should be expired
    assert cache.get(state) is None
