"""
Plan Module — Daily Scheduling and Action Determination
========================================================
The third step of the cognitive loop:
    Perceive → Retrieve → PLAN → Reflect → Execute

What does "planning" mean?
    An agent needs to decide WHAT to do and WHERE to do it.
    Planning happens in two layers:

    1. Daily Schedule (high-level):
       "Today I will: wake up (60min), walk to cafe (15min),
        serve coffee (180min), lunch (60min), ..."

    2. Action Details (low-level):
       When a schedule slot activates, the agent fills in specifics:
       address="the Ville:Hobbs Cafe:counter", description="serving coffee",
       pronunciatio="☕", duration=120min

When does planning happen?
    - Once per day: generate_daily_schedule() creates f_daily_schedule
    - Each step: plan() checks if current action is done, if so determines next action

Connection to the paper:
    Section 4.2 — "Each agent maintains a plan that describes their daily
    sequence of activities. The plan is decomposed into hourly chunks."
"""
import datetime
from config import MAP_LOCATIONS
from agent.prompts import get_prompts


def _build_nearby_agents(persona, personas=None):
    """
    Build a string of nearby agents for the LLM prompt.

    Only includes agents that are within vision radius and not sleeping.

    Args:
        persona: the agent looking around
        personas: dict of all agents (if available)

    Returns:
        Formatted string of nearby agents, or "(no one nearby)"
    """
    if not personas:
        return "(no one nearby)"

    cx, cy = persona.scratch.curr_tile or (0, 0)
    vr = persona.scratch.vision_r

    nearby = []
    for other_name, other in personas.items():
        if other_name == persona.name:
            continue
        if not other.scratch.curr_tile:
            continue
        ox, oy = other.scratch.curr_tile
        if abs(ox - cx) <= vr and abs(oy - cy) <= vr:
            # Check if agent is sleeping
            desc = other.scratch.act_description or "idle"
            if "sleep" in desc.lower():
                continue
            nearby.append(f"- {other_name} ({desc})")

    if not nearby:
        return "(no one nearby)"
    return "\n".join(nearby)


def parse_schedule(schedule_text):
    """
    Parse LLM output into (task, duration) tuples.

    Expected format per line:
        "task description (X minutes)"
        or "task description: X min"

    Args:
        schedule_text: raw LLM output, one task per line

    Returns:
        List of (task_description, duration_minutes) tuples.
        If a line can't be parsed, uses 60 minutes as default.
    """
    schedule = []
    for line in schedule_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Try format: "task description (X minutes)" or "task description (X)"
        if "(" in line and ")" in line:
            try:
                paren_start = line.rfind("(")
                task = line[:paren_start].strip()
                # Remove leading dash or number if present
                if task and task[0] in "-•":
                    task = task[1:].strip()
                # Remove leading "HH:MM - " prefix if present
                if " - " in task:
                    task = task.split(" - ", 1)[1].strip()
                duration_str = line[paren_start + 1:].replace(")", "").strip()
                duration = int("".join(c for c in duration_str if c.isdigit()))
                schedule.append((task, duration))
            except (ValueError, IndexError):
                schedule.append((line, 60))

        # Try format: "task description: X min"
        elif "min" in line.lower() and ":" in line:
            try:
                parts = line.rsplit(":", 1)
                task = parts[0].strip()
                if task and task[0] in "-•":
                    task = task[1:].strip()
                if " - " in task:
                    task = task.split(" - ", 1)[1].strip()
                duration = int("".join(c for c in parts[1] if c.isdigit()))
                schedule.append((task, duration))
            except (ValueError, IndexError):
                schedule.append((line, 60))

        # Fallback: treat whole line as a 60-min task
        else:
            task = line.lstrip("-•0123456789. ").strip()
            if " - " in task:
                task = task.split(" - ", 1)[1].strip()
            schedule.append((task, 60))

    return schedule


