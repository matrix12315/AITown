import json
import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.generate.return_value = "wake up (60)\nwork (480)\nsleep (540)"
    llm.get_embedding.return_value = [0.1] * 1024
    return llm


@pytest.fixture
def sample_grids():
    collision = [[0] * 5 for _ in range(5)]
    arena = [["100"] * 5 for _ in range(5)]
    arena_id_to_name = {"100": "the Ville:house:room"}
    return collision, arena, arena_id_to_name


@pytest.fixture
def persona_jsons(tmp_path):
    """Create two temp persona JSON files."""
    agents = []
    for name in ["Alice", "Bob"]:
        data = {
            "name": name,
            "first_name": name,
            "last_name": "Test",
            "age": 25,
            "innate": "friendly",
            "learned": f"{name} is a student.",
            "currently": "studying",
            "lifestyle": "normal",
            "living_area": "the Ville:house:room",
            "daily_plan_req": "study all day",
            "vision_r": 4,
            "att_bandwidth": 3,
            "retention": 5,
            "curr_tile": None,
            "act_event": [name, None, None],
            "act_obj_event": [None, None, None],
        }
        path = tmp_path / f"{name.lower()}.json"
        with open(path, 'w') as f:
            json.dump(data, f)
        agents.append(str(path))
    return agents


class TestSimulationInit:
    @patch("sim.engine.load_mazes")
    def test_creates_agents(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        assert len(sim.agents) == 2
        assert "Alice" in sim.agents
        assert "Bob" in sim.agents

    @patch("sim.engine.load_mazes")
    def test_default_start_time(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        assert sim.curr_time == datetime(2023, 2, 14, 8, 0, 0)
        assert sim.step_count == 0

    @patch("sim.engine.load_mazes")
    def test_custom_start_time(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        t = datetime(2023, 3, 1, 10, 0, 0)
        sim = Simulation(persona_jsons, llm_client=mock_llm, start_time=t)
        assert sim.curr_time == t


class TestSimulationStep:
    @patch("sim.engine.load_mazes")
    def test_returns_state(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        result = sim.step()
        assert "time" in result
        assert "states" in result
        assert isinstance(result["states"], list)

    @patch("sim.engine.load_mazes")
    def test_states_match_agent_count(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        result = sim.step()
        assert len(result["states"]) == 2

    @patch("sim.engine.load_mazes")
    def test_advances_time(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        sim.step()
        assert sim.curr_time == datetime(2023, 2, 14, 8, 0, 10)
        assert sim.step_count == 1

    @patch("sim.engine.load_mazes")
    def test_replay_state_format(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        result = sim.step()
        state = result["states"][0]
        assert "x" in state
        assert "y" in state
        assert "address" in state
        assert "desc" in state
        assert "emoji" in state
        assert "chat" in state


class TestSimulationRun:
    @patch("sim.engine.load_mazes")
    def test_run_n_steps(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        results = sim.run(3)
        assert len(results) == 3
        assert sim.step_count == 3

    @patch("sim.engine.load_mazes")
    def test_history_accumulates(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        sim.run(5)
        assert len(sim.history) == 5


class TestSimulationSave:
    @patch("sim.engine.load_mazes")
    def test_save_creates_replay(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        sim.run(3)
        sim_dir = sim.save("test_run")
        replay_path = os.path.join(sim_dir, "replay.json")
        assert os.path.exists(replay_path)
        with open(replay_path) as f:
            replay = json.load(f)
        assert "meta" in replay
        assert "steps" in replay
        assert len(replay["steps"]) == 3
        assert replay["meta"]["agents"] == ["Alice", "Bob"]

    @patch("sim.engine.load_mazes")
    def test_save_creates_diary(self, mock_load, persona_jsons, mock_llm, sample_grids):
        mock_load.return_value = sample_grids
        from sim.engine import Simulation
        sim = Simulation(persona_jsons, llm_client=mock_llm)
        sim.run(3)
        sim_dir = sim.save("test_run")
        diary_path = os.path.join(sim_dir, "diary.md")
        assert os.path.exists(diary_path)
        with open(diary_path) as f:
            content = f.read()
        assert "# Simulation Diary" in content
        assert "## Alice" in content
        assert "## Bob" in content


class TestDiaryGeneration:
    def test_groups_consecutive(self):
        from sim.engine import _generate_diary
        replay = {
            "meta": {
                "start_time": "2023-02-14 08:00:00",
                "step_duration": 10,
                "agents": ["Alice"]
            },
            "steps": [
                {"time": "08:00:00", "states": [
                    {"x": 1, "y": 1, "address": "home", "desc": "sleeping", "emoji": "😴", "chat": None}
                ]},
                {"time": "08:00:10", "states": [
                    {"x": 1, "y": 1, "address": "home", "desc": "sleeping", "emoji": "😴", "chat": None}
                ]},
                {"time": "08:00:20", "states": [
                    {"x": 2, "y": 1, "address": "cafe", "desc": "eating", "emoji": "🍽️", "chat": None}
                ]},
            ]
        }
        diary = _generate_diary(replay)
        assert "## Alice" in diary
        assert "08:00:00 — 08:00:10" in diary or "08:00:00 — 08:00:20" in diary
        assert "sleeping" in diary
        assert "eating" in diary

    def test_single_step_diary(self):
        from sim.engine import _generate_diary
        replay = {
            "meta": {
                "start_time": "2023-02-14 08:00:00",
                "step_duration": 10,
                "agents": ["Bob"]
            },
            "steps": [
                {"time": "08:00:00", "states": [
                    {"x": 0, "y": 0, "address": "home", "desc": "idle", "emoji": "😶", "chat": None}
                ]}
            ]
        }
        diary = _generate_diary(replay)
        assert "## Bob" in diary
        assert "08:00:00" in diary
        assert "idle" in diary

    def test_empty_steps(self):
        from sim.engine import _generate_diary
        replay = {
            "meta": {
                "start_time": "2023-02-14 08:00:00",
                "step_duration": 10,
                "agents": ["Alice"]
            },
            "steps": []
        }
        diary = _generate_diary(replay)
        assert "# Simulation Diary" in diary
        assert "## Alice" in diary
