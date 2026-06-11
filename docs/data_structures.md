# Data Structures Reference

All data structures in AI Town, with realistic example content.

---

## 1. ConceptNode

A single memory entry. Stored in `AssociativeMemory`.

```
node_id:        "node_1"
node_count:     1                    # global counter across all nodes
type_count:     1                    # counter within this type (1st event)
type:           "event"              # "event" | "thought" | "chat"
depth:          0                    # 0=perceived, 1=first reflection, 2=reflection on reflection...
created:        datetime(2026, 5, 23, 8, 0, 0)
expiration:     None                 # None = never forget; thoughts expire in 30 days
last_accessed:  datetime(2026, 5, 23, 8, 0, 0)  # updated each time retrieved
subject:        "Isabella"
predicate:      "is"
object:         "cooking"
description:    "Isabella is cooking breakfast in the cafe kitchen"
embedding_key:  "Isabella is cooking breakfast in the cafe kitchen"  # text used for embedding
poignancy:      5                    # importance 1-10 (assigned by LLM)
keywords:       {"isabella", "cooking", "breakfast", "cafe", "kitchen"}
filling:        []                   # evidence node_ids (empty for events, populated for thoughts)
```

**Thought node example (depth=1):**
```
node_id:        "node_15"
type:           "thought"
depth:          1                    # one level deeper than events
subject:        "Isabella"
predicate:      "reflects"
object:         "on"
description:    "I notice I've been cooking alone a lot lately"
embedding_key:  "I notice I've been cooking alone a lot lately"
poignancy:      7                    # thoughts are moderately important
filling:        ["node_1", "node_3", "node_7"]  # evidence: which events support this insight
```

**Chat node example (depth=0):**
```
node_id:        "node_20"
type:           "chat"
depth:          0
subject:        "Isabella"
predicate:      "talked to"
object:         "Maria"
description:    "Isabella talked to Maria about the Valentine's Day party"
embedding_key:  "Isabella talked to Maria about the Valentine's Day party"
poignancy:      4
filling:        []
```

---

## 2. AssociativeMemory

The agent's long-term memory. Contains three sequences and lookup indexes.

```
AssociativeMemory:
  id_to_node:           {"node_1": ConceptNode, "node_2": ConceptNode, ...}  # master lookup
  seq_event:            [ConceptNode, ConceptNode, ...]   # newest first
  seq_thought:          [ConceptNode, ConceptNode, ...]   # newest first
  seq_chat:             [ConceptNode, ConceptNode, ...]   # newest first

  kw_to_event:          {"isabella": [node_1, node_3], "cooking": [node_1], ...}
  kw_to_thought:        {"cooking": [node_15], "alone": [node_15], ...}
  kw_to_chat:           {"maria": [node_20], ...}

  kw_strength_event:    {"isabella": 12, "cooking": 5, "maria": 3, ...}
  kw_strength_thought:  {"cooking": 2, "alone": 1, ...}

  embeddings:           {"Isabella is cooking breakfast": [0.12, -0.34, 0.56, ...], ...}
```

**Key relationships:**
- `id_to_node` is the master dict; `seq_*` lists and `kw_to_*` dicts reference the same node objects
- `kw_strength_*` counts how many times each keyword appeared (used for reflection triggers)
- `embeddings` caches vectors by `embedding_key` text (1024-dimensional floats)

---

## 3. Event Dict (perceive output)

What `perceive()` returns before storing in memory. Caller must convert to ConceptNode.

```
{
    "subject":      "Maria",
    "predicate":    "is",
    "object":       "painting",
    "description":  "Maria is painting in the studio",
    "created":      datetime(2026, 5, 23, 10, 30, 0),
    "poignancy":    2                    # observed actions are low importance
}
```

---

## 4. Insight Dict (reflect output)

What `generate_insights_and_evidence()` returns. Keys are insight text, values are evidence node_ids.

```
{
    "Isabella has been cooking alone frequently":  ["node_1", "node_3", "node_7"],
    "She might enjoy company while cooking":       ["node_1", "node_3"],
    "Cooking is a core part of her identity":      ["node_1"]
}
```

---

## 5. Retrieved Memories (retrieve output)

What `new_retrieve()` returns. Maps focal points to ranked ConceptNodes.

```
{
    "cooking breakfast": [ConceptNode_1, ConceptNode_5, ConceptNode_3, ...],  # ranked by score
    "social relationships": [ConceptNode_20, ConceptNode_12, ...]
}
```

Each node's `last_accessed` is updated to current time after retrieval.

---

## 6. Scratch (Working Memory)

The agent's "active consciousness" — current state, identity, planning.

