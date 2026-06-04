# AI Town

A Python implementation of [Generative Agents: Interactive Simulacra of Human Behavior](https://arxiv.org/abs/2304.03442) (Stanford, 2023). Built from scratch to learn agent cognitive architecture: memory, reflection, retrieval, and planning.

## What It Does

Simulates believable human behavior through a cognitive loop:

```
Perceive → Retrieve → Plan → Reflect → Execute
```

Each agent has:
- **Spatial Memory** — a tree-structured map of the world (locations and objects)
- **Associative Memory** — a chronological "diary" of events, thoughts, and conversations
- **Scratch Memory** — current identity, action state, and daily schedule

Agents perceive their surroundings, retrieve relevant memories, make plans, reflect on experiences, and execute actions — all powered by LLM calls.

## Project Structure

```
├── agent/
│   ├── memory/
│   │   ├── spatial.py       # World location hierarchy (tree structure)
│   │   ├── associative.py   # Memory stream: events, thoughts, chats
│   │   └── scratch.py       # Working memory: identity, current state, planning
│   └── cognitive/
│       └── retrieve.py      # Memory search: cosine similarity + weighted scoring
├── llm/
│   └── client.py            # Multi-provider LLM client with fallback
├── config.py                # All settings: API providers, hyperparameters
├── tests/                   # pytest test suite (43 tests)
├── docs/                    # Test documentation
└── requirements.txt
```

## Setup

```bash
# Clone and enter the project
cd AITown

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v
```

## API Configuration

Uses [SiliconFlow](https://siliconflow.cn/) (primary) and DashScope (fallback) for LLM calls. API keys are in `config.py` or set via environment variables:

```bash
export SILICONFLOW_API_KEY="your-key"
export DASHSCOPE_API_KEY="your-key"
```

Two types of LLM calls:
- **Chat** (text generation) — plans, reflections, conversations
- **Embedding** (text → vector) — for memory similarity search

## Tests

```bash
python -m pytest tests/ -v
```

43 tests across 5 modules:

| Module | Tests | What's Covered |
|--------|-------|----------------|
| `test_spatial` | 7 | Tree loading, location lookup, path extraction |
| `test_associative` | 10 | Events, thoughts, chats, keyword indexing, save/load |
| `test_scratch` | 7 | Identity, actions, scheduling, time checks |
| `test_llm_client` | 7 | API calls, retry logic, provider fallback |
| `test_retrieve` | 12 | Cosine similarity, scoring, normalization, full pipeline |

## Cognitive Architecture

Based on the original paper's design:

1. **Perceive** — detect events within vision radius (4 tiles)
2. **Retrieve** — search memories by recency (×0.5) + relevance (×3) + importance (×2)
3. **Plan** — generate daily schedule, decompose into hourly actions
4. **Reflect** — when importance counter hits 150, generate insights from accumulated memories
5. **Execute** — move agent, perform action, update state

## Tech Stack

- Python 3.13+
- FastAPI + WebSocket (simulation server)
- NumPy (vector operations)
- SiliconFlow API (LLM provider)
