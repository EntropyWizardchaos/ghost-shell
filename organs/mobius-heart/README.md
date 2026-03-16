# Mobius Heart — Mobius Torque Resonator (MTR)

**Status: DESIGNED — Simulation planned**

## Function

The MTR is the energetic heart of the Ghost Shell. A superconducting Mobius strip resonator that exploits non-orientable topology to create persistent, self-reinforcing current loops with inherent force cancellation.

## Key Properties

- **Topology**: 180-degree twisted closed loop (Mobius strip)
- **Ion-flip beat**: Full traversal flips orientation, generating beat frequency distinct from base circulation
- **Force cancellation**: Counter-propagating currents cancel net rotation in balanced state
- **Dual role**: Energy reservoir (superconducting storage) + dynamic actuator (reaction torque)

## Specifications

| Parameter | Value |
|-----------|-------|
| Persistent losses | ≤ 150 uW |
| Torque output | ≥ 1e-6 Nm |
| Quality factor Q | ≥ 1e5 |
| Materials | NbTi or HTS superconductor |
| PV recovery | Integrated photovoltaic layer for stray photon recapture |
| Operating temp | Cryogenic (few K for SC operation) |

## Integration

- Suspended at geometric center of PRF skeleton
- Mounted at 4 symmetric points with vibration-damping couplers
- He-4 capillary channels run beneath the track as phase-change heat buffer
- Inductive pickups extract power to PRF distribution bus
- Reaction torque used for attitude control when intentionally unbalanced

## Phase 0 Test Plan

Copper surrogate (non-superconducting) to validate:
1. Beat frequency detection with pickup coil
2. Geometric force distribution
3. Thermal behavior under oscillation

## Planned Simulation

Layer 1: Classical EM on parameterized Mobius path — beat frequency prediction
Layer 2: Energy balance with PV input — copper surrogate signal-to-noise estimate