```
Scratch:
  # --- Perception ---
  vision_r:               4              # see 4 tiles in each direction
  att_bandwidth:          3              # max events to pay attention to
  retention:              5              # recent events for dedup

  # --- Time & Position ---
  curr_time:              datetime(2026, 5, 23, 10, 30, 0)
  curr_tile:              (12, 8)        # (x, y) on the grid
  daily_plan_req:         "Open cafe at 8am, work until 8pm"

  # --- Identity ---
  name:                   "Isabella Rodriguez"
  first_name:             "Isabella"
  last_name:              "Rodriguez"
  age:                    34
  innate:                 "friendly, outgoing, hospitable"
  learned:                "Isabella is a cafe owner."
  currently:              "Planning a Valentine's Day party."
  lifestyle:              "Goes to bed around 11pm, wakes up around 6am."
  living_area:            "the Ville:Hobbs Cafe:bedroom"

  # --- Reflection ---
  importance_trigger_max: 150
  importance_trigger_curr: 142           # decreases as events are perceived
  importance_ele_n:       4              # events since last reflection
  thought_count:          5              # thoughts to generate per reflection

  # --- Retrieval Weights ---
  recency_w:              1
  relevance_w:            1
  importance_w:           1
  recency_decay:          0.99

  # --- Daily Planning ---
  daily_req:              ["Open cafe at 8am", "Prepare lunch menu", ...]
  f_daily_schedule:       [("morning routine", 60), ("open cafe", 120), ("lunch break", 60), ...]
  f_daily_schedule_hourly_org: [("morning routine", 60), ("open cafe", 120), ...]

  # --- Current Action ---
  act_address:            "the Ville:Hobbs Cafe:counter"
  act_start_time:         datetime(2026, 5, 23, 8, 0, 0)
  act_duration:           120            # minutes
  act_description:        "serving coffee to customers"
  act_pronunciatio:       "☕"       # ☕ emoji
  act_event:              ("Isabella", "is", "serving coffee")
  act_obj_description:    "coffee machine"
  act_obj_pronunciatio:   "☕"
  act_obj_event:          ("Isabella", "uses", "coffee machine")

  # --- Chat State ---
  chatting_with:          None           # or "Maria"
  chat:                   None           # or "Let's plan the party together"
  chatting_with_buffer:   {}
  chatting_end_time:      None

  # --- Pathfinding ---
  act_path_set:           True
  planned_path:           [(12, 8), (11, 8), (10, 8), ...]  # tiles to walk through
```

---

## 7. Schedule Tuple

Each entry in `f_daily_schedule` is a `(task_description, duration_minutes)` tuple.

```
f_daily_schedule = [
    ("wake up and morning routine", 60),
    ("walk to cafe", 15),
    ("open cafe and prepare for customers", 30),
    ("serve coffee and work", 180),
    ("lunch break", 60),
    ("afternoon cafe work", 180),
    ("close cafe and walk home", 30),
    ("dinner and relax", 120),
    ("evening reading", 60),
    ("sleep", 480),
]
```

---

## 8. SpatialMemory (Location Tree)

3-level hierarchy: world → sector → arena. Each arena has objects.

```
SpatialMemory:
  tree = {
      "the Ville": {
          "Hobbs Cafe": {
              "counter":   ["coffee machine", "register", "menu board"],
              "kitchen":   ["stove", "oven", "fridge", "sink"],
              "seating":   ["table 1", "table 2", "chair", "window seat"],
              "bedroom":   ["bed", "desk", "lamp"],
          },
          "the Park": {
              "bench area": ["bench", "fountain"],
              "garden":     ["flowers", "tree", "path"],
          },
          "the Library": {
              "reading room": ["bookshelf", "desk", "chair"],
              "lobby":        ["front desk", "newspaper stand"],
          },
      }
  }
```

---

## 9. LLM Client

API wrapper for text generation and embeddings.

```
LLMClient:
  providers = [
      {
          "name": "SiliconFlow",
          "base_url": "https://api.siliconflow.cn/v1",
          "api_key": "sk-...",
          "chat_models": ["inclusionAI/Ling-flash-2.0"],
          "embedding_models": [("Qwen/Qwen3-Embedding-8B", 1024)],
      },
      {
          "name": "DashScope",
          "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
          "api_key": "sk-...",
          "chat_models": ["qwen3.6-flash", "qwen-flash-character-2026-02-26"],
          "embedding_models": [],
      },
  ]
  current_provider: 0    # index into providers list
```

**Methods:**
- `generate(prompt) → str` — text generation with fallback on 403
- `get_embedding(text) → list[float]` — 1024-dim vector, no fallback

---

## 10. Config (config.py)

```
API_PROVIDERS:          [see LLM Client above]
EMBEDDING_DIM:          1024
PROJECT_ROOT:           "/home/hefeng/pythonProject/ccTest/AITown"
ASSETS_DIR:             ".../assets"
MAP_MATRIX_DIR:         ".../assets/the_ville/matrix"
MAP_VISUALS_DIR:        ".../assets/the_ville/visuals"
CHARACTERS_DIR:         ".../assets/characters"
DATA_DIR:               ".../data"
PERSONAS_DIR:           ".../data/personas"
SIMULATIONS_DIR:        ".../data/simulations"

TILE_SIZE:              32         # pixels per tile
MAP_WIDTH:              140        # tiles
MAP_HEIGHT:             100        # tiles
STEP_DURATION_SECONDS:  10         # game seconds per simulation step

VISION_RADIUS:          4
ATT_BANDWIDTH:          3
RETENTION:              5
RECENCY_DECAY:          0.99
RECENCY_W:              1
RELEVANCE_W:            1
IMPORTANCE_W:           1
RETRIEVAL_WEIGHTS:      [0.5, 3, 2]  # [recency, relevance, importance]
IMPORTANCE_TRIGGER_MAX: 150
```
