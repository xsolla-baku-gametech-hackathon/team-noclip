import pytest
from fastapi.testclient import TestClient
import io

from backend.main import app
from backend.models import GameStateDto, RecapResponseDto
from backend.services.heuristic_service import generate_heuristic_recap
from backend.services.xml_parser import parse_save_xml
from backend.tests.mock_data import MOCK_GAME_STATE, SAMPLE_STARDEW_XML

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data


def test_game_state_dto_deserialization():
    state = GameStateDto.model_validate(MOCK_GAME_STATE)
    assert state.player.name == "Aykhan"
    assert state.player.farm_name == "Misty Farm"
    assert state.player.gold == 12450
    assert state.date.season == "Summer"
    assert state.date.day == 18
    assert state.farm.crop_count == 47
    assert state.farm.ready_to_harvest == 8
    assert len(state.crops) == 3
    assert len(state.active_quests) == 2
    assert state.active_quests[1].days_left == 0


def test_heuristic_recap_rules():
    state = GameStateDto.model_validate(MOCK_GAME_STATE)
    recap = generate_heuristic_recap(state)

    assert recap.success is True
    # Rule 1: Exactly 2 sentences in previouslyOn
    sentences = [s.strip() for s in recap.previously_on.split(".") if s.strip()]
    assert len(sentences) == 2

    # Rule 2: Max 3 critical priorities
    assert len(recap.critical_priorities) <= 3
    assert len(recap.critical_priorities) > 0

    # Check that high urgency (ready/dead crops or expiring quest) is prioritized
    priorities = [p.title for p in recap.critical_priorities]
    assert any("Harvest" in p or "Expiring Quest" in p for p in priorities)

    # Rule 3: Goal tracker contains quests and bundle items
    assert len(recap.goal_tracker.active_quests) > 0
    assert "Delivery to Clint (Expires TODAY)" in recap.goal_tracker.active_quests
    assert "Red Cabbage" in recap.goal_tracker.missing_bundle_items


def test_xml_parser():
    state = parse_save_xml(SAMPLE_STARDEW_XML)
    assert state.player.name == "Aykhan"
    assert state.player.farm_name == "Misty Farm"
    assert state.player.gold == 12450
    assert state.date.season == "Summer"
    assert state.farm.crop_count == 1
    assert state.farm.ready_to_harvest == 1
    assert len(state.active_quests) == 1
    assert state.active_quests[0].title == "Robin's Request"


def test_api_recap_endpoint():
    response = client.post("/api/recap", json=MOCK_GAME_STATE)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "previouslyOn" in data
    assert "criticalPriorities" in data
    assert "goalTracker" in data


def test_api_recap_heuristic_endpoint():
    response = client.post("/api/recap/heuristic", json=MOCK_GAME_STATE)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["criticalPriorities"]) <= 3


def test_api_recap_from_xml_endpoint():
    xml_bytes = SAMPLE_STARDEW_XML.encode("utf-8")
    files = {"file": ("test_save.xml", io.BytesIO(xml_bytes), "application/xml")}
    response = client.post("/api/recap/from-xml", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "previouslyOn" in data
