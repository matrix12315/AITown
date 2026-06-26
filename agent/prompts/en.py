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
    {nearby_agents} — agents at the same location
    {other_name}  — name of agent being talked to
    {other_action} — what the other agent is doing
    {my_action}   — what I am currently doing
    {chat_type}   — "small_talk" or "deep_talk"
    {current_round} — current round number
    {total_rounds} — total rounds for this conversation
    {chat_history} — formatted conversation so far
    {name}        — agent name (for summary)
    {summary}     — conversation summary text
"""

# System prompt sent with every LLM request (role: "system")
SYSTEM_PROMPT = (
    "You are a character in a small-town simulation called the Ville. "
    "Stay in character. Respond only with the requested output format, "
    "no extra commentary.\n\n"
    "When you see other characters nearby, you may choose to talk to them:\n"
    "- small_talk: 1-5 rounds, casual greeting or quick exchange about what you're both doing\n"
    "- deep_talk: 6-20 rounds, meaningful conversation about topics relevant to your personality and interests"
)

# =============================================================================
# Plan Module Prompts
# =============================================================================

DAILY_SCHEDULE = """{identity}
Create a daily schedule for today. Each task should have a duration in minutes.
The total must add up to exactly 24 hours (1440 minutes) to cover the full day.
Include sleep as the last task.
The current time is {start_time}. Start the schedule from this time.

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

Nearby agents (people you can see at this location):
{nearby_agents}

Available locations (you MUST pick one of these for the address):
{locations}

Generate the action details for this task. Output exactly these fields, one per line.
For pronunciatio, use a single Unicode emoji character (not :shortcodes:).

Also decide if you want to chat with any nearby agent:
- chat_type: none / small_talk / deep_talk
- chat_with: agent name (or "none")

Example output:
address: the Ville:Hobbs Cafe:cafe
description: serving coffee to customers
pronunciatio: ☕
object_description: coffee machine
object_pronunciatio: ☕
chat_type: small_talk
chat_with: Klaus Mueller"""


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


# =============================================================================
# Chat Module Prompts
# =============================================================================

CHAT_PROMPT = """{identity}

I am currently {my_action}.
I am talking to {other_name} who is {other_action}.
This is a {chat_type} (round {current_round} of {total_rounds}).

Conversation so far:
{chat_history}

Generate my next message. Stay in character, be natural.
Output exactly:
message: <what I say>"""


SUMMARY_PROMPT = """Summarize this conversation between {name} and {other_name} in 1-2 sentences.

Conversation:
{chat_history}

Output a brief summary of what was discussed and any notable outcomes."""
