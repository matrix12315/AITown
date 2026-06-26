"""
Scratch Memory (Short-Term / Working Memory)
=============================================
Stores the agent's CURRENT STATE — who they are, what they're doing right now,
and their daily plan.

Think of it as the agent's "active consciousness":
- Identity: name, age, personality, lifestyle
- Current action: what am I doing, where, for how long
- Planning: today's schedule, daily goals
- Reflection triggers: counters that determine when to reflect

Unlike AssociativeMemory (long-term diary), Scratch is constantly updated
and represents the "now" — what the agent is thinking about at this moment.

Fields are organized into groups:
1. Perception settings (how far can I see, how much to pay attention to)
2. Identity (who am I)
3. Reflection settings (when should I reflect)
4. Retrieval weights (how to score memories)
5. Current action state (what am I doing right now)
6. Daily planning (today's schedule)
"""
import datetime
import json


class Scratch:
    def __init__(self):
        # ---- Group 1: Perception Settings ----
        # How far the agent can "see" on the map (in tiles)
        self.vision_r = 4
        # How many events the agent can pay attention to at once
        self.att_bandwidth = 3
        # How many recent events to check for deduplication
        self.retention = 5

        # ---- Group 2: Time & Position ----
        # Current simulation time (updated each step)
        self.curr_time = None
        # Current (x, y) position on the map grid
        self.curr_tile = None
        # Daily plan requirement (e.g., "Open cafe at 8am, work until 8pm")
        self.daily_plan_req = None

        # ---- Group 3: Identity ----
        # These fields define WHO the agent is. They're set once at creation
        # and used in prompts to give the LLM context about the agent's personality.
        self.name = None            # Full name (e.g., "Isabella Rodriguez")
        self.first_name = None      # First name (e.g., "Isabella")
        self.last_name = None       # Last name (e.g., "Rodriguez")
        self.age = None             # Age in years
        self.innate = None          # Born-with traits (e.g., "friendly, outgoing")
        self.learned = None         # Acquired traits (e.g., "cafe owner, painter")
        self.currently = None       # Current goal (e.g., "planning a party")
        self.lifestyle = None       # Daily habits (e.g., "early riser, vegetarian")
        self.living_area = None     # Where they live (location path)

        # ---- Group 4: Reflection Settings ----
        # How many memories to forget over time (not actively used yet)
        self.concept_forget = 100
        # How often to reflect (in minutes of game time)
        self.daily_reflection_time = 60 * 3
        # How many memories to consider for each reflection
        self.daily_reflection_size = 5
        # Threshold for overlapping memories during reflection
        self.overlap_reflect_th = 2
        # Keyword strength threshold to trigger reflection on events
        self.kw_strg_event_reflect_th = 4
        # Keyword strength threshold to trigger reflection on thoughts
        self.kw_strg_thought_reflect_th = 4

        # ---- Group 5: Retrieval Weights ----
        # These control how memories are scored during retrieval.
        # The formula: score = recency_w×recency + relevance_w×relevance + importance_w×importance
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1
        # Decay factor: 0.99^age — memories lose 1% relevance per step
        self.recency_decay = 0.99

        # ---- Group 6: Reflection Trigger ----
        # Counter: accumulates poignancy (importance) of perceived events.
        # When it hits 0, the agent reflects.
        # Starts at 150, decreases as events are perceived.
        self.importance_trigger_max = 150
        self.importance_trigger_curr = self.importance_trigger_max
        # Number of events accumulated since last reflection
        self.importance_ele_n = 0
        # How many thoughts to generate per reflection
        self.thought_count = 5

        # ---- Group 7: Daily Planning ----
        # Raw daily plan requirements (text from LLM)
        self.daily_req = []
        # Processed schedule: list of (task_description, duration_minutes) tuples
        # Example: [("wake up and morning routine", 60), ("breakfast", 30), ...]
        self.f_daily_schedule = []
        # Original hourly schedule (backup copy)
        self.f_daily_schedule_hourly_org = []
        # When the schedule was generated (used to calculate current task index)
        self.schedule_start_time = None

        # ---- Group 8: Current Action State ----
        # What the agent is doing RIGHT NOW. Updated each step.
        self.act_address = None       # Location path (e.g., "the Ville:Hobbs Cafe:counter")
        self.act_start_time = None    # When this action started
        self.act_duration = None      # How long it lasts (in minutes)
        self.act_description = None   # What they're doing (e.g., "serving coffee")
        self.act_pronunciatio = None  # Emoji representation (e.g., "☕")
        # The action as an SPO triple: (subject, predicate, object)
        self.act_event = (self.name, None, None)

        # Object interaction (if the agent is using an object)
        self.act_obj_description = None   # What object they're using
        self.act_obj_pronunciatio = None  # Emoji for the object
        self.act_obj_event = (self.name, None, None)  # SPO triple for object interaction

        # ---- Group 9: Chat State ----
        # If the agent is talking to someone, these fields track the conversation.
        self.chatting_with = None          # Name of the other agent
        self.chat = None                   # The conversation text
        self.chatting_with_buffer = {}     # Buffer for multi-turn conversations
        self.chatting_end_time = None      # When the chat ends
        # Conversation system fields
        self.chat_type = None              # "small_talk" or "deep_talk"
        self.chat_rounds_left = 0          # Rounds remaining in current conversation
        self.chat_total_rounds = 0         # Total rounds for this conversation
        self.chat_history = []             # List of {"from": name, "msg": text}
        self.chat_cooldown_until = None    # Datetime when this agent can chat again
        self.last_chat_with = {}           # {name: datetime} — per-pair cooldown

        # ---- Group 10: Pathfinding ----
        self.act_path_set = False    # Has the path been calculated?
        self.planned_path = []       # List of (x, y) tiles to walk through

    def load_from_dict(self, d):
        """
        Load identity fields from a dictionary.

        This is how we initialize an agent from a JSON config file.
        Only sets fields that exist in the Scratch class (ignores unknown keys).
        """
        for key, val in d.items():
            if hasattr(self, key):
                setattr(self, key, val)

    def load_from_file(self, filepath):
        """Load agent state from a JSON file."""
        with open(filepath, 'r') as f:
            d = json.load(f)
        self.load_from_dict(d)

    def add_new_action(self, action_address, action_duration, action_description,
                       action_pronunciatio, action_event,
                       chatting_with, chat, chatting_with_buffer, chatting_end_time,
                       act_obj_description, act_obj_pronunciatio, act_obj_event,
                       act_start_time=None):
        """
        Set a new action for the agent to perform.

        This is called when the planning system decides what the agent should do next.
        Example: add_new_action(
            action_address="the Ville:Hobbs Cafe:counter",
            action_duration=60,
            action_description="serving coffee",
            action_pronunciatio="☕",
            action_event=("Isabella", "is", "serving coffee"),
            ...
        )
        """
        self.act_address = action_address
        self.act_duration = action_duration
        self.act_description = action_description
        self.act_pronunciatio = action_pronunciatio
        self.act_event = action_event
        self.chatting_with = chatting_with
        self.chat = chat
        if chatting_with_buffer:
            self.chatting_with_buffer.update(chatting_with_buffer)
        self.chatting_end_time = chatting_end_time
        self.act_obj_description = act_obj_description
        self.act_obj_pronunciatio = act_obj_pronunciatio
        self.act_obj_event = act_obj_event
        self.act_start_time = self.curr_time  # action starts "now"
        self.act_path_set = False  # path needs recalculation

    def act_check_finished(self):
        """
        Check if the current action is complete.

        Returns True if:
        - No action is set (act_address is None)
        - Current time >= start_time + duration

        The time comparison aligns to the minute boundary:
        if start is 8:00:30 and duration is 1 minute, end time is 8:02:00
        (rounds up to next minute, then adds duration).
        """
        if not self.act_address:
            return True

        # Calculate end time
        if self.chatting_with:
            # If chatting, use the chat end time
            end_time = self.chatting_end_time
        else:
            # Align start time to minute boundary
            x = self.act_start_time
            if x.second != 0:
                x = x.replace(second=0)
                x = x + datetime.timedelta(minutes=1)
            end_time = x + datetime.timedelta(minutes=self.act_duration)

        # Compare times — use >= so we don't miss the exact moment
        if self.curr_time >= end_time:
            return True
        return False

    def get_str_iss(self):
        """
        Generate an "Identity Summary String" (ISS) for use in LLM prompts.

        This gives the LLM context about WHO the agent is, so it can generate
        responses that match the agent's personality.

        Example output:
            "Name: Isabella Rodriguez
             Age: 34
             Innate traits: friendly, outgoing, hospitable
             Learned traits: Isabella is a cafe owner.
             Currently: Planning a Valentine's Day party.
             Lifestyle: Goes to bed around 11pm, wakes up around 6am.
             Daily plan requirement: Open Hobbs Cafe at 8am, work until 8pm.
             Current Date: Friday May 23"
        """
        commonset = ""
        commonset += f"Name: {self.name}\n"
        commonset += f"Age: {self.age}\n"
        commonset += f"Innate traits: {self.innate}\n"
        commonset += f"Learned traits: {self.learned}\n"
        commonset += f"Currently: {self.currently}\n"
        commonset += f"Lifestyle: {self.lifestyle}\n"
        commonset += f"Daily plan requirement: {self.daily_plan_req}\n"
        if self.curr_time:
            commonset += f"Current Date: {self.curr_time.strftime('%A %B %d')}\n"
        return commonset

    def get_f_daily_schedule_index(self, advance=0):
        """
        Figure out which task in the daily schedule the agent should be doing NOW.

        Walks through f_daily_schedule, accumulating durations until we pass
        the elapsed time since the schedule started. Returns the index of the current task.

        Example: schedule = [("breakfast", 30), ("work", 120), ("lunch", 60)]
        If schedule started at 08:00 and current time is 09:00 → 60 min elapsed
        breakfast (30min) + work (120min) = 150min
        60 < 150, so we're in "work" → returns index 1.
        """
        if not self.curr_time or not self.f_daily_schedule:
            return 0

        # Calculate elapsed time since schedule started
        if self.schedule_start_time:
            elapsed_delta = self.curr_time - self.schedule_start_time
            min_elapsed = int(elapsed_delta.total_seconds() / 60) + advance
        else:
            # Fallback: use time since midnight (old behavior)
            min_elapsed = self.curr_time.hour * 60 + self.curr_time.minute + advance

        curr_index = 0
        accumulated = 0
        for task, duration in self.f_daily_schedule:
            accumulated += duration
            if accumulated > min_elapsed:
                return curr_index
            curr_index += 1
        return curr_index

    def save(self, filepath):
        """Save current state to a JSON file."""
        d = {
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "age": self.age,
            "innate": self.innate,
            "learned": self.learned,
            "currently": self.currently,
            "lifestyle": self.lifestyle,
            "living_area": self.living_area,
            "curr_tile": self.curr_tile,
            "daily_plan_req": self.daily_plan_req,
            "act_address": self.act_address,
            "act_start_time": self.act_start_time.strftime("%B %d, %Y, %H:%M:%S") if self.act_start_time else None,
            "act_duration": self.act_duration,
            "act_description": self.act_description,
            "act_pronunciatio": self.act_pronunciatio,
            "act_event": list(self.act_event) if self.act_event else None,
        }
        with open(filepath, 'w') as f:
            json.dump(d, f, indent=2)
