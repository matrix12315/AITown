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
            agent.step(
                maze=self.arena_grid,
                personas=self.agents
            )

        # Handle conversations AFTER all agents have planned
        # This ensures both agents have their actions set before chatting
        self._handle_conversations()

        # Collect states AFTER conversations (so chat field is populated)
        for name, agent in self.agents.items():
            step_state["states"].append(_to_replay_state(agent._get_state()))

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

    def _handle_conversations(self):
        """
        Handle all active conversations after all agents have planned.

        This runs AFTER all agents' cognitive loops, so both agents have
        their actions set. Each conversation pair is only processed once.
        """
        from agent.cognitive.chat import (
            generate_round, generate_reply, generate_summary,
            store_chat_memory, clear_chat_state
        )

        processed = set()
        for agent_name, agent in self.agents.items():
            if agent.scratch.chat_rounds_left <= 0:
                continue

            other_name = agent.scratch.chatting_with
            if not other_name:
                continue

            # Only process each pair once (use sorted tuple as key)
            pair = tuple(sorted([agent_name, other_name]))
            if pair in processed:
                continue
            processed.add(pair)

            if other_name not in self.agents:
                clear_chat_state(agent)
                continue

            other = self.agents[other_name]

            # Calculate how many rounds fit in one step
            rounds_per_step = max(1, STEP_DURATION_SECONDS // 120)  # 1 round = 2 min

            for _ in range(rounds_per_step):
                if agent.scratch.chat_rounds_left <= 0:
                    break

                # Generate message from agent
                generate_round(agent, other, agent.llm_client)
                # Generate reply from other
                generate_reply(agent, other, other.llm_client)

                # Decrement rounds on both
                agent.scratch.chat_rounds_left -= 1
                other.scratch.chat_rounds_left -= 1

            # Check if conversation is over
            if agent.scratch.chat_rounds_left <= 0:
                # Generate separate summaries for each agent's perspective
                summary_a = generate_summary(agent, other, agent.llm_client)
                summary_b = generate_summary(other, agent, other.llm_client)

                if summary_a:
                    store_chat_memory(agent, other_name, summary_a, agent.llm_client)
                if summary_b:
                    store_chat_memory(other, agent_name, summary_b, other.llm_client)

                clear_chat_state(agent)
                clear_chat_state(other)

                # After conversation, let each agent consider replanning
                _maybe_replan(agent, summary_a)
                _maybe_replan(other, summary_b)

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


def _maybe_replan(persona, summary):
    """
    After a conversation, let the LLM decide if the agent should replan.

    If replanning, clears the current schedule and generates a new one
    that only covers the remaining time until midnight.

    Args:
        persona: the agent who just finished a conversation
        summary: conversation summary text (from their perspective)
    """
    if not summary:
        return

    from agent.prompts import get_prompts
    prompts = get_prompts()

    # Build schedule with actual times
    schedule_lines = []
    if persona.scratch.schedule_start_time:
        t = persona.scratch.schedule_start_time
        for task, dur in persona.scratch.f_daily_schedule:
            schedule_lines.append(f"  {t.strftime('%H:%M')} - {task} ({dur}min)")
            t += datetime.timedelta(minutes=dur)
    else:
        for i, (task, dur) in enumerate(persona.scratch.f_daily_schedule):
            schedule_lines.append(f"  {i+1}. {task} ({dur}min)")
    schedule_text = "\n".join(schedule_lines) if schedule_lines else "  (empty)"

    prompt = f"""{persona.scratch.get_str_iss()}

I just finished a conversation.
Summary: {summary}

Current task: {persona.scratch.act_description or 'none'}
Current time: {persona.scratch.curr_time.strftime('%H:%M')}

Current schedule:
{schedule_text}

Should I change my current plan based on this conversation?
Output exactly one line:
replan: yes / no"""

    response = persona.llm_client.generate(prompt, system_prompt=prompts.SYSTEM_PROMPT)
    if not response:
        return

    should_replan = False
    for line in response.strip().split("\n"):
        line = line.strip().lower()
        if line.startswith("replan:"):
            value = line.split(":", 1)[1].strip()
            should_replan = value in ("yes", "true", "是")

    if should_replan:
        # Calculate remaining minutes until end of day
        now = persona.scratch.curr_time
        midnight = now.replace(hour=23, minute=59, second=59)
        remaining = int((midnight - now).total_seconds() / 60)

        # Clear schedule — next step will generate a new one for remaining time
        persona.scratch.f_daily_schedule = []
        persona.scratch.f_daily_schedule_hourly_org = []
        persona.scratch.schedule_start_time = None
        persona.scratch.act_address = None
        persona.scratch.act_description = None


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

    # Build chat info if agent is in a conversation
    chat = None
    chatting_with = agent_state.get("chatting_with")
    chat_history = agent_state.get("chat_history")
    if chatting_with and chat_history:
        # Get the last message in the conversation
        last_msg = chat_history[-1] if chat_history else None
        chat = {
            "with": chatting_with,
            "msg": last_msg["msg"] if last_msg else None
        }

    return {
        "x": tile[0] if tile else 0,
        "y": tile[1] if tile else 0,
        "address": agent_state.get("act_address") or "",
        "desc": agent_state.get("act_description") or "idle",
        "emoji": agent_state.get("act_pronunciatio") or "😶",
        "chat": chat
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
