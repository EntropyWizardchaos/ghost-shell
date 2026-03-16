# Ghost Shell

**A cryogenic artificial organism integrating seven subsystems analogous to biological anatomy.**

Designed by Harley Robinson.

---

## Architecture

The Ghost Shell is a seven-organ cryogenic-photonic organism. Each organ occupies a specific functional tier, and five coupled loops (thermal, energetic, informational, mechanical, pressure-drift) bind them into a single coherent system.

```
                    ┌─────────────────┐
                    │  Electrodermus  │  ← Interface (skin)
                    │  power harvest  │
                    │  radiation ctrl │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────┴───────┐  ┌──┴──┐  ┌────────┴────────┐
     │  PRF (Bones)   │  │He-4 │  │    Cognitive     │
     │  CNT/DLC truss │  │Core │  │     Lattice      │
     │  heat highway  │  │cryo │  │  MZI mesh brain  │
     │  waveguide     │  │buff.│  │  ACF-1 govern.   │
     └────────┬───────┘  └──┬──┘  └────────┬────────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────┴────────┐
                    │  Mobius Heart   │  ← Source (MTR)
                    │  SC resonator   │
                    │  energy + torque │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │                             │
     ┌────────┴────────┐          ┌─────────┴────────┐
     │ Quantum Spleen  │          │   He-4 Umbilicals │
     │ entropy buffer  │          │   cryo + telemetry │
     │ coherence recycle│          │   service ports    │
     └─────────────────┘          └──────────────────┘
```

## Organ Status

| Organ | Tier | Status | Simulation |
|-------|------|--------|------------|
| **Mobius Heart (MTR)** | Source | **Stress-tested** | **PASS (5/5 sim + 6/6 attacks)** |
| **PRF (Bones)** | Structure | **Simulated** | **PASS (5/5 bench tests)** |
| **He-4 Core** | Thermal | **Simulated** | **PASS (5/5 bench tests)** |
| **Electrodermus** | Interface | **Simulated** | **PASS (5/5 bench tests)** |
| **Quantum Spleen** | Buffer | **Simulated** | **PASS (5/5 bench tests)** |
| **Muscles** | Motor | **Simulated** | **PASS (5/5 bench tests)** |
| **SMES** | Energy | **Designed** | **Integration tested** |
| **Cognitive Lattice** | Brain | Designed | -- |
| **He-4 Umbilicals** | Service | Designed | -- |

## Quantum Spleen — Bench Test Results

The Quantum Spleen (Autonomous Coherence Stabilizer) has been simulated using Lindblad master equation dynamics with real parameters from Yale AQEC (2025). All five bench tests pass:

| Phase | Test | Result |
|-------|------|--------|
| 0 | Entropy Absorption | **32.7% reduction** |
| 1 | Discrete Storage | **5% anharmonic deviation** |
| 2 | Variance Suppression | **50.3% below thermal** |
| 3 | Coherent Emission | **Purity 7x above thermal** |
| 4 | Long-Cycle Stability | **0.02% drift / 50 cycles** |

Simulation code: [`organs/quantum-spleen/sim.py`](organs/quantum-spleen/sim.py)
Visualization: [`organs/quantum-spleen/viz.py`](organs/quantum-spleen/viz.py)
Results figure: [`docs/figures/quantum_spleen_results.png`](docs/figures/quantum_spleen_results.png)

## PRF Bones — Bench Test Results

The PRF (Photocarbon Resonance Frame) is the structural skeleton — a CNT-DLC composite strut carrying load, heat, and vibration as one medium. All five bench tests pass:

| Phase | Test | Result |
|-------|------|--------|
| 0 | Mechanical Mode Map | **6/6 modes within 5% analytic** |
| 1 | Thermal Conductivity | **k_eff = 2045 W/m-K** |
| 2 | Piezo Damping | **+800% damping, Q: 100 → 11** |
| 3 | Dynamic Stiffness | **dE/E = 17.2% across 10-50 MHz** |
| 4 | Thermal Step Response | **Settled in 85s (budget 120s)** |

Simulation code: [`organs/prf-bones/sim.py`](organs/prf-bones/sim.py)
Results figure: [`docs/figures/prf_bones_results.png`](docs/figures/prf_bones_results.png)

## Electrodermus — Bench Test Results

