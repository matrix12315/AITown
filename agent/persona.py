"""
Persona — The Agent
===================
A Persona is a complete AI agent. It owns three memory systems:
- Scratch: working memory (identity, current action, daily plan)
- AssociativeMemory: long-term memory (events, thoughts, chats)
- SpatialMemory: knowledge of the world map hierarchy

It orchestrates the cognitive loop by calling five modules each step:
    Perceive → Retrieve → Plan → Reflect → Execute

Usage:
    collision_grid, arena_grid, arena_id_to_name = load_mazes()
    llm = LLMClient()
    persona = Persona("data/personas/isabella_rodriguez.json", llm,
                      collision_grid, arena_grid, arena_id_to_name)
    state = persona.step()  # run one cognitive loop iteration
"""
import json

from agent.memory.scratch import Scratch
from agent.memory.associative import AssociativeMemory
from agent.memory.spatial import SpatialMemory
from agent.cognitive.perceive import perceive
from agent.cognitive.plan import plan
from agent.cognitive.reflect import reflect
from agent.cognitive.execute import execute_action, record_action_event


class Persona:
    """
    A complete AI agent with memory and cognitive abilities.

    Attributes:
        name: full name (e.g., "Isabella Rodriguez")
        scratch: working memory — identity, current state, daily plan
        a_mem: associative memory — long-term events, thoughts, chats
        s_mem: spatial memory — world map hierarchy
        llm_client: API client for text generation and embeddings
        collision_grid: 2D walkability grid (0=walkable, 32125=blocked)
        arena_grid: 2D arena ID grid
        arena_id_to_name: dict mapping arena IDs to "world:sector:arena" strings
    """

    def __init__(self, json_path, llm_client,
                 collision_grid=None, arena_grid=None, arena_id_to_name=None):
        """
        Load a persona from a JSON config file and initialize all memory systems.

        The JSON file contains ALL Scratch fields — identity, perception settings,
        reflection triggers, daily schedule, etc. These are loaded via
        Scratch.load_from_dict() which sets any matching attribute.

        Args:
            json_path: path to the persona JSON file
            llm_client: LLMClient instance for text generation and embeddings
            collision_grid: 2D walkability grid (from load_mazes)
            arena_grid: 2D arena ID grid (from load_mazes)
            arena_id_to_name: dict mapping arena IDs to address strings (from load_mazes)
        """
        # ---- Store references ----
        self.llm_client = llm_client
        self.collision_grid = collision_grid
        self.arena_grid = arena_grid
        self.arena_id_to_name = arena_id_to_name

        # ---- Initialize memory systems ----
        self.scratch = Scratch()          # working memory (identity + current state)
        self.a_mem = AssociativeMemory()  # long-term memory (events, thoughts, chats)
        self.s_mem = SpatialMemory()      # world map hierarchy

        # ---- Load persona config from JSON ----
        # The JSON contains ALL scratch fields. load_from_dict() sets any
        # attribute that exists on the Scratch object. This overwrites defaults
        # like vision_r=4 with the JSON value (e.g., vision_r=8).
        with open(json_path, 'r') as f:
            persona_data = json.load(f)
        self.scratch.load_from_dict(persona_data)

        # ---- Set name shortcut ----
        self.name = self.scratch.name

        # ---- Fix data types from JSON ----
        # JSON has arrays for act_event and act_obj_event, but Python code
        # uses tuples for SPO triples. Convert lists to tuples.
        if isinstance(self.scratch.act_event, list):
            self.scratch.act_event = tuple(self.scratch.act_event)
        if isinstance(self.scratch.act_obj_event, list):
            self.scratch.act_obj_event = tuple(self.scratch.act_obj_event)

        # ---- Set spawn point if curr_tile is null ----
        # The JSON has curr_tile: null. We need a starting position on the map.
        # Find a walkable tile in the agent's living_area.
        if self.scratch.curr_tile is None:
            self.scratch.curr_tile = self._find_spawn_tile()

    def _find_spawn_tile(self):
        """
        Find a walkable tile in the agent's living_area for spawning.

        Uses the arena_grid and collision_grid to find the first walkable
        tile in the agent's home location.

        Returns:
            (x, y) tuple, or (0, 0) if no valid tile found.
        """
        if self.arena_grid is None or self.collision_grid is None:
            return (0, 0)

        # Try to find tiles in the living area
        if self.scratch.living_area:
            from agent.cognitive.execute import resolve_address_to_tiles
            tiles = resolve_address_to_tiles(
                self.scratch.living_area,
                self.arena_grid, self.arena_id_to_name, self.collision_grid
            )
            if tiles:
                return tiles[0]

        # Fallback: find any walkable tile
        for y in range(len(self.collision_grid)):
            for x in range(len(self.collision_grid[y])):
                if self.collision_grid[y][x] == 0:
                    return (x, y)

        return (0, 0)

    def step(self, maze=None, personas=None):
        """
        Run one iteration of the cognitive loop:
            Perceive → Retrieve → Plan → Reflect → Execute

        Called once per simulation step (every 10 game-time seconds).

        Args:
            maze: arena_grid (2D list of arena ID strings). Required for perceive.
            personas: dict of {name: Persona} for all agents. Required for perceive
                      to detect other agents nearby.

        Returns:
            dict with the agent's current state for frontend rendering.
        """
        # Step 1: Perceive — detect what's happening around the agent
        perceive(self, maze, personas)

        # Step 2: Plan — decide what to do (generate schedule if needed,
        # determine next action if current one is finished)
        plan(self, self.llm_client)

        # Step 3: Reflect — generate insights if enough experiences accumulated
        reflect(self, self.llm_client)

        # Step 4: Record finished action as event in long-term memory
        # Must happen BEFORE execute_action, which may start a new action
        if self.scratch.act_check_finished():
            record_action_event(self, self.llm_client)

        # Step 5: Execute — advance time, move along path, compute new paths
        execute_action(self, self.collision_grid, self.arena_grid,
                       self.arena_id_to_name)

        # Step 6: Return current state for frontend
        return self._get_state()

    def _get_state(self):
        """
        Return the agent's current state as a dict for frontend rendering.

        The frontend uses this to:
        - Position the agent sprite on the map (curr_tile)
        - Show what the agent is doing (act_description, act_pronunciatio)
        - Display the agent's name and location
        """
        return {
            "name": self.name,
            "curr_tile": self.scratch.curr_tile,
            "act_address": self.scratch.act_address,
            "act_description": self.scratch.act_description,
            "act_pronunciatio": self.scratch.act_pronunciatio,
            "act_start_time": (
                self.scratch.act_start_time.strftime("%H:%M:%S")
                if self.scratch.act_start_time else None
            ),
            "act_duration": self.scratch.act_duration,
            "chatting_with": self.scratch.chatting_with,
        }
