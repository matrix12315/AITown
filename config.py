import os

# SiliconFlow API
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_CHAT_MODEL = os.environ.get("SILICONFLOW_CHAT_MODEL", "Qwen/Qwen2.5-7B-Instruct")
SILICONFLOW_EMBEDDING_MODEL = os.environ.get("SILICONFLOW_EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
MAP_MATRIX_DIR = os.path.join(ASSETS_DIR, "the_ville", "matrix")
MAP_VISUALS_DIR = os.path.join(ASSETS_DIR, "the_ville", "visuals")
CHARACTERS_DIR = os.path.join(ASSETS_DIR, "characters")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PERSONAS_DIR = os.path.join(DATA_DIR, "personas")
SIMULATIONS_DIR = os.path.join(DATA_DIR, "simulations")

# Simulation
TILE_SIZE = 32
MAP_WIDTH = 140
MAP_HEIGHT = 100
STEP_DURATION_SECONDS = 10

# Agent hyperparameters
VISION_RADIUS = 4
ATT_BANDWIDTH = 3
RETENTION = 5
RECENCY_DECAY = 0.99
IMPORTANCE_TRIGGER_MAX = 150
RECENCY_W = 1
RELEVANCE_W = 1
IMPORTANCE_W = 1
RETRIEVAL_WEIGHTS = [0.5, 3, 2]