The Electrodermus is a photovoltaic CNT laminate skin that harvests light, radiates heat, senses vibration, gates reflectivity, and heals itself. All five bench tests pass:

| Phase | Test | Result |
|-------|------|--------|
| 0 | Spectral Absorption | **95% avg across 400-1100nm** |
| 1 | Cryo Emissivity | **epsilon = 0.922 at 77K** |
| 2 | Vibration Sensing | **100% band (1Hz-10MHz), 149 dB** |
| 3 | Optical Gating | **dR/R = 98% (W-doped VO2)** |
| 4 | Self-Healing | **100% conductivity restored** |

Photonic Fur is a design option (not required — bare skin radiates 40x thermal budget).

Simulation code: [`organs/electrodermus/sim.py`](organs/electrodermus/sim.py)
Results figure: [`docs/figures/electrodermus_results.png`](docs/figures/electrodermus_results.png)

## He-4 Core — Bench Test Results

The He-4 Core is the cryogenic metabolism — liquid helium-4 phase-change channels maintaining quasi-isothermal conditions at the MTR core. The core handles parasitic losses (~0.8W); the full 25W thermal budget flows through PRF to skin. All five bench tests pass:

| Phase | Test | Result |
|-------|------|--------|
| 0 | Cooldown (77K to 4.2K) | **0.1 hours** |
| 1 | Phase-Change Buffer | **T_max = 4.222K under 10W spike** |
| 2 | Thermal Regulation | **0.0 mK range (PI control)** |
| 3 | Vascular Flow | **MTR>mid>far hierarchy, 17.6% d^4 deviation** |
| 4 | Entropy Exchange | **150% margin, converged** |

Simulation code: [`organs/he4-core/sim.py`](organs/he4-core/sim.py)
Results figure: [`docs/figures/he4_core_results.png`](docs/figures/he4_core_results.png)

## Muscles — Bench Test Results

The Muscles are hybrid CNT yarn / REBCO voice-coil actuators — fast-twitch and slow-twitch fibers in the same bundle. Every movement the body makes runs through these. All five bench tests pass:

| Phase | Test | Result |
|-------|------|--------|
| 0 | CNT Yarn Contraction | **11.9% strain, 80 MPa, 1.8 ms** |
| 1 | REBCO Voice-Coil Stroke | **360 N, 20 mm, 0.0 W loss** |
| 2 | Hybrid Bundle | **15,239 N combined, 84% @ 100 Hz** |
| 3 | Fatigue Life | **98% retention, SF=2.18 at 10^6 cycles** |
| 4 | Coordinated Movement | **187 ms settle, 1.98 deg error** |

Simulation code: [`organs/muscles/sim.py`](organs/muscles/sim.py)
Results figure: [`docs/figures/muscles_results.png`](docs/figures/muscles_results.png)

## Coupling Loops

The seven organs are bound by five coupling loops:

1. **Thermal** — He-4 capillary channels carry heat from MTR core through PRF frame to Electrodermus skin for radiation
2. **Energetic** — MTR superconducting loop stores/delivers energy via inductive pickups through PRF power bus
3. **Informational** — Cognitive Lattice monitors all organ states; MTR oscillation serves as master clock via photonic distribution
4. **Mechanical** — MTR reaction torque couples through PRF truss for attitude control and stabilization
5. **Pressure-Drift** — Quantum Spleen buffers entropy fluctuations, recycling coherence back to MTR and Cognitive Lattice

## Mobius Heart — Stress Test Results (REBCO Redesign)

Original NbTi design (R=5cm) failed at bend strain — 10% torsional strain vs 0.5% limit. Redesigned with REBCO HTS tape:

| Parameter | Original (NbTi) | Redesign (REBCO) |
|-----------|-----------------|------------------|
| Material | NbTi | REBCO on Hastelloy |
| Radius | 5 cm | 50 cm |
| Tape width | 10 mm | 2 mm |
| T_crit | 9.2 K | 92 K |
| Thermal margin | 5.0 K | 87.8 K |
| Bend strain | 10.0% (FATAL) | 0.20% (SURVIVES) |
| Beat frequency | 15,916 Hz | 1,592 Hz |

