"""
AI Town Configuration
=====================
This file contains all the settings for the simulation.
Think of it as the "control panel" — change values here to adjust behavior
without touching any other code.

Sections:
1. API Settings — how to connect to the LLM (SiliconFlow)
2. File Paths — where to find map data, character images, etc.
3. Simulation Settings — map size, time speed
4. Agent Hyperparameters — memory, reflection, retrieval tuning
"""
import os
import csv

# =============================================================================
# SECTION 1: API Provider Settings
# =============================================================================
# We use LLM APIs to:
#   1. Generate text (plans, reflections, conversations) — called "chat"
#   2. Convert text into vectors for similarity search — called "embedding"
#
# Two providers are configured with automatic fallback:
#   - SiliconFlow (primary): cheaper, supports Chinese models
#   - DashScope / Alibaba (fallback): chat only, no embedding fallback
#
# Why no embedding fallback?
#   Different embedding models produce different vector spaces.
#   Cosine similarity only works within the same model.
#   So we use ONE embedding model (Qwen3-Embedding-8B, 1024 dims).
#
# Each provider has:
#   - name: for logging
#   - base_url: API endpoint (OpenAI-compatible format)
#   - api_key: authentication secret
#   - chat_models: ordered list of models to try for text generation
#   - embedding_models: list of (model_name, dimension) tuples

API_PROVIDERS = [
    {
        "name": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "api_key": os.environ.get("SILICONFLOW_API_KEY", ""),
        "chat_models": ["inclusionAI/Ling-flash-2.0"],
        "embedding_models": [("Qwen/Qwen3-Embedding-8B", 1024)],
    },
    {
        "name": "DashScope",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": os.environ.get("DASHSCOPE_API_KEY", ""),
        "chat_models": [
            "qwen3.6-flash",
            "qwen-flash-character-2026-02-26",
            "qwen3.6-flash-2026-04-16",
        ],
        "embedding_models": [],  # No fallback — incompatible vector spaces
    },
]

# Embedding dimension: must match across all embedding models for cosine similarity
# Qwen3-Embedding-8B supports 32-4096; 1024 chosen for balance of speed and quality
EMBEDDING_DIM = 1024

# =============================================================================
# SECTION 2: File Paths
# =============================================================================
# The map data and character images come from the original Generative Agents project.
# We copied them into our project's "assets/" folder.

# Root directory of this project (where config.py lives)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Assets: contains map tiles, character sprites, collision matrices
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

# Map matrix: CSV files defining the grid (collision blocks, sectors, arenas)
# The original project stores map data as CSV grids — each cell has an ID
MAP_MATRIX_DIR = os.path.join(ASSETS_DIR, "the_ville", "matrix")

# Map visuals: tile images for rendering the map
MAP_VISUALS_DIR = os.path.join(ASSETS_DIR, "the_ville", "visuals")

# Character images: PNG sprites for each agent (Isabella, Maria, Klaus, etc.)
CHARACTERS_DIR = os.path.join(ASSETS_DIR, "characters")

# Data directory: agent definitions and simulation recordings
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PERSONAS_DIR = os.path.join(DATA_DIR, "personas")       # Agent config files (JSON)
SIMULATIONS_DIR = os.path.join(DATA_DIR, "simulations")  # Saved simulation recordings

# =============================================================================
# SECTION 3: Simulation Settings
# =============================================================================
# The map is a grid. Each cell is a 32x32 pixel tile.
# Total map: 140 tiles wide × 100 tiles tall = 14,000 tiles

TILE_SIZE = 32             # Each tile is 32×32 pixels
MAP_WIDTH = 140            # Map is 140 tiles wide
MAP_HEIGHT = 100           # Map is 100 tiles tall
STEP_DURATION_SECONDS = 10 # Each simulation step = 10 seconds of game time

# =============================================================================
# SECTION 4: Agent Hyperparameters
# =============================================================================
# These control how agents perceive, remember, and reflect.
# Tune these to change agent behavior.

# PERCEPTION: how far an agent can "see"
VISION_RADIUS = 4          # Can see 4 tiles in each direction (8×8 area)
ATT_BANDWIDTH = 3          # Max number of events to pay attention to at once
RETENTION = 5              # How many recent events to remember (for deduplication)

# MEMORY RETRIEVAL: how memories are scored when searching
# Score = recency_w × recency + relevance_w × relevance + importance_w × importance
RECENCY_DECAY = 0.99       # Memories lose 1% relevance per step (exponential decay)
                           # Formula: 0.99^i where i is the memory's age in steps
RECENCY_W = 1              # Weight for "how recent" factor
RELEVANCE_W = 1            # Weight for "how relevant" factor (cosine similarity)
IMPORTANCE_W = 1           # Weight for "how important" factor (poignancy score)

# Global weights for the three factors [recency, relevance, importance]
# Higher number = more influence on the final score
RETRIEVAL_WEIGHTS = [0.5, 3, 2]  # Relevance matters most (3), then importance (2), recency (0.5)

# REFLECTION: when should an agent "reflect" on their experiences?
# A counter starts at 150 and decreases by each event's poignancy (1-10).
# When the counter hits 0, the agent pauses to reflect and generate insights.
# After reflecting, the counter resets to 150.
# Example: 15 events with poignancy 10 → reflect after 15 events.
IMPORTANCE_TRIGGER_MAX = 150  # Counter starts here; reflects when it hits 0

# =============================================================================
# SECTION 5: World Map Locations
# =============================================================================
# Complete list of all locations in the Ville, loaded from arena_blocks.csv.
# Format: "world:sector:arena" (e.g., "the Ville:Hobbs Cafe:cafe")
# Used in planning prompts so the LLM knows where agents can go.

def _load_map_locations():
    """Load all location paths from the arena_blocks CSV file."""
    locations = []
    csv_path = os.path.join(ASSETS_DIR, "the_ville", "matrix", "special_blocks", "arena_blocks.csv")
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4:
                # CSV format: id, world, sector, arena
                loc = f"{row[1].strip()}:{row[2].strip()}:{row[3].strip()}"
                locations.append(loc)
    return sorted(set(locations))

MAP_LOCATIONS = _load_map_locations()
