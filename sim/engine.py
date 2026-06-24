"""
Simulation Engine — Main Loop and Output Generation
====================================================
The top-level orchestrator that runs the AI Town simulation.

What does it do?
    1. Loads the world map (collision grid + arena grid)
    2. Creates Persona agents from JSON config files
    3. Runs the cognitive loop for all agents each step
    4. Saves replay.json (for frontend) and diary.md (for humans)

Usage:
    sim = Simulation(["data/personas/en/isabella_rodriguez.json", ...])
    sim.run(steps=100)
    sim.save("feb14")
"""
import datetime
import json
import os

from agent.persona import Persona
from agent.cognitive.execute import load_mazes
from config import (
    PERSONAS_DIR, SIMULATIONS_DIR, STEP_DURATION_SECONDS, LANGUAGE
)


class Simulation:
    """
    Main simulation engine.

    Attributes:
        agents: dict of {name: Persona} for all agents
        curr_time: current simulation time
        step_count: how many steps have been executed
        history: list of per-step state dicts (for replay.json)
    """

    def __init__(self, persona_paths, llm_client=None, start_time=None):
        """
        Initialize the simulation.

        Args:
            persona_paths: list of paths to persona JSON files
            llm_client: LLMClient instance. If None, creates a new one.
            start_time: simulation start time. Default: 2023-02-14 08:00:00
        """
        # ---- LLM client ----
        if llm_client is None:
            from llm.client import LLMClient
            llm_client = LLMClient()

        # ---- Load world map (shared by all agents) ----
        self.collision_grid, self.arena_grid, self.arena_id_to_name = load_mazes()

        # ---- Create agents ----
        self.agents = {}
        for path in persona_paths:
            p = Persona(
                path, llm_client,
                self.collision_grid, self.arena_grid, self.arena_id_to_name
            )
            self.agents[p.name] = p

        # ---- Time tracking ----
        if start_time is None:
            start_time = datetime.datetime(2023, 2, 14, 8, 0, 0)
        self.start_time = start_time
        self.curr_time = start_time
        self.step_count = 0

        # ---- Replay history ----
        self.history = []

    def step(self):
        """
        Run one simulation step for all agents.

        Steps:
        1. Set curr_time on all agents
        2. Each agent runs its cognitive loop (perceive→plan→reflect→execute)
        3. Collect agent states into a history entry
        4. Advance curr_time by STEP_DURATION_SECONDS

        Returns:
            dict with "time" and "states" keys
        """
        step_state = {
            "time": self.curr_time.strftime("%H:%M:%S"),
            "states": []
        }

        # Set current time on all agents before they act
        for agent in self.agents.values():
            agent.scratch.curr_time = self.curr_time

        # Run cognitive loop for each agent
        for name, agent in self.agents.items():
            agent_state = agent.step(
                maze=self.arena_grid,
                personas=self.agents
            )
            step_state["states"].append(_to_replay_state(agent_state))

        # Record and advance
        self.history.append(step_state)
        self.curr_time += datetime.timedelta(seconds=STEP_DURATION_SECONDS)
        self.step_count += 1

        return step_state

    def run(self, steps=1):
        """
        Run the simulation for N steps.

        Args:
            steps: number of steps to execute

        Returns:
            list of step state dicts
        """
        results = []
        for _ in range(steps):
            results.append(self.step())
        return results

    def save(self, sim_name):
        """
        Save simulation results to data/simulations/<sim_name>/.

        Creates:
        - replay.json: compact replay data for frontend
        - diary.md: human-readable log of agent actions

        Args:
            sim_name: name for this simulation run (e.g., "feb14")
        """
        sim_dir = os.path.join(SIMULATIONS_DIR, sim_name)
        os.makedirs(sim_dir, exist_ok=True)

        # Save replay.json
        replay = self._build_replay()
        replay_path = os.path.join(sim_dir, "replay.json")
        with open(replay_path, 'w', encoding='utf-8') as f:
            json.dump(replay, f, indent=2, ensure_ascii=False)

        # Generate and save diary.md
        diary = _generate_diary(replay)
        diary_path = os.path.join(sim_dir, "diary.md")
        with open(diary_path, 'w', encoding='utf-8') as f:
            f.write(diary)

        return sim_dir

    def _build_replay(self):
        """
        Build the replay.json structure from history.

        Returns:
            dict matching the replay.json contract:
            {
                "meta": {"start_time", "step_duration", "agents"},
                "steps": [{"time", "states"}, ...]
            }
        """
        return {
            "meta": {
                "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "step_duration": STEP_DURATION_SECONDS,
                "agents": list(self.agents.keys())
            },
            "steps": self.history
        }


def _to_replay_state(agent_state):
    """
    Convert a Persona._get_state() dict to replay format.

    Replay format: {x, y, address, desc, emoji, chat}

    Args:
        agent_state: dict from Persona._get_state()

    Returns:
        dict in replay format
    """
    tile = agent_state.get("curr_tile")
    return {
        "x": tile[0] if tile else 0,
        "y": tile[1] if tile else 0,
        "address": agent_state.get("act_address") or "",
        "desc": agent_state.get("act_description") or "idle",
        "emoji": agent_state.get("act_pronunciatio") or "😶",
        "chat": None
    }


def _generate_diary(replay_data):
    """
    Generate a human-readable diary.md from replay data.

    Groups consecutive identical actions per agent into time ranges.
    Pure formatting — no LLM involved.

    Args:
        replay_data: dict with "meta" and "steps" keys

    Returns:
        string containing the full diary in markdown format
    """
    meta = replay_data["meta"]
    steps = replay_data["steps"]
    agents = meta["agents"]

    lines = [
        "# Simulation Diary",
        f"Started: {meta['start_time']}",
        f"Step duration: {meta['step_duration']}s",
        ""
    ]

    # Process each agent
    for agent_idx, agent_name in enumerate(agents):
        lines.append(f"## {agent_name}")

        # Track consecutive identical actions
        prev_desc = None
        prev_address = None
        range_start = None

        for step in steps:
            if agent_idx >= len(step["states"]):
                continue

            state = step["states"][agent_idx]
            desc = state["desc"]
            address = state["address"]
            time_str = step["time"]

            # If action changed, emit the previous range
            if desc != prev_desc or address != prev_address:
                if prev_desc is not None:
                    _emit_diary_entry(lines, range_start, time_str,
                                      prev_desc, prev_address)
                range_start = time_str
                prev_desc = desc
                prev_address = address

        # Emit the last range
        if prev_desc is not None:
            last_time = steps[-1]["time"] if steps else range_start
            # End time is one step after the last observation
            _emit_diary_entry(lines, range_start, last_time,
                              prev_desc, prev_address)

        lines.append("")  # blank line between agents

    return "\n".join(lines)


def _emit_diary_entry(lines, start_time, end_time, desc, address):
    """
    Add one diary entry: a time range with action description.

    Args:
        lines: list to append to
        start_time: when the action started (HH:MM:SS)
        end_time: when the action ended (HH:MM:SS)
        desc: action description
        address: location address
    """
    if start_time == end_time:
        time_range = f"### {start_time}"
    else:
        time_range = f"### {start_time} — {end_time}"
    lines.append(time_range)
    if address:
        lines.append(f"- {desc} @ {address}")
    else:
        lines.append(f"- {desc}")
