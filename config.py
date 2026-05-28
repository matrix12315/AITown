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

# =============================================================================
# SECTION 1: SiliconFlow API Settings
# =============================================================================
# SiliconFlow is an OpenAI-compatible API service (cheaper, supports Chinese models).
# We use two models:
#   - Chat model (Qwen2.5-7B): generates text responses (planning, reflection, conversation)
#   - Embedding model (bge-large-zh): converts text into a vector (list of numbers)
#     for similarity search. Similar meanings → similar vectors.

# API key: set via environment variable or use default
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "sk-bdjyqopyqxjtayqgjfootthqvxmsayqhbuxegeywvhwzysoo")

# Base URL for all API calls (OpenAI-compatible format)
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

# Chat model: used for generating plans, reflections, conversations
SILICONFLOW_CHAT_MODEL = os.environ.get("SILICONFLOW_CHAT_MODEL", "inclusionAI/Ling-flash-2.0")

# Embedding model: converts text into a vector of numbers for similarity comparison
# Example: "cooking breakfast" → [0.12, -0.34, 0.56, ...] (1024 numbers)
SILICONFLOW_EMBEDDING_MODEL = os.environ.get("SILICONFLOW_EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-8B")
EMBEDDING_DIM = 1024  # Must match across all embedding models for cosine similarity

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
# Every time an agent perceives an event, its poignancy (1-10) is added to a counter.
# When the counter hits 150, the agent pauses to reflect and generate insights.
IMPORTANCE_TRIGGER_MAX = 150  # Reflect after accumulating 150 importance points
