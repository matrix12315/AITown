"""
Retrieve Module — Memory Search and Scoring
============================================
When an agent needs to remember something (e.g., "what do I know about cooking?"),
this module searches through ALL memories and returns the most relevant ones.

The retrieval process:
1. Take a "focal point" (a question or topic, e.g., "Isabella is cooking breakfast")
2. Score every memory on three dimensions:
   - Recency:   how recently was this memory created? (newer = higher score)
   - Relevance: how similar is this memory to the query? (cosine similarity)
   - Importance: how important was this event? (poignancy score 1-10)
3. Combine scores: final = recency×0.5 + relevance×3 + importance×2
4. Return the top 30 memories

This is the core of the "retrieval" step in the cognitive loop:
    Perceive → RETRIEVE → Plan → Reflect → Execute

Why cosine similarity?
    Embedding vectors capture meaning. Two texts with similar meanings
    produce vectors pointing in similar directions.
    Cosine similarity measures the angle between vectors:
    - 1.0 = same direction (identical meaning)
    - 0.0 = perpendicular (unrelated)
    - -1.0 = opposite direction (opposite meaning)
"""
import math
from numpy import dot
from numpy.linalg import norm


def cos_sim(a, b):
    """
    Calculate cosine similarity between two vectors.

    Formula: cos(θ) = (a · b) / (||a|| × ||b||)

    Args:
        a: first vector (list of floats), e.g., [0.12, -0.34, 0.56, ...]
        b: second vector (list of floats)

    Returns:
        Float between -1.0 and 1.0
        1.0 = identical direction (same meaning)
        0.0 = perpendicular (unrelated)

    Example:
        cos_sim([1, 0, 0], [1, 0, 0]) → 1.0  (same direction)
        cos_sim([1, 0, 0], [0, 1, 0]) → 0.0  (perpendicular)

    The numpy functions:
        dot(a, b) = sum(a[i] * b[i]) for all i  — the dot product
        norm(a) = sqrt(sum(a[i]^2))              — the vector's length
    """
    return dot(a, b) / (norm(a) * norm(b))


def normalize_dict_floats(d, target_min, target_max):
    """
    Normalize all values in a dictionary to a target range [target_min, target_max].

    Why normalize?
        Different scoring dimensions have different scales:
        - Recency: 0.99^0 = 1.0, 0.99^100 = 0.366 (range ~0.6)
        - Importance: 1 to 10 (range 9)
        - Relevance: -1.0 to 1.0 (range 2)

        Without normalization, importance (range 9) would dominate recency (range 0.6).
        After normalization, all scores are in [0, 1] — fair comparison.

    Formula: normalized = (value - min) / (max - min) × (target_max - target_min) + target_min

    Args:
        d: dictionary of {key: float_value}
        target_min: target minimum (usually 0)
        target_max: target maximum (usually 1)

    Returns:
        The same dictionary with values normalized (modified in place)
    """
    if not d:
        return d
    min_val = min(d.values())
    max_val = max(d.values())
    range_val = max_val - min_val
    if range_val == 0:
        # All values are the same — assign midpoint
        for key in d:
            d[key] = (target_max - target_min) / 2
    else:
        for key in d:
            d[key] = (d[key] - min_val) * (target_max - target_min) / range_val + target_min
    return d


def top_highest_x_values(d, x):
    """
    Return the top X entries with highest values from a dictionary.

    Example: top_highest_x_values({"a": 5, "b": 2, "c": 8, "d": 1}, 2)
    → {"c": 8, "a": 5}

    Used to select the most relevant memories after scoring.
    """
    return dict(sorted(d.items(), key=lambda item: item[1], reverse=True)[:x])


def extract_recency(persona, nodes):
    """
    Calculate recency scores for a list of memory nodes.

    Recency uses exponential decay: 0.99^i where i is the memory's position
    in the sorted list (0 = most recent, 1 = second most recent, ...).

    Example with 3 memories (decay=0.99):
        memory at position 0 (newest): 0.99^1 = 0.99
        memory at position 1:          0.99^2 = 0.9801
        memory at position 2 (oldest): 0.99^3 = 0.9703

    Newer memories get higher scores. The decay rate (0.99) controls how
    quickly old memories lose relevance. At 0.99, a memory 100 steps old
    retains 0.99^100 ≈ 36.6% of its original recency score.

    Args:
        persona: the agent (to access scratch.recency_decay)
        nodes: list of ConceptNodes, sorted by last_accessed (oldest first)

    Returns:
        Dictionary of {node_id: recency_score}
    """
    # Generate decay values: [0.99^1, 0.99^2, 0.99^3, ...]
    recency_vals = [persona.scratch.recency_decay ** i for i in range(1, len(nodes) + 1)]
    # Map each node to its recency value
    return {node.node_id: recency_vals[count] for count, node in enumerate(nodes)}


