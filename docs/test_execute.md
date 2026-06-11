# Execute Module Test Documentation

## What is Execute?
The fifth and final step of the cognitive loop. Handles agent movement (BFS pathfinding on the collision maze), time advancement (10 seconds per step), and event recording to associative memory.

## Tests

### test_load_mazes
**Asserts:** Real CSV files load correctly — collision_grid is 100x140, arena_grid is 100x140, arena_id_to_name has 63 entries, and "the Ville:Hobbs Cafe:cafe" is present.
**Why it passes:** The three CSV files (collision_maze.csv, arena_maze.csv, arena_blocks.csv) contain exactly these dimensions and data.

### test_resolve_address
**Asserts:** Resolving "the Ville:Hobbs Cafe:cafe" returns a non-empty list of (x,y) tiles, all of which are walkable (collision == 0).
**Why it passes:** The arena_blocks.csv maps this name to an arena ID, and the arena_maze has tiles with that ID. The filter removes blocked tiles.

### test_resolve_address_unknown
**Asserts:** Resolving "the Ville:Nonexistent:place" returns an empty list.
**Why it passes:** No arena in arena_blocks.csv matches this name, so the reverse lookup finds no arena ID, and no tiles are returned.

### test_find_path_straight
**Asserts:** Path from (0,0) to (4,0) on an open 5x5 grid is 4 steps, ending at (4,0).
**Why it passes:** With no obstacles, BFS finds the shortest straight-line path along row 0.

### test_find_path_around_wall
**Asserts:** Path from (0,0) to (2,0) with a wall at (1,0)-(1,2) is longer than 2 steps, ending at (2,0).
**Why it passes:** The wall blocks the direct route, so BFS must detour through row 3, making the path longer than the Manhattan distance.

### test_find_path_already_at_target
**Asserts:** Path from (2,2) when (2,2) is in the target list is empty.
**Why it passes:** The function checks `if start in target_tiles` and returns [] immediately.

### test_find_path_no_path
**Asserts:** Path to a blocked tile (2,2) surrounded by walls returns empty list.
**Why it passes:** BFS can never reach a tile where collision != 0, and all surrounding tiles are also blocked.

### test_find_path_empty_targets
**Asserts:** Empty target list returns empty path.
**Why it passes:** The function checks `if not target_tiles` and returns [] immediately.

### test_find_path_multiple_targets
**Asserts:** With targets at (1,0) and (4,0), path from (0,0) finds (1,0) (the closer one).
**Why it passes:** BFS explores level by level, so it encounters (1,0) at distance 1 before reaching (4,0) at distance 4.

### test_execute_movement
**Asserts:** Popping from a 3-tile path returns the first tile, updates curr_tile, and leaves 2 tiles.
**Why it passes:** `planned_path.pop(0)` removes and returns the first element.

### test_execute_movement_empty_path
**Asserts:** Empty path returns None without changing curr_tile.
**Why it passes:** The function checks `if not planned_path` and returns None.

### test_execute_action_advances_time
**Asserts:** After execute_action, curr_time is 10 seconds later.
**Why it passes:** The function adds `timedelta(seconds=STEP_DURATION_SECONDS)` where STEP_DURATION_SECONDS=10.

### test_execute_action_sets_path
**Asserts:** With act_path_set=False and act_address="the Ville:Hobbs Cafe:cafe", execute_action computes a path and sets act_path_set=True.
**Why it passes:** The function calls resolve_address_to_tiles and find_path, stores the result in planned_path, and sets the flag.

### test_execute_action_moves
**Asserts:** With a 2-tile path, execute_action moves curr_tile to the first tile and leaves 1 tile.
**Why it passes:** execute_action calls execute_movement which pops the first tile.

### test_record_action_event
**Asserts:** Recording an action with act_event=("Isabella", "is", "serving coffee") calls a_mem.add_event() once with the correct SPO triple.
**Why it passes:** The function extracts s/p/o from act_event and passes them to add_event along with description, keywords, and embedding.

### test_record_action_event_no_description
**Asserts:** If act_description is None, a_mem.add_event is not called.
**Why it passes:** The function has an early return guard for missing description.

### test_record_action_event_with_object
**Asserts:** If act_obj_description is set, two events are recorded (action + object interaction).
**Why it passes:** The function checks for act_obj_description and calls add_event a second time with the object's SPO triple.
