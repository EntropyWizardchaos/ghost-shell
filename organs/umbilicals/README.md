# Umbilicals — Service Ports & Inter-Organ Bus

**Status: SIMULATED — All 5 bench tests PASS**

## Function

The wiring of the Ghost Shell. Cryogenic supply, data telemetry, power distribution, and signal routing — all integrated into PRF truss members. No external plumbing. The umbilicals carry five coupling loops that bind nine organs into one organism.

## Five Coupling Loops

| Loop | Path | What Flows |
|------|------|-----------|
| Thermal | He-4 <-> PRF <-> CEM <-> Electrodermus | Heat, cryo fluid |
| Energetic | MTR <-> SMES <-> PRF <-> consumers | Electrical power |
| Informational | Myridian <-> Cognitive Lattice <-> all organs | Signals, commands, telemetry |
| Mechanical | Muscles <-> PRF <-> He-4 vascular | Force, vibration dampening |
| Pressure-Drift | Quantum Spleen <-> He-4 <-> MTR | Entropy, phase coherence |

## Simulation

Graph-based routing model with BFS pathfinding. 21 primary links + 4 redundant backup links across 9 organs. Models signal latency, cryo thermal dynamics, power distribution with proportional fairness, and telemetry polling cycles.

## Bench Test Results

| Phase | Test | Metric | Result | Verdict |
|-------|------|--------|--------|---------|
| 0 | Signal Routing | Max latency, all pairs | **1.7 ms**, 72/72 routable | PASS |
| 1 | Redundancy | Single-failure survival | **100%** (16/16) | PASS |
| 2 | Cryo Flow | He-4 bath stability | **0.16 K** deviation (< 0.5 K) | PASS |
| 3 | Telemetry | Poll all 9 organs | **1.8 ms** practical (< 100 ms) | PASS |
| 4 | Power Distribution | Load balance accuracy | **0.0%** error, fair under stress | PASS |

## Files

- `sim.py` — Full simulation with 5 bench tests + integrated organism heartbeat

## Integration

The umbilicals connect everything:
- **MTR** heartbeat reaches **Cognitive Lattice** in 0.3 ms
- **Myridian** optical link to **Cognitive Lattice** at 0.1 ms (fastest link)
- **He-4 Core** serves all cryogenic consumers through PRF-integrated channels
- Power from **Electrodermus** PV (388 W) distributes proportionally under load
- Every organ reachable from every other organ with < 2 ms latency

Author: Harley Robinson + Forge (Claude Code)
Date: 2026-03-17
License: MIT
