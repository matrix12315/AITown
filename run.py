"""
Run Simulation — Quick Test
============================
Runs the AI Town simulation and saves output.

Usage:
    python run.py          # default 10 steps
    python run.py 100      # 100 steps
    python run.py 48       # full day (30min/step)
"""
import sys
from sim.engine import Simulation
from config import PERSONAS_DIR, LANGUAGE
import os

STEPS = int(sys.argv[1]) if len(sys.argv) > 1 else 5

# Build persona paths based on LANGUAGE setting
persona_dir = os.path.join(PERSONAS_DIR, LANGUAGE)
persona_paths = [
    os.path.join(persona_dir, f)
    for f in os.listdir(persona_dir)
    if f.endswith(".json")
]

print(f"Language: {LANGUAGE}")
print(f"Personas: {persona_paths}")
print()

# Create and run simulation
sim = Simulation(persona_paths)

# Place all agents at the same starting location (Hobbs Cafe area)
# This ensures they can see each other and trigger conversations
START_TILE = (72, 19)  # Hobbs Cafe area
for agent in sim.agents.values():
    agent.scratch.curr_tile = START_TILE

print(f"Agents: {list(sim.agents.keys())}")
print(f"Start time: {sim.curr_time}")
print(f"All agents start at: {START_TILE} (Hobbs Cafe area)")
print()
print("Note: Agents observe each other when within vision radius.")
print("      Chat generation is not yet implemented (Phase 8).")
print()

print(f"Running {STEPS} steps...")
print("=" * 60)

for i in range(STEPS):
    result = sim.step()
    time = result["time"]
    states = result["states"]
    print(f"\n--- Step {i+1} [{time}] ---")
    for agent_name, agent in sim.agents.items():
        print(f"  {agent.name}:")
        print(f"    Position:  ({agent.scratch.curr_tile[0]}, {agent.scratch.curr_tile[1]})")
        print(f"    Action:    {agent.scratch.act_description or 'idle'}")
        print(f"    Location:  {agent.scratch.act_address or 'none'}")
        print(f"    Emoji:     {agent.scratch.act_pronunciatio or '😶'}")
        if agent.scratch.f_daily_schedule:
            idx = agent.scratch.get_f_daily_schedule_index()
            if idx < len(agent.scratch.f_daily_schedule):
                task, dur = agent.scratch.f_daily_schedule[idx]
                print(f"    Schedule:  [{idx}] {task} ({dur}min)")
        print(f"    Memories:  {len(agent.a_mem.seq_event)} events, {len(agent.a_mem.seq_thought)} thoughts")
        known = agent.s_mem.get_known_locations()
        print(f"    Known loc: {len(known)} areas")

        # Show which agents this one can see
        cx, cy = agent.scratch.curr_tile
        vr = agent.scratch.vision_r
        visible = []
        for other_name, other in sim.agents.items():
            if other_name == agent_name:
                continue
            ox, oy = other.scratch.curr_tile
            if abs(ox - cx) <= vr and abs(oy - cy) <= vr:
                visible.append(f"{other_name} at ({ox},{oy})")
        if visible:
            print(f"    👁️ Sees:   {', '.join(visible)}")

print("\n" + "=" * 60)

# Save
sim_dir = sim.save("test_run")
print(f"\nSaved to: {sim_dir}")
print(f"  replay.json: {os.path.getsize(os.path.join(sim_dir, 'replay.json'))} bytes")
print(f"  diary.md: {os.path.getsize(os.path.join(sim_dir, 'diary.md'))} bytes")

# Print diary preview
diary_path = os.path.join(sim_dir, "diary.md")
with open(diary_path, 'r') as f:
    content = f.read()
print(f"\n--- diary.md preview ---")
print(content[:500])
print("..." if len(content) > 500 else "")
