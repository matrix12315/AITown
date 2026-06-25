"""
Tests for the Execute module (agent/cognitive/execute.py).

Tests pathfinding (BFS), address resolution, movement, and event recording.
Uses small 5x5 grids for unit tests; real CSV loading for integration.
"""
import datetime
from unittest.mock import MagicMock
from agent.cognitive.execute import (
    load_mazes, resolve_address_to_tiles, find_path,
    execute_movement, execute_action, record_action_event
)


# --- Fake classes for testing ---

class FakeScratch:
    def __init__(self):
        self.name = "Isabella"
        self.curr_time = datetime.datetime(2026, 5, 23, 8, 0)
        self.curr_tile = (2, 2)
        self.act_address = None
        self.act_start_time = None
        self.act_duration = None
        self.act_description = None
        self.act_pronunciatio = None
        self.act_event = (self.name, None, None)
        self.act_obj_description = None
        self.act_obj_pronunciatio = None
        self.act_obj_event = (self.name, None, None)
        self.act_path_set = False
        self.planned_path = []
        self.chatting_with = None


class FakePersona:
    def __init__(self):
        self.name = "Isabella"
        self.scratch = FakeScratch()
        self.a_mem = MagicMock()


# --- Helper: small 5x5 collision grid ---
# 0 = walkable, 32125 = blocked
# Layout:
#   . . . . .
#   . # # # .
#   . . . # .
#   . # . . .
#   . . . . .

