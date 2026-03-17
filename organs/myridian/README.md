# Myridian — A Living Photonic Processor

**Status: SIMULATED — All 5 bench tests PASS**

## Function

The nervous system of the Ghost Shell. A bio-photonic microprocessor grown from engineered mycelium on a PRF scaffold. Each fungal junction acts as an Iris Switch — opening or closing in response to specific wavelengths. Computation arises from light modulation, bioluminescent timing, and structural adaptation.

A self-healing, self-learning logic fabric. The sensory bridge between the external world and the Cognitive Lattice brain.

## Architecture

| Layer | Function | Physical Expression |
|-------|----------|-------------------|
| PRF "Bones" | Photonic & conductive truss | CNT-DLC lattice with embedded waveguides |
| Myridian layer | Adaptive logic medium | Photosensitive mycelial web |
| Optical gates | Logic & timing | Light intensity modulates conductivity |
| Bioluminescent nodes | Internal clocking | Phase-locked optical pulses |
| Electro-optic I/O | Read/write interface | LED/fiber inputs, photodiode outputs |

## Simulation

4x4 grid of Iris Switch junctions + 4 bioluminescent clock nodes. Lateral signal propagation through neighbor coupling. Hebbian learning reinforces correlated pathways. Morphological memory retains learned conductance through structural change.

**Key parameters:**
- Per-junction ON/OFF ratio: 15.8x (G_dark=0.01, G_light=0.15)
- 4 bioluminescent clocks with entrainment coupling
- Hebbian learning rate: 0.008 per correlated activation
- Morphological retention: 85% after 24h simulated decay

## Bench Test Results

| Phase | Test | Metric | Result | Verdict |
|-------|------|--------|--------|---------|
| 0 | Optical Gating | ON/OFF conductance ratio | **15.8x** (>= 3x) | PASS |
| 1 | Logic Gates | Truth-table fidelity (AND/OR/NOT) | **100%** (>= 90%) | PASS |
| 2 | Phase-Locked Timing | Phase error over 60s | **16.7 deg** (< 20 deg) | PASS |
| 3 | Memory Formation | Retained conductance after 24h | **85%** (>= 10%) | PASS |
| 4 | Mini Classifier | 2-bit pattern accuracy | **100%** (>= 80%) | PASS |

## Integration

- Grows on **PRF Bones** (CNT-DLC scaffold provides waveguides)
- Feeds optical signals to **Cognitive Lattice** (MZI mesh brain)
- Receives environmental data through **Electrodermus** (skin sensors)
- Clock nodes entrain to **Mobius Heart** (MTR master oscillation)
- Operates at 280-310 K (bio-compatible zone, thermally managed by **CEM**)

## Files

- `sim.py` — Full simulation with all 5 bench tests

Author: Harley Robinson + Forge (Claude Code)
Date: 2026-03-17
License: MIT
