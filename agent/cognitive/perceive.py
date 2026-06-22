"""
Perceive Module — Detect Events in the Environment
====================================================
The first step of the cognitive loop:
    PERCEIVE → Retrieve → Plan → Reflect → Execute

What does "perceive" mean?
    An agent can only "see" things within its vision radius (4 tiles in each
    direction). This module scans nearby tiles for other agents and records
    what they're doing as events.

What does it produce?
    A list of new events to add to the agent's associative memory.
    Example: "Maria is painting in the studio" → (Maria, is, painting)

Why filter out duplicates?
    Without deduplication, the agent would record "Maria is painting" every
    single step (every 10 game seconds). That wastes memory and makes
    retrieval noisy. We check the last N events (retention=5) and skip
    any with the same (subject, predicate, object) triple.

Exploration:
    When an agent enters a new area for the first time, they "discover" it.
    The discovery is recorded as an event (high poignancy = 8) and the area
    is added to their known_areas in spatial memory. This means agents can
    only plan to go places they've already discovered.

Connection to the paper:
    Section 4.1 — "Each agent receives information about the environment
    through perception. The agent's perception is limited to a radius
    around its current position."
"""


def perceive(persona, maze, personas, arena_grid=None, arena_id_to_name=None):
    """
    Scan the environment and return new events the agent noticed.

    Steps:
    1. Check if the agent has entered a new area (exploration)
    2. Check every other agent — are they within vision radius?
    3. If visible, record what they're doing as an event
    4. Filter out events already in recent memory (deduplication)

    Args:
        persona: the agent doing the perceiving
        maze: the world map (not used yet — will be needed for object interactions)
        personas: dict of {name: Persona} — all agents in the simulation
        arena_grid: 2D arena ID grid (needed for exploration detection)
        arena_id_to_name: dict mapping arena IDs to address strings

    Returns:
        List of event dicts, each with:
        - subject: who (e.g., "Maria")
        - predicate: what kind of action (e.g., "is")
        - object: what they're doing (e.g., "painting")
        - description: human-readable text (e.g., "Maria is painting in the studio")
        - created: datetime when perceived
        - poignancy: importance score (2 for observed actions, 8 for discoveries)
    """
    perceived = []

    # Step 1: Exploration — check if agent entered a new area
    if arena_grid is not None and arena_id_to_name is not None:
        cx, cy = persona.scratch.curr_tile
        if 0 <= cy < len(arena_grid) and 0 <= cx < len(arena_grid[cy]):
            arena_id = arena_grid[cy][cx]
            area_name = arena_id_to_name.get(arena_id, None)
            if area_name:
                is_new = persona.s_mem.add_area(area_name)
                if is_new:
                    perceived.append({
                        "subject": persona.name,
                        "predicate": "discovered",
                        "object": area_name,
                        "description": f"{persona.name} discovered {area_name} for the first time",
                        "created": persona.scratch.curr_time,
                        "poignancy": 8,  # high importance — new discovery
                    })

    # Step 2: Get this agent's position and vision radius
    cx, cy = persona.scratch.curr_tile
    vr = persona.scratch.vision_r  # default 4 tiles

    # Step 3: Check each other agent
    for other_name, other_persona in personas.items():
        # Skip self
        if other_name == persona.name:
            continue
        # Skip agents with no position yet
        if other_persona.scratch.curr_tile is None:
            continue

        # Calculate distance (Manhattan distance on grid)
        ox, oy = other_persona.scratch.curr_tile
        if abs(ox - cx) <= vr and abs(oy - cy) <= vr:
            # This agent is within vision radius — we can see them

            # Step 3a: Record what they're doing
            if other_persona.scratch.act_description:
                # Build a human-readable description
                desc = f"{other_name} is {other_persona.scratch.act_description}"

                # Build the SPO triple for structured storage
                # e.g., ("Maria", "is", "painting")
                s = other_name
                p = "is"
                # Take the first word of the action as the "object"
                # e.g., "painting in the studio" → "painting"
                o = other_persona.scratch.act_description.split()[0] \
                    if other_persona.scratch.act_description else "idle"

                perceived.append({
                    "subject": s,
                    "predicate": p,
                    "object": o,
                    "description": desc,
                    "created": persona.scratch.curr_time,
                    "poignancy": 2,  # low importance — just observing someone else
                })

    # Step 4: Deduplication — filter out events already in recent memory
    # (applies to both discovery events and observed agent events)
    # get_summarized_latest_events returns SPO tuples of the last N events
    recent_summaries = persona.a_mem.get_summarized_latest_events(
        persona.scratch.retention  # default 5
    )

    filtered = []
    for event in perceived:
        spo = (event["subject"], event["predicate"], event["object"])
        if spo not in recent_summaries:
            filtered.append(event)

    # Step 5: Update the reflection trigger counter
    # Each new event's poignancy decreases the counter.
    # When the counter hits 0, the agent will reflect on the next cycle.
    for event in filtered:
        persona.scratch.importance_trigger_curr -= event["poignancy"]
        persona.scratch.importance_ele_n += 1

    return filtered