Simulation: [`organs/mobius-heart/sim.py`](organs/mobius-heart/sim.py)
Stress test (NbTi): [`organs/mobius-heart/stress_test.py`](organs/mobius-heart/stress_test.py)
Stress test (REBCO): [`organs/mobius-heart/stress_test_rebco.py`](organs/mobius-heart/stress_test_rebco.py)

## Key Specifications

| Parameter | Value |
|-----------|-------|
| MTR material | REBCO HTS (2mm x 0.1mm tape) |
| MTR radius | 50 cm (1m diameter) |
| MTR operating current | 200 A |
| MTR thermal margin | 87.8 K |
| MTR persistent losses | ≤ 150 uW |
| MTR torque | ≥ 1e-6 Nm |
| MTR quality factor | ≥ 1e5 |
| PRF layup | [0/+-45/90]s, ~1.0mm, E = 70 GPa (static), 91 GPa (glassy) |
| PRF areal density | ~1.3 kg/m^2 |
| PRF thermal conductivity | k_eff = 2045 W/m-K (T-dependent, 4.2K to 250K) |
| PRF relaxation center | 25 MHz (mid-band, 60% sp3 DLC) |
| PRF piezo damping | +800%, Q: 100 → 11 |
| PRF strut geometry | Hollow tube OD=6.37mm, wall=0.5mm (same area as old flat beam) |
| PRF periosteum sheath | 3mm CNT fiber wrap, k=750 W/m-K, 88 mm²/strut |
| PRF total thermal capacity | 419 W (6 struts, core + periosteum) |
| PRF Mode 1 frequency | 794 Hz (tube + sheath, above 200 Hz muscle band) |
| SMES coil | 3000 turns REBCO, R=15cm, L=30cm, inside MTR ring |
| SMES inductance | 2.66 H |
| SMES energy | 53.3 kJ at 200A (8 min shadow walk, 3 min shadow run) |
| SMES B_peak | 2.51 T (REBCO Ic > 300A at this field) |
| SMES mass | 5.0 kg (2827m REBCO tape) |
| Electrodermus absorption | 95% avg (400-1100nm, multi-chirality CNT) |
| Electrodermus emissivity | 0.922 at 77K, 0.950 at 250K |
| Electrodermus optical gating | W-doped VO2, dR/R = 98%, 2.7x flux swing |
| Electrodermus sensing | 1 Hz - 10 MHz, dual phase-coupled nodes, 149 dB |
| Electrodermus self-healing | 100% conductivity restored post fracture |
| Electrodermus heater lanes | 100 Ohm @ 12V = 1.44W |
| Electrodermus radiative capacity | ~1050 W (40x thermal budget) |
| He-4 bath temperature | 4.2K (1 atm, liquid) |
| He-4 mass | ~754g in R=8cm, L=30cm vessel |
| He-4 latent buffer | ~15,600 J (absorbs 10W x 60s with 3.8% evaporation) |
| He-4 parasitic load | 0.8W nominal (PRF back-conduction + MLI + electronics) |
| He-4 cryocooler | 2.0W at 4.2K, two-stage GM/PT |
| He-4 vascular tree | trunk 0.6mm, branches 0.5mm, endpoints 0.40/0.35/0.30mm (MTR/mid/far) |
| He-4 flow hierarchy | MTR:mid:far = 2.5:1.6:1.0 (thermosiphon, Venturi junctions, 17.6% d^4 dev) |
| He-4 entropy margin | 150% above nominal |
| He-4 thermal budget | dump ≥ 25W via PRF to skin, settle ±3K in ≤ 120s |
| Muscles fast-twitch | CNT yarn, 11.9% strain, 80 MPa, 1.8 ms response, 200 Hz bandwidth |
| Muscles slow-twitch | REBCO voice-coil, 360 N, 20 mm stroke, 0.0 W loss (superconducting) |
| Muscles hybrid bundle | 60/40 CNT/REBCO, 15,239 N peak, 84% amplitude @ 100 Hz |
| Muscles fatigue | 5% cruise strain, SF=2.18, 98% retention @ 10^6 cycles |
| Muscles joint performance | 187 ms settle, 136 Nm peak torque, 1215 deg/s peak velocity |
| Cognitive Lattice operating band | 4-20 K |
| Cognitive Lattice phase coherence | > 1000x ambient |

## License

All rights reserved. Harley Robinson, 2025-2026.
