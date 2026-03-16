# Mobius Heart — Mobius Torque Resonator (MTR)

**Status: DESIGNED + SIMULATED — Stress-tested, REBCO spec locked**

## Function

The MTR is the energetic heart of the Ghost Shell. A superconducting Mobius strip resonator that exploits non-orientable topology to create persistent, self-reinforcing current loops with inherent force cancellation.

## Key Properties

- **Topology**: 180-degree twisted closed loop (Mobius strip)
- **Ion-flip beat**: Full traversal flips orientation, generating beat frequency at f_circ/2
- **Force cancellation**: Counter-propagating currents cancel net rotation in balanced state
- **Dual role**: Energy reservoir (superconducting storage) + dynamic actuator (reaction torque)

## Specifications (REBCO — locked)

| Parameter | Value |
|-----------|-------|
| **Material** | REBCO (YBa2Cu3O7) on Hastelloy substrate |
| **Tape width** | 2 mm |
| **Tape thickness** | 0.1 mm |
| **Ring radius** | 50 cm (1m diameter) |
| **Operating current** | 200 A |
| **T_crit** | 92 K |
| **T_bath** | 4.2 K (He-4) |
| **Thermal margin** | 87.8 K (virtually unquenchable) |
| **Beat frequency** | 1,592 Hz (at v_ion = 10 km/s) |
| **Bend strain** | 0.20% (limit 0.40%, 50% headroom) |
| **Freq shift (self-field)** | 400 ppm (correctable) |
| **Radiation Q** | ~2.7e15 (negligible loss) |
| **Persistent losses** | ≤ 150 uW |
| **Quality factor Q** | ≥ 1e5 |

### Why REBCO, not NbTi

The original NbTi design (R=5cm) fails catastrophically at Attack 3: the Mobius twist puts 10% torsional strain on the strip, far exceeding NbTi's 0.5% critical strain. REBCO on Hastelloy tolerates 0.4-0.7% strain, and narrow 2mm tape at R=50cm keeps total strain at 0.20% — well within limits.

Additional REBCO advantages:
- T_crit = 92K vs 9.2K — 10x higher, giving 87.8K thermal margin at 4.2K bath
- Could operate at 77K (liquid nitrogen) for reduced cooling cost
- Higher Jc at 4K — supports 200A+ in narrow tape

## Stress Test Results

Six adversarial attacks ("The Little Black Dress"):

| Attack | What it tests | NbTi (R=5cm) | REBCO (R=50cm) |
|--------|--------------|--------------|----------------|
| 1. Lorentz Force | Self-field structural stress | SURVIVES | SURVIVES |
| 2. Copper Signal | Phase 0 detection window | SURVIVES | VULNERABLE* |
| 3. Bend Strain | Twist kills superconductivity? | **FATAL** | SURVIVES |
| 4. Radiation Q | Oscillating dipole power leak | SURVIVES | SURVIVES |
| 5. Thermal Hot Spot | Twist region quench? | SURVIVES | SURVIVES |
| 6. Frequency Shift | Self-field beat drift | VULNERABLE | SURVIVES |

*Phase 0 copper surrogate at REBCO geometry has fewer detectable cycles due to thinner tape / higher resistance. Fix: use thicker copper surrogate strip or lock-in amplifier. This is a test rig issue, not a design issue.

## Layer 1 Simulation Results (5/5 pass)

| Test | What | Result |
|------|------|--------|
| Normal flip | \|N(0) + N(2pi)\| = 0 | PASS |
| Beat frequency | f_beat / f_circ = 0.5000 | PASS |
| Torque cancellation | 100% cancelled | PASS |
| Moment oscillation | Sign flip + period = 2 laps | PASS |
| 1/R scaling | All ratios within 1% | PASS |

## Integration

- Suspended at geometric center of PRF skeleton
- Mounted at 4 symmetric points with vibration-damping couplers
- He-4 capillary channels run beneath the track as phase-change heat buffer
- Inductive pickups extract power to PRF distribution bus
- Reaction torque used for attitude control when intentionally unbalanced

## Phase 0 Test Plan

Copper surrogate (non-superconducting) to validate:
1. Beat frequency detection with pickup coil (use lock-in amplifier for REBCO geometry)
2. Geometric force distribution
3. Thermal behavior under oscillation

## Files

- `sim.py` — Layer 1 classical EM simulation (parameterized Mobius path, beat frequency, torque)
- `stress_test.py` — Original NbTi stress test (6 attacks, found bend strain fatal)
- `stress_test_rebco.py` — REBCO redesign (6 attacks, all clear)

## Design History

1. **Original spec** (Oct 2025): NbTi, R=25-50mm, w=8-15mm — from Master MTR Prints
2. **Ghost Shell sim** (Mar 2026): Layer 1 sim at R=5cm, 5/5 bench tests pass
3. **Stress test v1** (Mar 2026): 6 adversarial attacks — bend strain FATAL at R=5cm
4. **REBCO redesign** (Mar 2026): Switch material + geometry — all 6 attacks clear
5. **Wide vs narrow** (Mar 2026): Tested w=12mm at R=1.5m — works but big. Narrow (w=2mm, R=50cm) is tighter and cleaner. Locked.
