"""
Reflect Module — Generate Insights from Accumulated Memories
=============================================================
The fourth step of the cognitive loop:
    Perceive → Retrieve → Plan → REFLECT → Execute

What is "reflection"?
    After accumulating enough experiences (importance counter hits 150),
    the agent pauses to think about what it has learned.
    It generates higher-level insights from lower-level memories.

    Example:
    - Level 0 (event): "Isabella cooked breakfast alone"
    - Level 0 (event): "Isabella cooked dinner alone"
    - Level 0 (event): "Isabella ate lunch alone"
    - Level 1 (thought): "I notice I've been eating alone a lot lately"

When does reflection trigger?
    Every perceived event has a "poignancy" (importance 1-10).
    These accumulate in a counter (starts at 150).
    When the counter hits 0, the agent reflects.
    After reflecting, the counter resets to 150.

    This means:
    - 150 low-importance events (poignancy 1) → reflect after 150 events
    - 15 high-importance events (poignancy 10) → reflect after 15 events

How does reflection work?
    1. Generate 3 "focal points" — questions about recent experiences
    2. Retrieve relevant memories for each focal point
    3. Generate insights from those memories (up to 5 per focal point)
    4. Store insights as "thought" nodes in associative memory

Connection to the paper:
    Section 4.3 — "When the importance score accumulates to a threshold,
    the agent reflects on its memories and generates higher-level insights."
"""
import datetime
from config import IMPORTANCE_TRIGGER_MAX


def generate_focal_points(persona, llm_client, n=3):
    """
    Generate N questions that the agent should reflect on.

    The LLM looks at recent memories and asks "what are the most important
    things I should think about?"

    Example output:
    - "What have I been eating lately?"
    - "How are my relationships with other agents?"
    - "Am I making progress on my goals?"

    Args:
        persona: the agent
        llm_client: API client for generating text
        n: how many focal points to generate (default 3)

    Returns:
        List of question strings, or empty list if no memories exist
    """
    # Gather recent memories (events + thoughts), excluding idle actions
    nodes = [(i.last_accessed, i) for i in persona.a_mem.seq_event + persona.a_mem.seq_thought
             if "idle" not in i.embedding_key]
    nodes.sort(key=lambda x: x[0])  # oldest first
    nodes = [i for _, i in nodes]

    # Build a summary of recent memories for the LLM prompt
    statements = ""
    for node in nodes[-1 * persona.scratch.importance_ele_n:]:
        statements += node.embedding_key + "\n"

    # If no memories to reflect on, skip
    if not statements.strip():
        return []

    # Ask the LLM to generate questions about the memories
    prompt = f"""{persona.scratch.get_str_iss()}
What are the {n} most salient high-level questions we can answer about the subjects in the statements?

Statements:
{statements}

Output {n} questions, one per line."""

    response = llm_client.generate(prompt)
    # Parse response: one question per line
    focal_points = [line.strip() for line in response.strip().split("\n") if line.strip()]
    return focal_points[:n]


def generate_insights_and_evidence(persona, nodes, llm_client, n=5):
    """
    Given a set of memories, ask the LLM to generate insights.

    Each insight is a higher-level conclusion drawn from the memories.
    The LLM also identifies which memories support each insight.

    Example:
    Input memories:
    0. "Isabella cooked breakfast alone"
    1. "Isabella ate lunch alone"
    2. "Isabella cooked dinner alone"

    Output insights:
    "I've been eating alone frequently [0, 1, 2]"
    "I should invite someone to eat with me [1, 2]"

    Args:
        persona: the agent
        nodes: list of ConceptNodes to generate insights from
        llm_client: API client for generating text
        n: max number of insights to generate (default 5)

    Returns:
        Dict of {insight_text: [evidence_node_ids]}
    """
    # Number each memory for the LLM to reference
    statements = ""
    for count, node in enumerate(nodes):
        statements += f"{count}. {node.embedding_key}\n"

    # Ask the LLM for insights
    prompt = f"""{persona.scratch.get_str_iss()}
What {n} high-level insights can you infer from the above statements?

Statements:
{statements}

For each insight, provide the statement numbers that support it.
Output format: one insight per line, followed by supporting numbers in brackets.
Example: "Insight text [1, 3]" """

    response = llm_client.generate(prompt)

    # Parse the response
    insights = {}
    for line in response.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        # Parse "insight [evidence_ids]" format
        if "[" in line and "]" in line:
            insight_text = line[:line.rfind("[")].strip()
            evidence_str = line[line.rfind("[") + 1:line.rfind("]")]
            try:
                evidence_ids = [int(x.strip()) for x in evidence_str.split(",")]
                evidence_node_ids = [nodes[i].node_id for i in evidence_ids if i < len(nodes)]
                insights[insight_text] = evidence_node_ids
            except:
                insights[insight_text] = []
        else:
            insights[line] = []
    return insights


def reflection_trigger(persona):
    """
    Check if the agent should reflect now.

    Returns True when:
    - The importance counter has hit 0 (accumulated enough experiences)
    - There are memories to reflect on

    The counter starts at 150 (IMPORTANCE_TRIGGER_MAX) and decreases
    by the poignancy of each perceived event. So high-importance events
    trigger reflection faster.
    """
    if (persona.scratch.importance_trigger_curr <= 0 and
            [] != persona.a_mem.seq_event + persona.a_mem.seq_thought):
        return True
    return False


def reset_reflection_counter(persona):
    """
    Reset the importance counter after reflecting.

    Sets the counter back to 150 and resets the event count.
    This means the agent needs to accumulate 150 more importance
    points before the next reflection.
    """
    persona.scratch.importance_trigger_curr = persona.scratch.importance_trigger_max
    persona.scratch.importance_ele_n = 0


def run_reflect(persona, llm_client):
    """
    Execute the full reflection process.

    Steps:
    1. Generate 3 focal points (questions about recent experiences)
    2. For each focal point, retrieve relevant memories
    3. Generate insights from those memories
    4. Store each insight as a "thought" node in associative memory

    Each thought node has:
    - depth: 1+ (reflection is one level deeper than direct perception)
    - poignancy: 7 (insights are moderately important)
    - expiration: 30 days (thoughts fade over time)
    - filling: the evidence node IDs that support this insight
    """
    # Step 1: Generate focal points
    focal_points = generate_focal_points(persona, llm_client, 3)
    if not focal_points:
        return

    # Step 2: Retrieve memories for each focal point
    from agent.cognitive.retrieve import new_retrieve
    retrieved = new_retrieve(persona, focal_points, llm_client)

    # Step 3: Generate insights and store them
    for focal_pt, nodes in retrieved.items():
        thoughts = generate_insights_and_evidence(persona, nodes, llm_client, 5)
        for thought, evidence in thoughts.items():
            # Create a thought node
            created = persona.scratch.curr_time
            expiration = persona.scratch.curr_time + datetime.timedelta(days=30)
            keywords = set(thought.lower().split()[:5])
            thought_embedding = llm_client.get_embedding(thought)

            # Store in associative memory
            persona.a_mem.add_thought(
                created, expiration,
                persona.name, "reflects", "on",
                thought, keywords, 7,
                thought, thought_embedding, evidence
            )


def reflect(persona, llm_client):
    """
    Main entry point — check if reflection should happen, and if so, run it.

    Called during each step of the cognitive loop.
    Only does work when the importance counter hits 0.
    """
    if reflection_trigger(persona):
        run_reflect(persona, llm_client)
        reset_reflection_counter(persona)