def generate_daily_schedule(persona, llm_client):
    """
    Generate a high-level daily schedule for the agent.

    The LLM receives the agent's identity and daily constraints,
    then produces a list of tasks covering the full day (e.g., 18 hours).

    The schedule is stored in:
        persona.scratch.f_daily_schedule — the active schedule
        persona.scratch.f_daily_schedule_hourly_org — backup copy

    Args:
        persona: the agent
        llm_client: API client for text generation

    Returns:
        The generated schedule as list of (task, duration) tuples.
        Empty list if generation fails.
    """
    # Don't regenerate if schedule already exists
    if persona.scratch.f_daily_schedule:
        return persona.scratch.f_daily_schedule

    # Build the prompt — identity already includes daily_plan_req, don't repeat it
    identity = persona.scratch.get_str_iss()

    # Build the location list for the LLM — only known locations (exploration)
    known_locs = persona.s_mem.get_known_locations()
    # Fallback to all locations if spatial memory is empty (shouldn't happen)
    if not known_locs:
        known_locs = MAP_LOCATIONS
    loc_list = "\n".join(known_locs)

    # Use language-specific prompt template from registry
    prompts = get_prompts()
    start_time_str = persona.scratch.curr_time.strftime("%H:%M") if persona.scratch.curr_time else "08:00"

    # Calculate total minutes: full day (1440) or remaining time (replan)
    if persona.scratch.curr_time:
        midnight = persona.scratch.curr_time.replace(hour=23, minute=59, second=59)
        remaining = int((midnight - persona.scratch.curr_time).total_seconds() / 60)
        total_minutes = remaining if remaining > 0 else 1440
    else:
        total_minutes = 1440

    prompt = prompts.DAILY_SCHEDULE.format(
        identity=identity,
        locations=loc_list,
        start_time=start_time_str,
        total_minutes=total_minutes
    )

    response = llm_client.generate(prompt, system_prompt=prompts.SYSTEM_PROMPT)
    if not response:
        return []

    # Parse the response into (task, duration) tuples
    schedule = parse_schedule(response)

    if not schedule:
        return []

    # Validate total duration — pad with sleep if schedule is too short
    total = sum(dur for _, dur in schedule)
    if total < total_minutes:
        schedule.append(("sleep", total_minutes - total))

    # Store the schedule
    persona.scratch.f_daily_schedule = schedule
    persona.scratch.f_daily_schedule_hourly_org = list(schedule)
    # Record when the schedule started (used by get_f_daily_schedule_index)
    persona.scratch.schedule_start_time = persona.scratch.curr_time

    return schedule


def determine_action(persona, llm_client, personas=None):
    """
    Given the current schedule slot, generate full action details.

    This is the bridge between "what should I do today" (high-level schedule)
    and "what am I doing right now" (specific action fields for scratch).

    Uses get_f_daily_schedule_index() to find which task is current,
    then asks the LLM to fill in action details.

    Args:
        persona: the agent
        llm_client: API client for text generation
        personas: dict of all agents (for nearby agents info)
    """
    # Find which task in the schedule is current
    idx = persona.scratch.get_f_daily_schedule_index()
    schedule = persona.scratch.f_daily_schedule

    if idx >= len(schedule):
        # Past the end of schedule — default to sleeping
        task_desc = "sleeping"
        task_duration = 480
    else:
        task_desc, task_duration = schedule[idx]

    # Build prompt for action detail generation
    identity = persona.scratch.get_str_iss()
    current_location = persona.scratch.act_address or "unknown"

    # Build the location list for the LLM — only known locations (exploration)
    known_locs = persona.s_mem.get_known_locations()
    if not known_locs:
        known_locs = MAP_LOCATIONS
    loc_list = "\n".join(known_locs)

    # Build nearby agents list (who can this agent see?)
    nearby_agents = _build_nearby_agents(persona, personas)

    # Use language-specific prompt template from registry
    prompts = get_prompts()
    prompt = prompts.ACTION_DETAIL.format(
        identity=identity,
        task_desc=task_desc,
        current_location=current_location,
        current_time=persona.scratch.curr_time.strftime('%H:%M'),
        locations=loc_list,
        nearby_agents=nearby_agents
    )

    response = llm_client.generate(prompt, system_prompt=prompts.SYSTEM_PROMPT)
    if not response:
        # Fallback: use task description directly
        _set_action_from_task(persona, task_desc, task_duration)
        return

    # Parse the LLM response
    chat_type, chat_with, chat_rounds = _parse_and_set_action(persona, response, task_desc, task_duration)

    # Start conversation if LLM decided to chat
    if chat_type in ("small_talk", "deep_talk") and chat_with != "none" and chat_rounds > 0:
        _start_conversation(persona, chat_with, chat_type, chat_rounds, personas)


