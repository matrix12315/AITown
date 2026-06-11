"""
Execute Module — Movement, Time Advancement, Event Recording
=============================================================
The fifth and final step of the cognitive loop:
    Perceive → Retrieve → Plan → Reflect → EXECUTE

What does "execute" mean?
    After the agent decides what to do (Plan), Execute makes it happen:
    1. Advance simulation time by one step (10 seconds)
    2. Compute a path from current position to the action's location
    3. Move the agent one tile along the path
    4. Record completed actions as events in associative memory

How does movement work?
    - The map is a 140x100 grid of tiles
    - Each tile is either walkable (0) or blocked (32125) in collision_maze.csv
    - When a new action starts, BFS finds the shortest path to the target
    - Each step, the agent moves one tile along the path
    - When the path is empty, the agent has arrived

How does time work?
    - Each simulation step = 10 seconds of game time (STEP_DURATION_SECONDS)
    - Actions have durations in minutes (set by the Plan module)
    - When curr_time >= act_start_time + act_duration, the action is finished

Connection to the paper:
    Section 4.4 — "Agents execute their plans by moving through the world
    and performing actions at their destination."
"""
import csv
import datetime
import os
from collections import deque
from config import MAP_MATRIX_DIR, STEP_DURATION_SECONDS


# =============================================================================
# Maze Loading
# =============================================================================

