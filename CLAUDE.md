# AI Town — Project Guide

## Purpose
Build an AI Town simulation from scratch in Python, inspired by the "Generative Agents: Interactive Simulacra of Human Behavior" paper. The primary learning goal is understanding agent cognitive architecture: memory, reflection, retrieval, planning.

## About the Developer
- Veon / Product Manager, also handling some development
- Uses Claude Code for product demos and learning development
- Limited coding background — needs detailed comments in implementation files (not test files)
- Prefers step-by-step execution with explanations, not TDD "expect fail" approach
- Wants test documentation written to `docs/` after each test suite

## Run Tests
```bash
cd D:\pythonProject\ccTest\myAITown
python -m pytest tests/ -v
```

## Git Conventions
- Commit after each task
- Assets are copied into repo (not symlinked) for portability

## Test Report Convention
After each test suite is written, create a test documentation file at `docs/test_<module>.md`:
- One file per module (e.g., `test_spatial.md`, `test_llm_client.md`)
- Format: section per test method — test name, what it asserts, why it passes
- Explain every test method: what scenario it covers, what input it uses, what the expected output is, and the logic behind why the implementation produces that output
- Keep it concise — no code snippets, just intent and logic

## API Providers
- **SiliconFlow** (primary): `https://api.siliconflow.cn/v1`
  - Chat: `inclusionAI/Ling-flash-2.0`
  - Embedding: `Qwen/Qwen3-Embedding-8B` (1024 dims, sole embedding provider)
- **DashScope** (chat fallback only): `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - Chat: `qwen3.6-flash`, `qwen-flash-character-2026-02-26`, `qwen3.6-flash-2026-04-16`
  - Embedding: none (different models produce incompatible vector spaces)

## Key Technical Decisions
1. **Embedding: single provider only** — different embedding models produce different vector spaces. Cosine similarity only works within the same model. No fallback for embeddings.
2. **Chat: multi-provider fallback** — on 403 (insufficient quota), rotate to next model/provider. Chat outputs are text, no vector space issue.
3. **Embedding dimension: 1024** — Qwen3-Embedding-8B supports 32-4096; 1024 chosen for balance.
4. **Map hierarchy** — always 3 levels deep: `world:sector:arena`. `get_path_for_location` is hardcoded to this.

## Implementation Progress

### Completed (84 tests passing)
| Task | File(s) | Status |
|------|---------|--------|
| Spatial Memory | `agent/memory/spatial.py` | Done, 7 tests |
| Associative Memory | `agent/memory/associative.py` | Done, 10 tests |
| Scratch Memory | `agent/memory/scratch.py` | Done, 7 tests |
| LLM Client | `llm/client.py` | Done, 7 tests |
| Retrieve | `agent/cognitive/retrieve.py` | Done, 12 tests |
| Perceive | `agent/cognitive/perceive.py` | Done, 6 tests |
| Reflect | `agent/cognitive/reflect.py` | Done, 8 tests |
| Plan | `agent/cognitive/plan.py` | Done, 10 tests |
| Execute | `agent/cognitive/execute.py` | Done, 17 tests |

### Remaining
| Task | Description |
|------|-------------|
| Persona | Load agent definitions from JSON, initialize all memory types |
| Simulation Engine | Main loop: perceive → retrieve → plan → reflect → execute |
| Frontend | Pygame rendering of map + agents |
| Integration | Wire everything together |

## Agent Cognitive Loop
```
Perceive → Retrieve → Plan → Reflect → Execute
```

## Hyperparameters (config.py)
- `VISION_RADIUS = 4` — see 4 tiles in each direction
- `ATT_BANDWIDTH = 3` — max events to pay attention to at once
- `RETENTION = 5` — recent events for deduplication
- `RECENCY_DECAY = 0.99` — memories lose 1% relevance per step
- `IMPORTANCE_TRIGGER_MAX = 150` — reflect after accumulating 150 importance points
- `RETRIEVAL_WEIGHTS = [0.5, 3, 2]` — relevance matters most

## Coding SOP
- **Step-by-step**: Do one module at a time. Write code → write tests → run tests → write test doc → commit. Don't batch.
- **Explain before coding**: Before writing code, briefly explain what the module does and why. The developer is learning.
- **No TDD "expect fail"**: Don't write a test, run it to see it fail, then implement. Just implement, then test.
- **Comments on implementation files**: Every function needs a docstring. Every non-obvious line needs a comment. Test files don't need comments.
- **No skipping test docs**: After every test suite, create `docs/test_<module>.md` before committing.
- **Don't rewrite existing code**: Only modify existing files if there's a bug. New features go in new files.
