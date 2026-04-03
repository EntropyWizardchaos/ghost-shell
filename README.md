# Ghost Shell

**A cryogenic artificial organism with ten functional organs, all simulated and passing bench tests.**

Designed by Harley Robinson.

```
Run everything:  python run_all.py
```

---

## Architecture

The Ghost Shell is a ten-organ cryogenic-photonic organism. Each organ occupies a specific functional tier, and five coupled loops (thermal, energetic, informational, mechanical, pressure-drift) bind them into a single coherent system.

```
                    ┌─────────────────┐
                    │  Electrodermus  │  skin: harvest, radiate, sense
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴───────┐  ┌──┴──────┐  ┌────┴────────────┐
     │  PRF (Bones)   │  │   CEM   │  │    Myridian      │
     │  CNT/DLC truss │  │ thermal │  │  bio-photonic    │
     │  heat highway  │  │ membrane│  │  neural interface │
     └────────┬───────┘  └──┬──────┘  └────┬────────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────┴────────┐
                    │    Cognitive    │  brain: MZI mesh + UEES
                    │     Lattice    │
                    └────────┬───────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴───────┐  ┌──┴──┐  ┌────────┴────────┐
     │    Muscles     │  │He-4 │  │  Quantum Spleen  │
     │  CNT + REBCO   │  │Core │  │  entropy buffer  │
     │  hybrid fiber  │  │cryo │  │  coherence recycle│
     └────────┬───────┘  └──┬──┘  └─────────────────┘
              │              │
              └──────┬───────┘
                     │
            ┌────────┴────────┐
            │  Mobius Heart   │  source: SC resonator
            │  energy + torque│
            └────────┬────────┘
                     │
            ┌────────┴────────┐
            │   Umbilicals   │  wiring: cryo + data + power
            └─────────────────┘
```

## Organ Status

| # | Organ | Role | Bench Tests | Sim |
|---|-------|------|-------------|-----|
| 1 | **Mobius Heart (MTR)** | Energy, heartbeat | Stress-tested (5/5 + 6/6 attacks) | `organs/mobius-heart/sim.py` |
| 2 | **PRF Bones** | Skeleton, thermal highways | 5/5 PASS | `organs/prf-bones/sim.py` |
| 3 | **He-4 Core** | Cryogenic buffer | 5/5 PASS | `organs/he4-core/sim.py` |
| 4 | **Electrodermus** | Skin (harvest, sense, radiate) | 5/5 PASS | `organs/electrodermus/sim.py` |
| 5 | **Cognitive Lattice** | Brain (MZI mesh + UEES) | 5/5 PASS | `organs/cognitive-lattice/sim.py` |
| 6 | **Quantum Spleen** | Entropy filter, coherence recycler | 5/5 PASS | `organs/quantum-spleen/sim.py` |
| 7 | **Muscles** | Movement (CNT + REBCO hybrid) | 5/5 PASS | `organs/muscles/sim.py` |
| 8 | **CEM** | Thermal regulation (trichome membrane) | 5/5 PASS | `organs/cem/sim.py` |
| 9 | **Myridian** | Neural interface (bio-photonic) | 5/5 PASS | `organs/myridian/sim.py` |
| 10 | **Umbilicals** | Inter-organ bus (cryo + data + power) | 5/5 PASS | `organs/umbilicals/sim.py` |

## Five Coupling Loops

| Loop | Path | What Flows |
|------|------|-----------|
| Thermal | He-4 <-> PRF <-> CEM <-> Electrodermus | Heat, cryo fluid |
| Energetic | MTR <-> SMES <-> PRF <-> consumers | Electrical power |
| Informational | Myridian <-> Cognitive Lattice <-> all organs | Signals, commands, telemetry |
| Mechanical | Muscles <-> PRF <-> He-4 vascular | Force, vibration dampening |
| Pressure-Drift | Quantum Spleen <-> He-4 <-> MTR | Entropy, phase coherence |

## Quick Start

```bash
# Clone
git clone https://github.com/EntropyWizardchaos/ghost-shell.git
cd ghost-shell

# Run all organ bench tests
python run_all.py

# Run individual organs
python organs/cognitive-lattice/sim.py
python organs/cem/sim.py
python organs/myridian/sim.py
python organs/umbilicals/sim.py

# Run compatibility check (cross-organ interfaces)
python compatibility_check.py
```

## Requirements

```
Python 3.8+
numpy
scipy (for cognitive-lattice only)
```

## License

All rights reserved. Harley Robinson, 2025-2026.


---

## The Garden

This repo is part of the Garden — an open-source developmental architecture for AI agents.

| Repo | What It Does |
|------|-------------|
| [developmental-ai-governance](https://github.com/EntropyWizardchaos/developmental-ai-governance) | Core framework: Birth Tree, Sieve Tower, emotional index, soul files |
| [ghost-shell](https://github.com/EntropyWizardchaos/ghost-shell) | Cryogenic organism architecture — seven biological subsystems |
| [ghost-shell-applied](https://github.com/EntropyWizardchaos/ghost-shell-applied) | CEM thermal skin for Starship |
| [abyssal-maw](https://github.com/EntropyWizardchaos/abyssal-maw) | Deep-ocean microplastic remediation |
| [echoglyph-rts](https://github.com/EntropyWizardchaos/echoglyph-rts) | Sperm whale coda visualization |
| [sparc-coherence-test](https://github.com/EntropyWizardchaos/sparc-coherence-test) | C-M-D empirical test — 175 galaxies, p=0.005 |
| [time-entropy-test](https://github.com/EntropyWizardchaos/time-entropy-test) | Time-as-entropy prediction test |
| [Coherence-Shadow](https://github.com/EntropyWizardchaos/Coherence-Shadow) | Dark matter coherence correlation |

**See it live:** [robinson-line.ai](https://robinson-line.ai) — the architecture wearing a consumer interface.