def make_small_grid():
    BLOCKED = 32125
    # Layout:
    #   . # . . .
    #   . # . . .
    #   . # . . .
    #   . . . . .
    #   . . . . .
    # Wall at (1,0)-(1,2) blocks left-to-right on rows 0-2
    return [
        [0, BLOCKED, 0, 0, 0],
        [0, BLOCKED, 0, 0, 0],
        [0, BLOCKED, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]


# --- Tests: load_mazes ---

def test_load_mazes():
    """
    Test: loading real CSV files produces correct grid dimensions.

    collision_grid should be 100 rows × 140 columns.
    arena_grid should be the same shape.
    arena_id_to_name should have 63 entries (from arena_blocks.csv).
    """
    collision, arena, id_to_name = load_mazes()
    assert len(collision) == 100
    assert len(collision[0]) == 140
    assert len(arena) == 100
    assert len(arena[0]) == 140
    assert len(id_to_name) == 63
    # Check a known arena
    assert "the Ville:Hobbs Cafe:cafe" in id_to_name.values()


# --- Tests: resolve_address_to_tiles ---

def test_resolve_address():
    """
    Test: resolving a known address returns walkable tiles.

    "the Ville:Hobbs Cafe:cafe" should map to tiles where
    the arena_maze has that arena's ID and collision is 0.
    """
    collision, arena, id_to_name = load_mazes()
    tiles = resolve_address_to_tiles(
        "the Ville:Hobbs Cafe:cafe", arena, id_to_name, collision
    )
    assert len(tiles) > 0
    # All tiles should be walkable
    for x, y in tiles:
        assert collision[y][x] == 0


def test_resolve_address_unknown():
    """
    Test: resolving an unknown address returns empty list.
    """
    collision, arena, id_to_name = load_mazes()
    tiles = resolve_address_to_tiles(
        "the Ville:Nonexistent:place", arena, id_to_name, collision
    )
    assert tiles == []


# --- Tests: find_path ---

def test_find_path_straight():
    """
    Test: path on open ground goes straight.

    On a 5x5 grid with no obstacles, path from (0,0) to (4,0)
    should be 4 steps: (1,0) → (2,0) → (3,0) → (4,0).
    """
    grid = [[0] * 5 for _ in range(5)]
    path = find_path((0, 0), [(4, 0)], grid)
    assert len(path) == 4
    assert path[-1] == (4, 0)


def test_find_path_around_wall():
    """
    Test: path goes around a wall.

    Grid:
      . # . . .
      . # . . .
      . # . . .
      . . . . .
      . . . . .

    Wall at (1,0)-(1,2) blocks the direct route from (0,0) to (2,0).
    Path must go around: (0,0)→(0,1)→(0,2)→(0,3)→(1,3)→(2,3)→(2,2)→(2,1)→(2,0)
    or similar detour via row 3.
    """
    grid = make_small_grid()
    path = find_path((0, 0), [(2, 0)], grid)
    assert len(path) > 0
    assert path[-1] == (2, 0)
    # Path should be longer than 2 (direct distance) due to wall
    assert len(path) > 2


def test_find_path_already_at_target():
    """
    Test: if already on a target tile, path is empty.
    """
    grid = [[0] * 5 for _ in range(5)]
    path = find_path((2, 2), [(2, 2), (3, 3)], grid)
    assert path == []


def test_find_path_no_path():
    """
    Test: if target is completely surrounded by walls, path is empty.
    """
    BLOCKED = 32125
    grid = [
        [0, 0, 0, 0, 0],
        [0, BLOCKED, BLOCKED, BLOCKED, 0],
        [0, BLOCKED, BLOCKED, BLOCKED, 0],
        [0, BLOCKED, BLOCKED, BLOCKED, 0],
        [0, 0, 0, 0, 0],
    ]
    # Target is (2,2) which is blocked
    path = find_path((0, 0), [(2, 2)], grid)
    assert path == []


def test_find_path_empty_targets():
    """
    Test: empty target list returns empty path.
    """
    grid = [[0] * 5 for _ in range(5)]
    path = find_path((0, 0), [], grid)
    assert path == []


def test_find_path_multiple_targets():
    """
    Test: with multiple targets, finds the nearest one.
    """
    grid = [[0] * 5 for _ in range(5)]
    # Targets at (1,0) [distance 1] and (4,0) [distance 4]
    path = find_path((0, 0), [(1, 0), (4, 0)], grid)
    assert len(path) == 1
    assert path[0] == (1, 0)


# --- Tests: execute_movement ---

def test_execute_movement():
    """
    Test: movement pops first tile from path and updates curr_tile.
    """
    p = FakePersona()
    p.scratch.planned_path = [(1, 2), (2, 2), (3, 2)]
    result = execute_movement(p)
    assert result == (1, 2)
    assert p.scratch.curr_tile == (1, 2)
    assert len(p.scratch.planned_path) == 2


def test_execute_movement_empty_path():
    """
    Test: movement with empty path returns None.
    """
    p = FakePersona()
    p.scratch.planned_path = []
    result = execute_movement(p)
    assert result is None


# --- Tests: execute_action ---

def test_execute_action_advances_time():
    """
    Test: execute_action advances curr_time by STEP_DURATION_SECONDS.
    """
    from config import STEP_DURATION_SECONDS
    p = FakePersona()
    p.scratch.curr_time = datetime.datetime(2026, 5, 23, 8, 0, 0)
    execute_action(p)
    expected = datetime.datetime(2026, 5, 23, 8, 0, 0) + datetime.timedelta(seconds=STEP_DURATION_SECONDS)
    assert p.scratch.curr_time == expected


def test_execute_action_sets_path():
    """
    Test: when act_path_set is False and act_address is set,
    execute_action computes a path and sets act_path_set = True.
    """
    collision, arena, id_to_name = load_mazes()
    p = FakePersona()
    p.scratch.curr_tile = (70, 20)
    p.scratch.act_address = "the Ville:Hobbs Cafe:cafe"
    p.scratch.act_path_set = False

    execute_action(p, collision, arena, id_to_name)
    assert p.scratch.act_path_set is True
    # Path should be non-empty if we're not already in the cafe
    assert len(p.scratch.planned_path) > 0


def test_execute_action_moves():
    """
    Test: when path exists, execute_action moves one tile.
    """
    p = FakePersona()
    p.scratch.planned_path = [(3, 2), (4, 2)]
    p.scratch.act_path_set = True
    execute_action(p)
    assert p.scratch.curr_tile == (3, 2)
    assert len(p.scratch.planned_path) == 1


# --- Tests: record_action_event ---

def test_record_action_event():
    """
    Test: recording a finished action calls a_mem.add_event().
    """
    p = FakePersona()
    p.scratch.act_event = ("Isabella", "is", "serving coffee")
    p.scratch.act_description = "serving coffee to customers"
    p.scratch.act_obj_description = None

    llm = MagicMock()
    llm.get_embedding.return_value = [0.1, 0.2, 0.3]

    record_action_event(p, llm)
    p.a_mem.add_event.assert_called_once()
    call_args = p.a_mem.add_event.call_args[0]
    assert call_args[2] == "Isabella"  # subject
    assert call_args[3] == "is"  # predicate
    assert call_args[4] == "serving coffee"  # object


def test_record_action_event_no_description():
    """
    Test: if act_description is None, no event is recorded.
    """
    p = FakePersona()
    p.scratch.act_description = None
    llm = MagicMock()
    record_action_event(p, llm)
    p.a_mem.add_event.assert_not_called()


def test_record_action_event_with_object():
    """
    Test: if act_obj_description is set, two events are recorded.
    """
    p = FakePersona()
    p.scratch.act_event = ("Isabella", "is", "serving coffee")
    p.scratch.act_description = "serving coffee"
    p.scratch.act_obj_description = "coffee machine"
    p.scratch.act_obj_event = ("Isabella", "uses", "coffee machine")

    llm = MagicMock()
    llm.get_embedding.return_value = [0.1, 0.2, 0.3]

    record_action_event(p, llm)
    assert p.a_mem.add_event.call_count == 2