def load_mazes(collision_path=None, arena_path=None, arena_blocks_path=None):
    """
    Load the three CSV files that define the world map.

    Files:
    - collision_maze.csv: 140x100 grid, 0=walkable, 32125=blocked
    - arena_maze.csv: 140x100 grid, each cell = arena ID
    - arena_blocks.csv: maps arena IDs to names (id, world, sector, arena)

    Returns:
        (collision_grid, arena_grid, arena_id_to_name)
        collision_grid[y][x] = 0 (walkable) or 32125 (blocked)
        arena_grid[y][x] = arena ID string (e.g., "32171")
        arena_id_to_name[arena_id] = "world:sector:arena" (e.g., "the Ville:Hobbs Cafe:cafe")
    """
    if collision_path is None:
        collision_path = os.path.join(MAP_MATRIX_DIR, "maze", "collision_maze.csv")
    if arena_path is None:
        arena_path = os.path.join(MAP_MATRIX_DIR, "maze", "arena_maze.csv")
    if arena_blocks_path is None:
        arena_blocks_path = os.path.join(MAP_MATRIX_DIR, "special_blocks", "arena_blocks.csv")

    # Load collision maze: single row of 14000 values → 100 rows of 140
    collision_flat = _load_csv_row(collision_path)
    collision_grid = []
    for y in range(100):
        row = []
        for x in range(140):
            val = int(collision_flat[y * 140 + x].strip())
            row.append(val)
        collision_grid.append(row)

    # Load arena maze: same shape, values are arena IDs
    arena_flat = _load_csv_row(arena_path)
    arena_grid = []
    for y in range(100):
        row = []
        for x in range(140):
            row.append(arena_flat[y * 140 + x].strip())
        arena_grid.append(row)

    # Load arena ID → name mapping
    arena_id_to_name = {}
    with open(arena_blocks_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4:
                arena_id = row[0].strip()
                name = f"{row[1].strip()}:{row[2].strip()}:{row[3].strip()}"
                arena_id_to_name[arena_id] = name

    return collision_grid, arena_grid, arena_id_to_name


def _load_csv_row(filepath):
    """Load a single-row CSV file and return the list of values."""
    with open(filepath, 'r') as f:
        reader = csv.reader(f)
        return next(reader)


# =============================================================================
# Address Resolution
# =============================================================================

def resolve_address_to_tiles(address, arena_grid, arena_id_to_name, collision_grid):
    """
    Find all walkable tiles in a given arena.

    Example: "the Ville:Hobbs Cafe:cafe" → [(72, 19), (73, 19), ...]

    Steps:
    1. Find the arena ID for this address (reverse lookup from name to ID)
    2. Find all grid cells with that arena ID
    3. Filter to only walkable tiles (collision_grid[y][x] == 0)

    Returns:
        List of (x, y) tuples for walkable tiles in the arena.
        Empty list if the address is unknown or has no walkable tiles.
    """
    # Step 1: Find arena ID from address name
    target_id = None
    for arena_id, name in arena_id_to_name.items():
        if name == address:
            target_id = arena_id
            break

    if target_id is None:
        return []

    # Step 2: Find all tiles with this arena ID
    tiles = []
    for y in range(len(arena_grid)):
        for x in range(len(arena_grid[y])):
            if arena_grid[y][x] == target_id:
                # Step 3: Filter to walkable tiles
                if collision_grid[y][x] == 0:
                    tiles.append((x, y))

    return tiles


# =============================================================================
# Pathfinding (BFS)
# =============================================================================

def find_path(start, target_tiles, collision_grid):
    """
    Find the shortest path from start to any tile in target_tiles using BFS.

    Args:
        start: (x, y) current position
        target_tiles: list of (x, y) — any of these is a valid destination
        collision_grid: 2D grid where 0 = walkable, non-zero = blocked

    Returns:
        List of (x, y) from start to the nearest target (excluding start).
        Empty list if already at target or no path exists.
    """
    if not target_tiles:
        return []

    # If already standing on a target tile, no movement needed
    if start in target_tiles:
        return []

    target_set = set(target_tiles)
    grid_h = len(collision_grid)
    grid_w = len(collision_grid[0]) if grid_h > 0 else 0

    # BFS
    visited = {start}
    queue = deque([(start, [])])  # (current_pos, path_so_far)

    while queue:
        (cx, cy), path = queue.popleft()

        # Try 4 directions: up, down, left, right
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = cx + dx, cy + dy

            # Bounds check
            if nx < 0 or nx >= grid_w or ny < 0 or ny >= grid_h:
                continue
            # Walkability check
            if collision_grid[ny][nx] != 0:
                continue
            # Already visited
            if (nx, ny) in visited:
                continue

            new_path = path + [(nx, ny)]

            # Found target
            if (nx, ny) in target_set:
                return new_path

            visited.add((nx, ny))
            queue.append(((nx, ny), new_path))

    return []  # No path found


# =============================================================================
# Movement
# =============================================================================

def execute_movement(persona):
    """
    Move the agent one tile along their planned path.

    Pops the first tile from planned_path and sets it as curr_tile.
    This is called once per simulation step.

    Returns:
        The new (x, y) position, or None if no path to follow.
    """
    if not persona.scratch.planned_path:
        return None

    next_tile = persona.scratch.planned_path.pop(0)
    persona.scratch.curr_tile = next_tile
    return next_tile


# =============================================================================
# Main Execute Entry Point
# =============================================================================

def execute_action(persona, collision_grid=None, arena_grid=None,
                   arena_id_to_name=None):
    """
    Main entry point — called each simulation step after plan().

    Steps:
    1. Advance simulation time by STEP_DURATION_SECONDS
    2. If path not computed yet, compute it (BFS from curr_tile to act_address)
    3. If path exists, move one tile
    4. If path is empty, agent has arrived (action is "in progress")

    Args:
        persona: the agent
        collision_grid: 2D walkability grid (loaded by load_mazes)
        arena_grid: 2D arena ID grid
        arena_id_to_name: dict mapping arena IDs to address strings
    """
    # Step 1: Advance time
    if persona.scratch.curr_time:
        persona.scratch.curr_time += datetime.timedelta(seconds=STEP_DURATION_SECONDS)

    # Step 2: Compute path if needed
    if (not persona.scratch.act_path_set
            and persona.scratch.act_address
            and persona.scratch.curr_tile
            and collision_grid is not None):

        # Resolve the target address to walkable tiles
        target_tiles = resolve_address_to_tiles(
            persona.scratch.act_address,
            arena_grid, arena_id_to_name, collision_grid
        )

        # Find path from current position to the target
        path = find_path(persona.scratch.curr_tile, target_tiles, collision_grid)
        persona.scratch.planned_path = path
        persona.scratch.act_path_set = True

    # Step 3: Move one tile if path exists
    execute_movement(persona)


# =============================================================================
# Event Recording
# =============================================================================

def record_action_event(persona, llm_client):
    """
    Record the current action as an event in associative memory.

    Called when an action finishes (act_check_finished() returns True).
    Creates an event node with the SPO triple from act_event.

    Args:
        persona: the agent
        llm_client: API client for generating embeddings
    """
    if not persona.scratch.act_description:
        return
    if not persona.scratch.act_event or persona.scratch.act_event[1] is None:
        return

    # Build event details
    s, p, o = persona.scratch.act_event
    description = persona.scratch.act_description
    created = persona.scratch.curr_time
    expiration = created + datetime.timedelta(days=30)

    # Generate keywords from description
    keywords = set(description.lower().split()[:5])

    # Get embedding for the description
    embedding = llm_client.get_embedding(description)

    # Default poignancy for executed actions
    poignancy = 5

    # Add to associative memory
    persona.a_mem.add_event(
        created, expiration,
        s, p, o,
        description, keywords, poignancy,
        description, embedding, []
    )

    # Also record object interaction if there is one
    if (persona.scratch.act_obj_description
            and persona.scratch.act_obj_event
            and persona.scratch.act_obj_event[1] is not None):
        obj_s, obj_p, obj_o = persona.scratch.act_obj_event
        obj_desc = persona.scratch.act_obj_description
        obj_keywords = set(obj_desc.lower().split()[:3])
        obj_embedding = llm_client.get_embedding(obj_desc)

        persona.a_mem.add_event(
            created, expiration,
            obj_s, obj_p, obj_o,
            obj_desc, obj_keywords, poignancy,
            obj_desc, obj_embedding, []
        )