def extract_importance(persona, nodes):
    """
    Extract importance scores from memory nodes.

    Importance is the "poignancy" score (1-10) assigned by the LLM when
    the memory was created. Higher poignancy = more important event.

    Example:
        "Isabella won an award" → poignancy 9 → high importance
        "Isabella walked to the store" → poignancy 2 → low importance

    Args:
        persona: the agent (not directly used, but kept for API consistency)
        nodes: list of ConceptNodes

    Returns:
        Dictionary of {node_id: poignancy_score}
    """
    return {node.node_id: node.poignancy for node in nodes}


def extract_relevance(persona, nodes, focal_pt, llm_client):
    """
    Calculate relevance scores using cosine similarity of embeddings.

    This is the most computationally expensive step — it requires:
    1. Getting the embedding vector for the focal point (query)
    2. Getting the embedding vector for each memory node
    3. Computing cosine similarity between each pair

    Example:
        focal_pt = "cooking breakfast"
        → embedding: [0.12, -0.34, 0.56, ...]

        memory_1 = "Isabella is making eggs"
        → embedding: [0.11, -0.32, 0.55, ...]  → cos_sim = 0.98 (very relevant)

        memory_2 = "Klaus is reading a book"
        → embedding: [-0.45, 0.67, -0.12, ...] → cos_sim = 0.15 (not relevant)

    Args:
        persona: the agent (to access cached embeddings via a_mem)
        nodes: list of ConceptNodes to score
        focal_pt: the query text (what we're searching for)
        llm_client: API client to generate embeddings for the focal point

    Returns:
        Dictionary of {node_id: relevance_score} (cosine similarity values)
    """
    # Get embedding vector for the query
    focal_embedding = llm_client.get_embedding(focal_pt)
    relevance_out = {}
    for node in nodes:
        # Get cached embedding for this memory node
        node_embedding = persona.a_mem.get_embedding(node.embedding_key)
        if node_embedding and focal_embedding:
            # Calculate cosine similarity between query and memory
            relevance_out[node.node_id] = cos_sim(node_embedding, focal_embedding)
        else:
            # No embedding available — relevance is 0
            relevance_out[node.node_id] = 0
    return relevance_out


def new_retrieve(persona, focal_points, llm_client, n_count=30):
    """
    Main retrieval function — find the most relevant memories for each focal point.

    This is called during the "Retrieve" step of the cognitive loop:
        Perceive → RETRIEVE → Plan → Reflect → Execute

    For each focal point (query topic):
    1. Gather all non-idle memories (events + thoughts)
    2. Score each on three dimensions: recency, relevance, importance
    3. Normalize scores to [0, 1] range
    4. Combine: final = recency×0.5 + relevance×3 + importance×2
    5. Return top 30 memories

    The weights [0.5, 3, 2] mean:
    - Relevance (×3) matters most — "does this memory relate to what I'm thinking about?"
    - Importance (×2) matters second — "was this a significant event?"
    - Recency (×0.5) matters least — "how fresh is this memory?"

    Args:
        persona: the agent doing the retrieval
        focal_points: list of query strings (topics to search for)
        llm_client: API client for generating embeddings
        n_count: how many memories to return per focal point (default 30)

    Returns:
        Dictionary of {focal_point: [list of ConceptNodes]}
        Each focal_point maps to its top N most relevant memories.
    """
    from config import RETRIEVAL_WEIGHTS  # [0.5, 3, 2]

    retrieved = {}
    for focal_pt in focal_points:
        # Step 1: Gather all non-idle memories (events + thoughts)
        # Filter out "idle" actions — they're not informative
        nodes = [i for i in persona.a_mem.seq_event + persona.a_mem.seq_thought
                 if "idle" not in i.embedding_key]

        # Sort by last_accessed time (oldest first) for recency calculation
        nodes.sort(key=lambda x: x.last_accessed, reverse=False)

        # Step 2: Calculate raw scores for each dimension
        recency_out = extract_recency(persona, nodes)
        importance_out = extract_importance(persona, nodes)
        relevance_out = extract_relevance(persona, nodes, focal_pt, llm_client)

        # Step 3: Normalize all scores to [0, 1] range
        # This ensures fair comparison across different scales
        recency_out = normalize_dict_floats(recency_out, 0, 1)
        importance_out = normalize_dict_floats(importance_out, 0, 1)
        relevance_out = normalize_dict_floats(relevance_out, 0, 1)

        # Step 4: Combine scores with weights
        # Formula: final = recency_w × recency × gw[0] + relevance_w × relevance × gw[1] + importance_w × importance × gw[2]
        gw = RETRIEVAL_WEIGHTS  # [0.5, 3, 2]
        master_out = {}
        for key in recency_out:
            master_out[key] = (persona.scratch.recency_w * recency_out[key] * gw[0]
                               + persona.scratch.relevance_w * relevance_out[key] * gw[1]
                               + persona.scratch.importance_w * importance_out[key] * gw[2])

        # Step 5: Select top N memories
        master_out = top_highest_x_values(master_out, n_count)
        master_nodes = [persona.a_mem.id_to_node[key] for key in master_out]

        # Step 6: Update last_accessed time for retrieved memories
        # This affects future recency calculations — recently used memories score higher
        for n in master_nodes:
            n.last_accessed = persona.scratch.curr_time

        retrieved[focal_pt] = master_nodes
    return retrieved