def _start_conversation(persona, other_name, chat_type, chat_rounds, personas):
    """
    Start a conversation between persona and another agent.

    Sets up chat state on both agents. Actual message generation
    happens in sim.step() after all agents have planned.

    Args:
        persona: the agent initiating the conversation
        other_name: name of the agent to talk to
        chat_type: "small_talk" or "deep_talk"
        chat_rounds: number of rounds (decided by LLM)
        personas: dict of all agents
    """
    if not personas or other_name not in personas:
        return

    other = personas[other_name]

    # Check cooldowns
    from agent.cognitive.chat import can_chat
    if not can_chat(persona, other_name):
        return
    if not can_chat(other, persona.name):
        return

    # Use LLM-decided rounds, clamped to valid range
    if chat_type == "small_talk":
        total_rounds = max(1, min(5, chat_rounds))
    else:  # deep_talk
        total_rounds = max(6, min(20, chat_rounds))

    # Set chat state on both agents
    # IMPORTANT: both agents share the SAME chat_history list
    shared_history = []
    persona.scratch.chatting_with = other_name
    persona.scratch.chat_type = chat_type
    persona.scratch.chat_rounds_left = total_rounds
    persona.scratch.chat_total_rounds = total_rounds
    persona.scratch.chat_history = shared_history

    other.scratch.chatting_with = persona.name
    other.scratch.chat_type = chat_type
    other.scratch.chat_rounds_left = total_rounds
    other.scratch.chat_total_rounds = total_rounds
    other.scratch.chat_history = shared_history


def _parse_and_set_action(persona, response, task_desc, task_duration):
    """
    Parse LLM response into action fields and call add_new_action().

    Expected response format:
        address: the Ville:Hobbs Cafe:counter
        description: serving coffee to customers
        pronunciatio: ☕
        object_description: coffee machine
        object_pronunciatio: ☕
    """
    # Defaults
    address = persona.scratch.act_address or "the Ville:unknown:default"
    description = task_desc
    pronunciatio = "🔄"
    obj_desc = "none"
    obj_pron = "⬜"
    chat_type = "none"
    chat_with = "none"
    chat_rounds = 0

    # Parse each field from the response
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()

        if key == "address":
            address = value
        elif key == "description":
            description = value
        elif key == "pronunciatio":
            pronunciatio = value if value else "🔄"
        elif key in ("object_description", "object desc"):
            obj_desc = value if value.lower() != "none" else "none"
        elif key in ("object_pronunciatio", "object pron"):
            obj_pron = value if value.lower() != "none" else "⬜"
        elif key == "chat_type":
            chat_type = value.lower() if value else "none"
        elif key == "chat_with":
            chat_with = value if value.lower() != "none" else "none"
        elif key == "chat_rounds":
            try:
                chat_rounds = int(value)
            except ValueError:
                chat_rounds = 0

    # Build SPO triple — use first 3 words as the "object" for meaningful summaries
    words = description.split() if description else ["idle"]
    short_desc = " ".join(words[:3]) if len(words) > 3 else description
    event = (persona.name, "is", short_desc)
    obj_event = (persona.name, "uses", obj_desc) if obj_desc != "none" else (persona.name, None, None)

    # Set the action
    persona.scratch.add_new_action(
        action_address=address,
        action_duration=task_duration,
        action_description=description,
        action_pronunciatio=pronunciatio,
        action_event=event,
        chatting_with=None,
        chat=None,
        chatting_with_buffer=None,
        chatting_end_time=None,
        act_obj_description=obj_desc if obj_desc != "none" else None,
        act_obj_pronunciatio=obj_pron if obj_pron != "⬜" else None,
        act_obj_event=obj_event,
    )

    # Return chat decision for the caller to handle
    return chat_type, chat_with, chat_rounds


def _set_action_from_task(persona, task_desc, task_duration):
    """
    Fallback: set action directly from task description without LLM.
    Used when LLM fails to generate action details.
    """
    address = persona.scratch.act_address or "the Ville:unknown:default"
    first_word = task_desc.split()[0] if task_desc else "idle"
    event = (persona.name, "is", first_word)

    persona.scratch.add_new_action(
        action_address=address,
        action_duration=task_duration,
        action_description=task_desc,
        action_pronunciatio="🔄",
        action_event=event,
        chatting_with=None,
        chat=None,
        chatting_with_buffer=None,
        chatting_end_time=None,
        act_obj_description=None,
        act_obj_pronunciatio=None,
        act_obj_event=(persona.name, None, None),
    )


def plan(persona, llm_client, personas=None):
    """
    Main entry point — called each simulation step.

    Logic:
    1. If no daily schedule exists → generate one
    2. If current action is finished → determine next action
    3. If schedule is empty after generation → do nothing

    Args:
        persona: the agent
        llm_client: API client for text generation
        personas: dict of all agents (for nearby agents info)
    """
    # Step 1: Generate daily schedule if needed
    if not persona.scratch.f_daily_schedule:
        generate_daily_schedule(persona, llm_client)

    # Step 2: If no schedule could be generated, give up
    if not persona.scratch.f_daily_schedule:
        return

    # Step 3: If current action is done, determine next action
    if persona.scratch.act_check_finished():
        determine_action(persona, llm_client, personas)
