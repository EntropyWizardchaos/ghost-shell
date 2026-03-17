# CEM — Corkscrew Equilibrium Membrane

**Status: SIMULATED — All 5 bench tests PASS**

## Function

The thermal regulation organ of the Ghost Shell. A flexible thermal boundary that separates hot and cold regimes while dynamically routing excess heat into a governed sink. Combines switchable thermal trichomes, a loop-heat-pipe (LHP) corkscrew core, and a vacuum laminate structure.

In biological terms: the sweat glands and circulatory system. Without CEM, the organism has no way to manage the 300 K gradient between the MTR core (4.2 K) and the Electrodermus skin (200-350 K).

## Architecture (Hot to Cold)

| Layer | Spec |
|-------|------|
| Hot Skin | 25-50 um SS304 foil, SiC emissive paint, up to 450 K |
| Vacuum Spacer | 50-200 um polyimide, SiO2 pillars, sealed |
| Trichome Matrix | 10,000 CNT/graphite hairs (20 rows x 25 cols, 20 hairs/node) |
| Corkscrew LHP | Helical channel, sintered wick, 20-40 W dual helix capacity |
| Cold Manifold | Cu plate with condenser pads |
| Radiator | 70x70x10 mm finned Al, black anodized |

## Operating Modes

| Mode | Trichomes | Power Flow |
|------|-----------|-----------|
| Protect | All OFF | < 1 W (radiation only) |
| Vent | Few nodes ON | 1-5 W |
| Dump | Many/all nodes ON | 5-30 W |

## Simulation

Thermal mass model with PI control loop. Hot skin, manifold, and radiator as lumped capacitances. Trichome matrix as variable conductance. LHP as capacity-limited heat transport. Radiator as Stefan-Boltzmann emitter.

**Key parameters (from CEM v1 spec, October 2025):**
- Per-hair conductance: G_h = 1.3e-4 W/K
- Total (all engaged): G_tot = 1.3 W/K
- LHP capacity: 30 W (dual helix)
- Safety interlock: T_hot > 450 K

## Bench Test Results

| Phase | Test | Metric | Result | Verdict |
|-------|------|--------|--------|---------|
| 0 | Protect Leak | Power at dT=20K, all OFF | **0.007 W** (< 1 W) | PASS |
| 1 | Step Response | +20W step settle time | **6 s** (< 120 s) | PASS |
| 2 | Dump Capacity | Sustained dump, skin stable | **21.3 W**, 342 K | PASS |
| 3 | Modulation Linearity | Conductance vs node count | **R^2 = 1.000** | PASS |
| 4 | Safety Interlock | Over-temp trip time | **1 s** (< 5 s) | PASS |

## Files

- `sim.py` — Full simulation with all 5 bench tests + integrated variable load run

## Integration

- Trichomes couple to **PRF Bones** (thermal highway substrate)
- LHP condenser connects to **He-4 Core** (cryogenic buffer)
- Hot skin interfaces with **Electrodermus** (outer surface)
- PID setpoint controlled by **Cognitive Lattice** (brain adjusts thermal targets)
- Safety interlock reports to **Cognitive Lattice** anomaly detection

Author: Harley Robinson + Forge (Claude Code)
Date: 2026-03-17
License: MIT
