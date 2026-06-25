"""
Tests for the Persona class (agent/persona.py)

Tested:
- Loading persona from JSON file
- act_event/act_obj_event list→tuple conversion
- _find_spawn_tile with mock map data
- step() orchestration of the cognitive loop
- _get_state() output format
"""
import pytest
import datetime
import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.persona import Persona


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock LLMClient that returns predictable responses."""
    llm = MagicMock()
    # generate() returns a schedule or action details
    llm.generate.return_value = "wake up and morning routine (60)\nwork at cafe (480)\nevening relax (120)\nsleep (480)"
    # get_embedding() returns a fake 1024-dim vector
    llm.get_embedding.return_value = [0.1] * 1024
    return llm


@pytest.fixture
def sample_grid():
    """Create a small 5x5 collision grid for testing."""
    # 0 = walkable, 32125 = blocked
    collision = [
        [0, 0, 0, 0, 0],
        [0, 32125, 32125, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 32125, 0],
        [0, 0, 0, 0, 0],
    ]
    # Arena IDs for each cell
    arena = [
        ["100", "100", "100", "200", "200"],
        ["100", "100", "100", "200", "200"],
        ["300", "300", "300", "300", "300"],
        ["300", "300", "300", "300", "300"],
        ["400", "400", "400", "400", "400"],
    ]
    arena_id_to_name = {
        "100": "the Ville:house:room",
        "200": "the Ville:cafe:counter",
        "300": "the Ville:park:bench",
        "400": "the Ville:library:main",
    }
    return collision, arena, arena_id_to_name


@pytest.fixture
def persona_json_path(tmp_path):
    """Create a temporary persona JSON file."""
    data = {
        "name": "Test Agent",
        "first_name": "Test",
        "last_name": "Agent",
        "age": 25,
        "innate": "curious, kind",
        "learned": "Test Agent is a student.",
        "currently": "studying for exams",
        "lifestyle": "goes to bed at 11pm, wakes up at 7am",
        "living_area": "the Ville:house:room",
        "daily_plan_req": "study all day",
        "vision_r": 8,
        "att_bandwidth": 8,
        "retention": 8,
        "curr_tile": None,
        "act_event": ["Test Agent", None, None],
        "act_obj_event": [None, None, None],
    }
    path = tmp_path / "test_agent.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return str(path)


@pytest.fixture
def persona_json_with_tile(tmp_path):
    """Create a persona JSON with curr_tile already set."""
    data = {
        "name": "Test Agent",
        "first_name": "Test",
        "last_name": "Agent",
        "age": 25,
        "innate": "curious",
        "learned": "student",
        "currently": "studying",
        "lifestyle": "normal",
        "living_area": "the Ville:house:room",
        "daily_plan_req": "study",
        "curr_tile": [2, 3],
        "act_event": ["Test Agent", None, None],
        "act_obj_event": [None, None, None],
    }
    path = tmp_path / "test_agent_tile.json"
    with open(path, 'w') as f:
        json.dump(data, f)
    return str(path)


# =============================================================================
# Test: Loading from JSON
# =============================================================================

class TestPersonaLoading:

    def test_load_identity_fields(self, persona_json_path, mock_llm, sample_grid):
        """Identity fields from JSON are set on scratch."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        assert p.name == "Test Agent"
        assert p.scratch.first_name == "Test"
        assert p.scratch.last_name == "Agent"
        assert p.scratch.age == 25
        assert p.scratch.innate == "curious, kind"
        assert p.scratch.living_area == "the Ville:house:room"
        assert p.scratch.daily_plan_req == "study all day"

    def test_load_perception_overrides(self, persona_json_path, mock_llm, sample_grid):
        """Perception settings from JSON override defaults."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        # Defaults are 4, 3, 5 — JSON has 8, 8, 8
        assert p.scratch.vision_r == 8
        assert p.scratch.att_bandwidth == 8
        assert p.scratch.retention == 8

    def test_act_event_converted_to_tuple(self, persona_json_path, mock_llm, sample_grid):
        """JSON stores act_event as list; Persona converts to tuple."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        assert isinstance(p.scratch.act_event, tuple)
        assert p.scratch.act_event == ("Test Agent", None, None)

    def test_act_obj_event_converted_to_tuple(self, persona_json_path, mock_llm, sample_grid):
        """JSON stores act_obj_event as list; Persona converts to tuple."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        assert isinstance(p.scratch.act_obj_event, tuple)


# =============================================================================
# Test: Spawn Point
# =============================================================================

class TestSpawnPoint:

    def test_spawn_from_living_area(self, persona_json_path, mock_llm, sample_grid):
        """When curr_tile is null, spawn in living_area."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        # living_area is "the Ville:house:room" → arena ID "100"
        # Walkable tiles with arena "100": (0,0), (1,0), (2,0), (0,1), (2,1)
        assert p.scratch.curr_tile is not None
        x, y = p.scratch.curr_tile
        assert collision[y][x] == 0  # must be walkable

    def test_spawn_with_preset_tile(self, persona_json_with_tile, mock_llm, sample_grid):
        """When curr_tile is set in JSON, use it directly."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_with_tile, mock_llm, collision, arena, arena_id_to_name)

        assert p.scratch.curr_tile == [2, 3]

    def test_spawn_fallback_no_grid(self, persona_json_path, mock_llm):
        """When no grid data, spawn at (0, 0)."""
        p = Persona(persona_json_path, mock_llm)

        assert p.scratch.curr_tile == (0, 0)


# =============================================================================
# Test: step() Orchestration
# =============================================================================

class TestStep:

    def test_step_returns_state_dict(self, persona_json_path, mock_llm, sample_grid):
        """step() returns a dict with expected keys."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)
        p.scratch.curr_time = datetime.datetime(2023, 2, 14, 8, 0, 0)

        state = p.step(maze=arena, personas={p.name: p})

        assert isinstance(state, dict)
        assert "name" in state
        assert "curr_tile" in state
        assert "act_address" in state
        assert "act_description" in state

    def test_step_advances_time(self, persona_json_path, mock_llm, sample_grid):
        """step() advances curr_time by STEP_DURATION_SECONDS."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)
        p.scratch.curr_time = datetime.datetime(2023, 2, 14, 8, 0, 0)

        p.step(maze=arena, personas={p.name: p})

        from config import STEP_DURATION_SECONDS
        expected = datetime.datetime(2023, 2, 14, 8, 0, 0) + datetime.timedelta(seconds=STEP_DURATION_SECONDS)
        assert p.scratch.curr_time == expected

    def test_step_calls_plan(self, persona_json_path, mock_llm, sample_grid):
        """step() calls plan() which generates a daily schedule."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)
        p.scratch.curr_time = datetime.datetime(2023, 2, 14, 8, 0, 0)

        p.step(maze=arena, personas={p.name: p})

        # After step, plan() should have generated a schedule
        assert len(p.scratch.f_daily_schedule) > 0


# =============================================================================
# Test: _get_state()
# =============================================================================

class TestGetState:

    def test_state_has_required_keys(self, persona_json_path, mock_llm, sample_grid):
        """_get_state() returns dict with all required keys."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        state = p._get_state()

        required_keys = ["name", "curr_tile", "act_address",
                         "act_description", "act_pronunciatio",
                         "act_start_time", "act_duration", "chatting_with"]
        for key in required_keys:
            assert key in state, f"Missing key: {key}"

    def test_state_name_matches_persona(self, persona_json_path, mock_llm, sample_grid):
        """State name matches the persona's name."""
        collision, arena, arena_id_to_name = sample_grid
        p = Persona(persona_json_path, mock_llm, collision, arena, arena_id_to_name)

        state = p._get_state()

        assert state["name"] == "Test Agent"
