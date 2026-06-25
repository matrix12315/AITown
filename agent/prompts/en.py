"""
English Prompt Templates
=========================
All LLM prompts used by cognitive modules, in English.

Variables (use .format() to fill in):
    {identity}    — agent's identity string from scratch.get_str_iss()
    {locations}   — newline-separated list of known locations
    {task_desc}   — current task description from daily schedule
    {current_location} — agent's current act_address
    {current_time} — formatted time string (HH:MM)
    {statements}  — newline-separated memory statements
    {n}           — number of items to generate
"""

# System prompt sent with every LLM request (role: "system")
SYSTEM_PROMPT = (
    "You are a character in a small-town simulation called the Ville. "
    "Stay in character. Respond only with the requested output format, "
    "no extra commentary."
)

# =============================================================================
# Plan Module Prompts
# =============================================================================

DAILY_SCHEDULE = """{identity}
Create a daily schedule for today. Each task should have a duration in minutes.
The total must add up to exactly 24 hours (1440 minutes) to cover the full day.
Include sleep as the last task.

Available locations in the world:
{locations}

Output format: one task per line, as "task description (X minutes)"
Example:
wake up and morning routine (60)
walk to cafe (15)
serve coffee to customers (180)
lunch break (60)
afternoon cafe work (180)
close cafe and walk home (30)
dinner and relax (120)
evening reading (60)
sleep (480)"""


ACTION_DETAIL = """{identity}
Current task: {task_desc}
Current location: {current_location}
Current time: {current_time}

Available locations (you MUST pick one of these for the address):
{locations}

Generate the action details for this task. Output exactly these fields, one per line.
For pronunciatio, use a single Unicode emoji character (not :shortcodes:).

Example output:
address: the Ville:Hobbs Cafe:cafe
description: serving coffee to customers
pronunciatio: ☕
object_description: coffee machine
object_pronunciatio: ☕"""


# =============================================================================
# Reflect Module Prompts
# =============================================================================

FOCAL_POINTS = """{identity}
I am reflecting on my recent experiences. Based on the statements below,
what are the {n} most important questions I should think about?
Focus on patterns, relationships, goals, and feelings — not surface details.

Statements:
{statements}

Output {n} questions, one per line.
Example:
What have I been eating lately?
How are my relationships with other agents?
Am I making progress on my goals?"""


INSIGHTS = """{identity}
I am reflecting on my experiences. Based on the statements below,
what {n} patterns or conclusions can I draw?

Statements:
{statements}

For each insight, provide the statement numbers that support it.
Output format: one insight per line, followed by supporting numbers in brackets.
Example:
I've been eating alone frequently [0, 1, 2]
I should invite someone to eat with me [1, 2]"""
