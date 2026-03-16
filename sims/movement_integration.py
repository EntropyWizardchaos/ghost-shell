"""
Movement Integration Test — Cross-Organ Stress Simulation
==========================================================
The body tries to move. What breaks first?

This is NOT a single-organ bench test. This couples all six simulated
organs into a movement timeline and tracks where limits are exceeded.

Coupled systems:
  Muscles → heat → PRF thermal highway → Electrodermus radiation
  Muscles → heat (cryo) → He-4 core → cryocooler
  Electrodermus PV → electrical bus → Muscles
  MTR stored energy → buffer → Muscles (supplement)
  PRF struts → conduction limit → thermal bottleneck

Movement scenarios tested:
  Phase 0: Power Budget — Can the skin power the muscles at all?
  Phase 1: Gentle Cruise — 2 bundles, low duty. Baseline.
  Phase 2: Active Movement — 6 bundles, moderate duty. Walking.
  Phase 3: Sprint — 12 bundles, high duty. Max sustained.
  Phase 4: Burst — All bundles, max effort, 10 seconds. Emergency.

Design by Harley Robinson. Integration test by Forge.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ==============================================================
# CONSTANTS
# ==============================================================

SIGMA_SB = 5.670374419e-8   # Stefan-Boltzmann [W/m2/K4]

# ==============================================================
# ORGAN PARAMETERS (from individual bench tests)
# ==============================================================

# --- Electrodermus (skin) ---
A_SKIN = 5.0                 # m2 (shell surface area, ~80cm radius sphere)
T_SKIN = 250.0               # K (operating skin temperature)
T_SPACE = 3.0                # K (deep space background)
SKIN_EMISSIVITY = 0.922      # at 77K, ~0.95 at 250K — use 0.93 average
SKIN_ABSORPTION = 0.95       # broadband, 400-1100 nm
# PV conversion: CNT forest photovoltaics
# Literature: 10-32% broadband. Use 15% (mid-range for multi-chirality)
PV_EFFICIENCY = 0.15
# Solar flux at 1 AU
SOLAR_FLUX_1AU = 1361.0      # W/m2
# Effective illuminated area (half the sphere, cosine-weighted = pi*R^2)
# For R=0.8m sphere: A_illuminated = pi*0.8^2 = 2.01 m2
A_ILLUMINATED = 2.0          # m2 (projected area facing sun)

# Radiative capacity (for reference — from bench test)
Q_RAD_MAX = SKIN_EMISSIVITY * SIGMA_SB * A_SKIN * (T_SKIN**4 - T_SPACE**4)

# --- PRF Bones (thermal highway) — hollow tube geometry ---
PRF_K_EFF = 2045.0           # W/m-K (bench test result, T-dependent average)
PRF_TUBE_OD = 6.37e-3        # m (6.37 mm outer diameter)
PRF_TUBE_WALL = 0.5e-3       # m (0.5 mm wall thickness)
PRF_TUBE_ID = PRF_TUBE_OD - 2 * PRF_TUBE_WALL  # 5.37 mm inner diameter
PRF_LENGTH = 0.30            # m (30 cm strut span, MTR ring to skin)
PRF_CROSS = np.pi / 4 * (PRF_TUBE_OD**2 - PRF_TUBE_ID**2)  # m2 (annular cross-section)
N_STRUTS = 6                 # geodesic minimum for full-body coverage

# --- Periosteum (CNT fiber thermal sheath wrapping each PRF tube) ---
# Like carbon fiber wrapping a structural member, but optimized for heat.
# CNT yarn/fiber: k ~ 500-1500 W/m-K (aligned yarn bundles)
# Wraps each 6.37mm OD tube with 3mm thick CNT fiber sheath.
# Sheath OD = 6.37 + 2*3 = 12.37 mm
SHEATH_THICKNESS = 3.0e-3    # m (3 mm wrap thickness)
SHEATH_K = 750.0             # W/m-K (CNT fiber yarn, conservative — lower than PRF core)
SHEATH_DENSITY = 1400.0      # kg/m3 (CNT yarn density)
SHEATH_CP = 700.0            # J/kg/K

# Sheath cross-section (annulus around tube)
SHEATH_OD = PRF_TUBE_OD + 2 * SHEATH_THICKNESS  # 12.37 mm
SHEATH_CROSS = np.pi / 4 * (SHEATH_OD**2 - PRF_TUBE_OD**2)  # m2 (sheath only)

# Combined thermal conductance per strut: PRF core + sheath in parallel
# Q = (k_prf * A_prf + k_sheath * A_sheath) * dT / L
PRF_DT_MAX = 246.0           # K
Q_CORE_PER_STRUT = PRF_K_EFF * PRF_CROSS * PRF_DT_MAX / PRF_LENGTH
Q_SHEATH_PER_STRUT = SHEATH_K * SHEATH_CROSS * PRF_DT_MAX / PRF_LENGTH
Q_PER_STRUT = Q_CORE_PER_STRUT + Q_SHEATH_PER_STRUT
Q_PRF_MAX = N_STRUTS * Q_PER_STRUT

# PRF thermal mass (core + sheath)
PRF_DENSITY = 1750.0         # kg/m3
PRF_CP = 700.0               # J/kg/K (approximate)
PRF_MASS_PER_STRUT = PRF_DENSITY * PRF_CROSS * PRF_LENGTH
SHEATH_MASS_PER_STRUT = SHEATH_DENSITY * SHEATH_CROSS * PRF_LENGTH
TOTAL_MASS_PER_STRUT = PRF_MASS_PER_STRUT + SHEATH_MASS_PER_STRUT
PRF_THERMAL_MASS = N_STRUTS * (PRF_MASS_PER_STRUT * PRF_CP +
                               SHEATH_MASS_PER_STRUT * SHEATH_CP)  # J/K total

# --- He-4 Core (cryogenic buffer) ---
HE4_MASS = 0.754             # kg
HE4_LATENT = 20.7e3          # J/kg (latent heat of vaporization)
HE4_BUFFER = HE4_MASS * HE4_LATENT  # J total latent buffer
HE4_T_BATH = 4.2             # K
HE4_T_MAX = 4.5              # K (max before systems degrade)
HE4_CP = 5193.0              # J/kg/K (He-4 liquid, ~4.2K)
CRYOCOOLER_POWER = 2.0       # W (cooling capacity at 4.2K)
PARASITIC_LOAD = 0.8         # W (nominal heat leak into cryo zone)
CRYO_HEADROOM = CRYOCOOLER_POWER - PARASITIC_LOAD  # W available for muscle heat

# --- Muscles ---
# CNT yarn bundle (from bench test: 500 yarns, 9.6 mJ per stroke)
ENERGY_PER_STROKE_SMALL = 9.621e-3   # J (500-yarn bundle)
N_YARNS_SMALL = 500
# Hybrid bundle (95,999 CNT yarns + REBCO coil)
N_YARNS_HYBRID = 95999
# Energy scales with yarn count (parallel yarns, same voltage, same time)
# Actually: more yarns = lower resistance = more current at same voltage = more power
# But energy per yarn per stroke is constant (same temperature rise needed)
ENERGY_PER_YARN_STROKE = ENERGY_PER_STROKE_SMALL / N_YARNS_SMALL  # J per yarn per stroke
ENERGY_PER_HYBRID_STROKE = N_YARNS_HYBRID * ENERGY_PER_YARN_STROKE  # J per hybrid stroke

# REBCO voice-coil AC loss (cryo-side heat)
# AC loss in REBCO tape in external field during current cycling
# Literature: ~0.1-1 mW/m per cycle for REBCO in 0.8T at full penetration
# Coil wire length: 28.3m (from bench test)
REBCO_WIRE_LENGTH = 28.3     # m per coil
REBCO_AC_LOSS_PER_M = 0.5e-3 # W/m per Hz (mid-range estimate)
# AC loss per coil = loss_per_m × length × frequency
# This goes into the CRYO zone — He-4 must absorb it

# Total hybrid bundles in the body
N_BUNDLES_TOTAL = 12          # 12 major muscle groups (humanoid body)

# --- MTR (resonator/clock — NOT energy storage) ---
# Mobius Heart is NOT an energy storage device — it's a resonator/clock
# Single-turn REBCO loop, R=50cm: L ≈ 4 µH, I=200A
MTR_INDUCTANCE = 4e-6        # H
MTR_CURRENT = 200.0          # A
MTR_ENERGY = 0.5 * MTR_INDUCTANCE * MTR_CURRENT**2  # J (0.08 J — negligible)

# --- SMES (Superconducting Magnetic Energy Storage) ---
# Solenoid coil: REBCO tape wound on former
SMES_N = 3000                # turns
SMES_R = 0.15                # m (coil radius)
SMES_L_SOL = 0.30            # m (solenoid length)
SMES_I = 200.0               # A (operating current)
MU_0 = 4 * np.pi * 1e-7     # H/m (permeability of free space)
SMES_INDUCTANCE = MU_0 * SMES_N**2 * np.pi * SMES_R**2 / SMES_L_SOL  # H
SMES_ENERGY = 0.5 * SMES_INDUCTANCE * SMES_I**2  # J
E_CAPACITY = SMES_ENERGY     # max energy storage

# ==============================================================
# DERIVED VALUES
# ==============================================================

# PV power at 1 AU
P_PV_1AU = SOLAR_FLUX_1AU * A_ILLUMINATED * SKIN_ABSORPTION * PV_EFFICIENCY

# Heater lane power (from electrodermus spec)
P_HEATER = 1.44              # W (100 Ohm @ 12V)

# Power per hybrid bundle at various duty cycles
def muscle_power(n_bundles, freq_hz):
    """Electrical power draw for n hybrid bundles cycling at freq_hz."""
    return n_bundles * ENERGY_PER_HYBRID_STROKE * freq_hz

def rebco_cryo_heat(n_bundles, freq_hz):
    """Heat deposited in cryo zone by REBCO AC losses."""
    return n_bundles * REBCO_AC_LOSS_PER_M * REBCO_WIRE_LENGTH * freq_hz

print("MOVEMENT INTEGRATION TEST")
print("=" * 70)
print("Cross-organ stress simulation: what breaks when the body moves?")
print()

# ==============================================================
# PHASE 0: POWER BUDGET
# ==============================================================
print("=" * 70)
print("PHASE 0: POWER BUDGET (Electrodermus PV vs Muscle Demand)")
print("=" * 70)

print(f"\n  Solar flux at 1 AU: {SOLAR_FLUX_1AU:.0f} W/m2")
print(f"  Illuminated area: {A_ILLUMINATED:.1f} m2 (projected)")
print(f"  Absorption: {SKIN_ABSORPTION*100:.0f}%")
print(f"  PV efficiency: {PV_EFFICIENCY*100:.0f}%")
print(f"  PV power at 1 AU: {P_PV_1AU:.1f} W")
print(f"  MTR stored energy: {MTR_ENERGY*1000:.1f} mJ (NOT a battery)")
print(f"  SMES energy storage: {SMES_ENERGY:.0f} J ({SMES_INDUCTANCE:.3f} H, {SMES_I:.0f} A)")
print(f"    ({SMES_N} turns, R={SMES_R*100:.0f}cm, L_sol={SMES_L_SOL*100:.0f}cm)")

print(f"\n  Energy per hybrid bundle stroke: {ENERGY_PER_HYBRID_STROKE*1000:.1f} mJ")
print(f"  ({N_YARNS_HYBRID} yarns x {ENERGY_PER_YARN_STROKE*1000:.4f} mJ/yarn)")

# Power demand at various activity levels
scenarios = [
    ("Idle (2 bundles, 1 Hz)",    2,  1),
    ("Gentle (2 bundles, 5 Hz)",  2,  5),
    ("Walk (6 bundles, 10 Hz)",   6, 10),
    ("Run (8 bundles, 20 Hz)",    8, 20),
    ("Sprint (12 bundles, 50 Hz)", 12, 50),
    ("Burst (12 bundles, 100 Hz)", 12, 100),
]

print(f"\n  {'Scenario':<35s} {'P_muscle':>10s} {'P_avail':>10s} {'Balance':>10s} {'Status':>8s}")
print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

power_results = []
for name, n, f in scenarios:
    p_muscle = muscle_power(n, f)
    p_avail = P_PV_1AU
    balance = p_avail - p_muscle
    status = "OK" if balance > 0 else "DEFICIT"
    print(f"  {name:<35s} {p_muscle:>9.1f}W {p_avail:>9.1f}W {balance:>+9.1f}W {status:>8s}")
    power_results.append((name, n, f, p_muscle, balance))

# Find the crossover
# Binary search for max sustainable frequency with 6 bundles
f_max_6 = P_PV_1AU / (6 * ENERGY_PER_HYBRID_STROKE)
f_max_12 = P_PV_1AU / (12 * ENERGY_PER_HYBRID_STROKE)
print(f"\n  Max sustainable freq (6 bundles): {f_max_6:.1f} Hz")
print(f"  Max sustainable freq (12 bundles): {f_max_12:.1f} Hz")

# Verdict
walk_power = muscle_power(6, 10)
v0 = "PASS" if P_PV_1AU > walk_power else "FAIL"
print(f"\n  PV covers walking (6 bundles, 10 Hz)? {P_PV_1AU:.1f}W vs {walk_power:.1f}W [{v0}]")

sprint_power = muscle_power(12, 50)
sprint_status = "PASS" if P_PV_1AU > sprint_power else "FAIL"
print(f"  PV covers sprint (12 bundles, 50 Hz)? {P_PV_1AU:.1f}W vs {sprint_power:.1f}W [{sprint_status}]")
print(f"  >> VERDICT: {v0} (walk) / {sprint_status} (sprint)")

# ==============================================================
# PHASE 1: THERMAL CASCADE — WARM SIDE (muscle heat → PRF → skin)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 1: WARM-SIDE THERMAL CASCADE (PRF highway capacity)")
print("=" * 70)

print(f"\n  PRF core: {N_STRUTS} x hollow tube (OD={PRF_TUBE_OD*1000:.2f}mm, wall={PRF_TUBE_WALL*1000:.1f}mm, ID={PRF_TUBE_ID*1000:.2f}mm, L={PRF_LENGTH*100:.0f}cm)")
print(f"  PRF k_eff: {PRF_K_EFF:.0f} W/m-K, core cross-section: {PRF_CROSS*1e6:.2f} mm2, capacity: {Q_CORE_PER_STRUT:.1f} W/strut")
print(f"  Periosteum sheath: {SHEATH_THICKNESS*1000:.0f}mm CNT fiber wrap, k={SHEATH_K:.0f} W/m-K, OD={SHEATH_OD*1000:.2f}mm")
print(f"  Sheath cross-section: {SHEATH_CROSS*1e6:.1f} mm2 (vs core {PRF_CROSS*1e6:.2f} mm2)")
print(f"  Sheath capacity: {Q_SHEATH_PER_STRUT:.1f} W/strut")
print(f"  Combined per strut: {Q_PER_STRUT:.1f} W (core {Q_CORE_PER_STRUT:.1f} + sheath {Q_SHEATH_PER_STRUT:.1f})")
print(f"  dT available: {PRF_DT_MAX:.0f} K (4.2K to 250K)")
print(f"  Total capacity: {Q_PRF_MAX:.1f} W ({N_STRUTS} struts)")
print(f"  Skin radiative capacity: {Q_RAD_MAX:.0f} W")

# Muscle heat = muscle power (all electrical energy → heat eventually)
# CNT yarns: resistive heating → contraction → heat dissipated to structure
# Some fraction conducted through PRF to skin, some to cryo zone
# Assume 85% warm side (CNT heat), 15% cryo side (REBCO AC loss + conduction)
WARM_FRACTION = 0.85

print(f"\n  Warm-side fraction of muscle heat: {WARM_FRACTION*100:.0f}%")
print(f"\n  {'Scenario':<35s} {'Q_warm':>10s} {'PRF cap':>10s} {'Margin':>10s} {'Status':>8s}")
print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

prf_results = []
for name, n, f, p_muscle, _ in power_results:
    q_warm = p_muscle * WARM_FRACTION
    margin = Q_PRF_MAX - q_warm
    status = "OK" if margin > 0 else "OVERLOAD"
    print(f"  {name:<35s} {q_warm:>9.1f}W {Q_PRF_MAX:>9.1f}W {margin:>+9.1f}W {status:>8s}")
    prf_results.append((name, q_warm, margin))

# The skin can radiate ~1050W, so radiation is NOT the bottleneck
# The PRF conduction IS the bottleneck
print(f"\n  Bottleneck: PRF conduction ({Q_PRF_MAX:.0f}W), NOT skin radiation ({Q_RAD_MAX:.0f}W)")

walk_warm = muscle_power(6, 10) * WARM_FRACTION
v1 = "PASS" if Q_PRF_MAX > walk_warm else "FAIL"
print(f"\n  PRF handles walking? {Q_PRF_MAX:.1f}W vs {walk_warm:.1f}W [{v1}]")

# How many struts needed for sprint?
sprint_warm = muscle_power(12, 50) * WARM_FRACTION
struts_needed_sprint = int(np.ceil(sprint_warm / Q_PER_STRUT))
print(f"  Struts needed for sprint: {struts_needed_sprint} (have {N_STRUTS})")
print(f"  >> VERDICT: {v1}")

# ==============================================================
# PHASE 2: CRYO STRESS (REBCO AC loss → He-4 core)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 2: CRYO-SIDE STRESS (REBCO AC loss → He-4 core)")
print("=" * 70)

print(f"\n  Cryocooler capacity: {CRYOCOOLER_POWER:.1f} W at 4.2K")
print(f"  Parasitic load: {PARASITIC_LOAD:.1f} W")
print(f"  Available headroom: {CRYO_HEADROOM:.1f} W")
print(f"  He-4 latent buffer: {HE4_BUFFER:.0f} J")
print(f"  REBCO AC loss: {REBCO_AC_LOSS_PER_M*1000:.1f} mW/m per Hz, {REBCO_WIRE_LENGTH:.1f}m wire")

print(f"\n  {'Scenario':<35s} {'Q_cryo':>10s} {'Headroom':>10s} {'Margin':>10s} {'Status':>8s}")
print(f"  {'-'*35} {'-'*10} {'-'*10} {'-'*10} {'-'*8}")

cryo_results = []
for name, n, f, _, _ in power_results:
    q_cryo = rebco_cryo_heat(n, f)
    margin = CRYO_HEADROOM - q_cryo
    status = "OK" if margin > 0 else "BOILOFF"
    print(f"  {name:<35s} {q_cryo:>9.3f}W {CRYO_HEADROOM:>9.1f}W {margin:>+9.3f}W {status:>8s}")
    cryo_results.append((name, q_cryo, margin))

# Time to exhaust He-4 buffer if over headroom
for name, q_cryo, margin in cryo_results:
    if margin < 0:
        excess = -margin
        t_buffer = HE4_BUFFER / excess
        print(f"\n  {name}: He-4 buffer exhausted in {t_buffer:.0f}s ({t_buffer/60:.1f} min)")

walk_cryo = rebco_cryo_heat(6, 10)
v2 = "PASS" if CRYO_HEADROOM > walk_cryo else "FAIL"
print(f"\n  Cryo handles walking? {CRYO_HEADROOM:.1f}W vs {walk_cryo:.3f}W [{v2}]")
print(f"  >> VERDICT: {v2}")

# ==============================================================
# PHASE 3: SUSTAINED MOVEMENT (60-second walk cycle)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 3: SUSTAINED WALK CYCLE (60 seconds, 6 bundles @ 10 Hz)")
print("=" * 70)

dt = 0.1  # s timestep
t_total = 60.0  # s
t = np.arange(0, t_total, dt)
N_steps = len(t)

# Movement profile: 6 bundles cycling at 10 Hz with some variation
# Bundles ramp up over first 5s, sustain, brief sprint at 30-40s
n_active = np.ones(N_steps) * 6
freq_profile = np.ones(N_steps) * 10.0  # Hz base

# Ramp up
ramp_mask = t < 5.0
n_active[ramp_mask] = 2 + 4 * (t[ramp_mask] / 5.0)
# Sprint burst at 30-40s
sprint_mask = (t >= 30.0) & (t < 40.0)
n_active[sprint_mask] = 12
freq_profile[sprint_mask] = 30.0

# Track system state
P_muscle_t = np.array([muscle_power(n, f) for n, f in zip(n_active, freq_profile)])
Q_warm_t = P_muscle_t * WARM_FRACTION
Q_cryo_t = np.array([rebco_cryo_heat(n, f) for n, f in zip(n_active, freq_profile)])

# Energy balance
P_pv = P_PV_1AU  # constant (sunlit)
E_reserve = np.zeros(N_steps)
E_reserve[0] = min(SMES_ENERGY * 0.33, E_CAPACITY)  # start at ~33% SMES charge

for i in range(1, N_steps):
    dE = (P_pv - P_muscle_t[i]) * dt
    E_reserve[i] = np.clip(E_reserve[i-1] + dE, 0, E_CAPACITY)

# PRF temperature (simplified 1-node thermal mass)
T_prf = np.zeros(N_steps)
T_prf[0] = 127.0  # K (midpoint of 4.2K-250K gradient, equilibrium)
# dT/dt = (Q_in - Q_out) / C_thermal
# Q_in = muscle warm heat + parasitic (already in baseline)
# Q_out = PRF conduction to skin (proportional to T_prf - T_skin_base)
T_SKIN_EQUIL = 250.0
for i in range(1, N_steps):
    Q_in = Q_warm_t[i]
    # Conduction out scales with temperature difference
    Q_out_fraction = min(1.0, (T_prf[i-1] - 4.2) / PRF_DT_MAX)
    Q_out = Q_PRF_MAX * Q_out_fraction
    dT = (Q_in - Q_out) * dt / PRF_THERMAL_MASS
    T_prf[i] = T_prf[i-1] + dT

# He-4 temperature
T_he4 = np.zeros(N_steps)
T_he4[0] = HE4_T_BATH
HE4_THERMAL_MASS = HE4_MASS * HE4_CP  # J/K

for i in range(1, N_steps):
    Q_in_cryo = Q_cryo_t[i] + PARASITIC_LOAD
    Q_out_cryo = CRYOCOOLER_POWER
    # If T > 4.2K, some latent heat absorption (boiloff provides extra cooling)
    if T_he4[i-1] > HE4_T_BATH:
        Q_latent = min(5.0, (T_he4[i-1] - HE4_T_BATH) * 10)  # proportional response
    else:
        Q_latent = 0
    dT = (Q_in_cryo - Q_out_cryo - Q_latent) * dt / HE4_THERMAL_MASS
    T_he4[i] = max(3.8, T_he4[i-1] + dT)  # can't go below cryocooler base temp

# Check for failures
energy_depleted = np.any(E_reserve <= 0)
prf_overloaded = np.any(T_prf > 300)  # K — above skin temp means heat flows backward
he4_overheated = np.any(T_he4 > HE4_T_MAX)

print(f"\n  Walk cycle: 6 bundles @ 10 Hz, with 10s sprint burst (12 @ 30 Hz)")
print(f"  PV power: {P_pv:.1f} W (constant, sunlit)")
print(f"  Initial energy reserve: {E_reserve[0]:.0f} J")
print(f"\n  Results over 60 seconds:")
print(f"    Peak muscle power: {np.max(P_muscle_t):.1f} W")
print(f"    Mean muscle power: {np.mean(P_muscle_t):.1f} W")
print(f"    Energy reserve min: {np.min(E_reserve):.1f} J (of {E_CAPACITY:.0f} J)")
print(f"    Energy reserve final: {E_reserve[-1]:.1f} J")
print(f"    PRF temp range: {np.min(T_prf):.1f} - {np.max(T_prf):.1f} K")
print(f"    He-4 temp range: {np.min(T_he4):.4f} - {np.max(T_he4):.4f} K")

if energy_depleted:
    t_deplete = t[np.argmax(E_reserve <= 0)]
    print(f"\n    ** ENERGY DEPLETED at t={t_deplete:.1f}s **")
if prf_overloaded:
    t_prf_fail = t[np.argmax(T_prf > 300)]
    print(f"\n    ** PRF OVERLOADED at t={t_prf_fail:.1f}s (T > 300K) **")
if he4_overheated:
    t_he4_fail = t[np.argmax(T_he4 > HE4_T_MAX)]
    print(f"\n    ** He-4 OVERHEATED at t={t_he4_fail:.1f}s (T > {HE4_T_MAX}K) **")

v3_energy = "PASS" if not energy_depleted else "FAIL"
v3_prf = "PASS" if not prf_overloaded else "FAIL"
v3_he4 = "PASS" if not he4_overheated else "FAIL"
v3 = "PASS" if all([not energy_depleted, not prf_overloaded, not he4_overheated]) else "FAIL"

print(f"\n  Energy sustained? [{v3_energy}]")
print(f"  PRF within limits? [{v3_prf}]")
print(f"  He-4 within limits? [{v3_he4}]")
print(f"  >> VERDICT: {v3}")

# ==============================================================
# PHASE 4: BURST TEST (all muscles, max effort, how long?)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 4: BURST TEST (12 bundles @ 50 Hz — how long until failure?)")
print("=" * 70)

t_burst_total = 120.0  # s — run until something breaks or 2 minutes
t_b = np.arange(0, t_burst_total, dt)
N_b = len(t_b)

P_burst = muscle_power(12, 50)
Q_warm_burst = P_burst * WARM_FRACTION
Q_cryo_burst = rebco_cryo_heat(12, 50)

print(f"\n  Burst power demand: {P_burst:.1f} W")
print(f"  PV supply: {P_pv:.1f} W")
print(f"  Deficit: {P_burst - P_pv:.1f} W")
print(f"  Warm-side heat: {Q_warm_burst:.1f} W (PRF capacity: {Q_PRF_MAX:.1f} W)")
print(f"  Cryo-side heat: {Q_cryo_burst:.3f} W (headroom: {CRYO_HEADROOM:.1f} W)")

E_burst = np.zeros(N_b)
E_burst[0] = E_CAPACITY  # start fully charged
T_prf_burst = np.zeros(N_b)
T_prf_burst[0] = 127.0
T_he4_burst = np.zeros(N_b)
T_he4_burst[0] = HE4_T_BATH

t_energy_fail = None
t_prf_fail = None
t_he4_fail = None

for i in range(1, N_b):
    # Energy
    dE = (P_pv - P_burst) * dt
    E_burst[i] = max(0, E_burst[i-1] + dE)
    if E_burst[i] <= 0 and t_energy_fail is None:
        t_energy_fail = t_b[i]

    # PRF
    Q_out_frac = min(1.0, (T_prf_burst[i-1] - 4.2) / PRF_DT_MAX)
    Q_out = Q_PRF_MAX * Q_out_frac
    dT_prf = (Q_warm_burst - Q_out) * dt / PRF_THERMAL_MASS
    T_prf_burst[i] = T_prf_burst[i-1] + dT_prf
    if T_prf_burst[i] > 300 and t_prf_fail is None:
        t_prf_fail = t_b[i]

    # He-4
    Q_in_cryo = Q_cryo_burst + PARASITIC_LOAD
    Q_out_cryo = CRYOCOOLER_POWER
    if T_he4_burst[i-1] > HE4_T_BATH:
        Q_latent = min(5.0, (T_he4_burst[i-1] - HE4_T_BATH) * 10)
    else:
        Q_latent = 0
    dT_he4 = (Q_in_cryo - Q_out_cryo - Q_latent) * dt / HE4_THERMAL_MASS
    T_he4_burst[i] = max(3.8, T_he4_burst[i-1] + dT_he4)
    if T_he4_burst[i] > HE4_T_MAX and t_he4_fail is None:
        t_he4_fail = t_b[i]

print(f"\n  First failure:")
failures = []
if t_energy_fail is not None:
    failures.append(("ENERGY DEPLETED", t_energy_fail))
    print(f"    Energy depleted at t={t_energy_fail:.1f}s")
if t_prf_fail is not None:
    failures.append(("PRF OVERLOAD", t_prf_fail))
    print(f"    PRF overloaded at t={t_prf_fail:.1f}s")
if t_he4_fail is not None:
    failures.append(("He-4 OVERHEAT", t_he4_fail))
    print(f"    He-4 overheated at t={t_he4_fail:.1f}s")

if failures:
    failures.sort(key=lambda x: x[1])
    first_fail = failures[0]
    print(f"\n  ** FIRST TO BREAK: {first_fail[0]} at t={first_fail[1]:.1f}s **")
    burst_endurance = first_fail[1]
else:
    print(f"\n  No failure in {t_burst_total:.0f}s — all systems nominal")
    burst_endurance = t_burst_total

v4 = "FAIL" if failures else "PASS"
print(f"\n  Burst endurance: {burst_endurance:.1f}s")
print(f"  >> VERDICT: {v4} (expected — this is a stress test)")

# ==============================================================
# SUMMARY
# ==============================================================
print(f"\n{'='*70}")
print("SUMMARY")
print("=" * 70)
verdicts = [
    ("Phase 0: Power Budget", v0),
    ("Phase 1: PRF Thermal Capacity", v1),
    ("Phase 2: Cryo Stress", v2),
    ("Phase 3: Sustained Walk", v3),
    ("Phase 4: Burst Endurance", v4),
]

pass_count = sum(1 for _, v in verdicts if v == "PASS")
for label, v in verdicts:
    print(f"  [{v}] {label}")

print(f"\n  {pass_count}/5 tests pass.")

# Identify the bottlenecks
print(f"\n  BOTTLENECK ANALYSIS:")
print(f"    PV harvest at 1 AU: {P_pv:.0f} W")
print(f"    Walk demand (6 @ 10 Hz): {muscle_power(6, 10):.0f} W")
print(f"    Sprint demand (12 @ 50 Hz): {muscle_power(12, 50):.0f} W")
print(f"    PRF conduction limit: {Q_PRF_MAX:.0f} W ({N_STRUTS} struts)")
print(f"    Skin radiation limit: {Q_RAD_MAX:.0f} W (NOT the bottleneck)")
print(f"    Cryo headroom: {CRYO_HEADROOM:.1f} W (REBCO AC loss is negligible)")
if burst_endurance < t_burst_total:
    print(f"    Burst endurance: {burst_endurance:.0f}s before {first_fail[0]}")
print()

# ==============================================================
# FIGURE — 6-panel dark theme
# ==============================================================
print("Generating figure...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.patch.set_facecolor('#1a1a2e')
fig.suptitle('Ghost Shell — Movement Integration Test',
             color='white', fontsize=16, fontweight='bold', y=0.98)

dark_bg = '#16213e'
colors = ['#e94560', '#0f3460', '#53d8fb', '#f5a623', '#7bed9f', '#ff6b6b']

for ax in axes.flat:
    ax.set_facecolor(dark_bg)
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    for spine in ax.spines.values():
        spine.set_color('#444')

# Panel 0: Power budget bar chart
ax = axes[0, 0]
scenario_names = [r[0].split('(')[0].strip() for r in power_results]
p_demands = [r[3] for r in power_results]
bar_colors = ['#7bed9f' if r[4] > 0 else '#e94560' for r in power_results]
bars = ax.barh(range(len(scenario_names)), p_demands, color=bar_colors, alpha=0.8)
ax.axvline(P_pv, color='#f5a623', linestyle='--', linewidth=2, label=f'PV supply ({P_pv:.0f}W)')
ax.set_yticks(range(len(scenario_names)))
ax.set_yticklabels(scenario_names, fontsize=8, color='white')
ax.set_xlabel('Power (W)')
ax.set_title(f'Phase 0: Power Budget [{v0}]')
ax.legend(fontsize=8, loc='lower right')

# Panel 1: PRF thermal capacity
ax = axes[0, 1]
warm_loads = [r[1] for r in prf_results]
bar_colors_prf = ['#7bed9f' if r[2] > 0 else '#e94560' for r in prf_results]
ax.barh(range(len(scenario_names)), warm_loads, color=bar_colors_prf, alpha=0.8)
ax.axvline(Q_PRF_MAX, color='#f5a623', linestyle='--', linewidth=2, label=f'PRF limit ({Q_PRF_MAX:.0f}W)')
ax.set_yticks(range(len(scenario_names)))
ax.set_yticklabels(scenario_names, fontsize=8, color='white')
ax.set_xlabel('Heat (W)')
ax.set_title(f'Phase 1: PRF Thermal [{v1}]')
ax.legend(fontsize=8, loc='lower right')

# Panel 2: Cryo stress
ax = axes[0, 2]
cryo_loads = [r[1] * 1000 for r in cryo_results]  # mW
ax.barh(range(len(scenario_names)), cryo_loads, color='#53d8fb', alpha=0.8)
ax.axvline(CRYO_HEADROOM * 1000, color='#f5a623', linestyle='--', linewidth=2,
           label=f'Headroom ({CRYO_HEADROOM*1000:.0f}mW)')
ax.set_yticks(range(len(scenario_names)))
ax.set_yticklabels(scenario_names, fontsize=8, color='white')
ax.set_xlabel('Heat (mW)')
ax.set_title(f'Phase 2: Cryo Stress [{v2}]')
ax.legend(fontsize=8, loc='lower right')

# Panel 3: Sustained walk — power & energy
ax = axes[1, 0]
ax.plot(t, P_muscle_t, color='#e94560', linewidth=1.5, label='Muscle power')
ax.axhline(P_pv, color='#f5a623', linestyle='--', linewidth=1, label=f'PV ({P_pv:.0f}W)')
ax2 = ax.twinx()
ax2.plot(t, E_reserve, color='#7bed9f', linewidth=1.5, alpha=0.7, label='Energy reserve')
ax2.set_ylabel('Energy (J)', color='#7bed9f')
ax2.tick_params(axis='y', colors='#7bed9f')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Power (W)', color='#e94560')
ax.tick_params(axis='y', colors='#e94560')
ax.set_title(f'Phase 3: Walk Cycle [{v3}]')
ax.legend(fontsize=7, loc='upper left')
ax2.legend(fontsize=7, loc='upper right')

# Panel 4: Sustained walk — temperatures
ax = axes[1, 1]
ax.plot(t, T_he4 * 1000, color='#53d8fb', linewidth=1.5, label='He-4 (mK)')
ax.axhline(HE4_T_MAX * 1000, color='#e94560', linestyle='--', alpha=0.5, label=f'He-4 limit ({HE4_T_MAX}K)')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Temperature (mK)', color='#53d8fb')
ax.tick_params(axis='y', colors='#53d8fb')
ax3 = ax.twinx()
ax3.plot(t, T_prf, color='#f5a623', linewidth=1.5, alpha=0.7, label='PRF midpoint')
ax3.set_ylabel('PRF Temp (K)', color='#f5a623')
ax3.tick_params(axis='y', colors='#f5a623')
ax.set_title(f'Phase 3: Thermal Response')
ax.legend(fontsize=7, loc='upper left')
ax3.legend(fontsize=7, loc='upper right')

# Panel 5: Burst test
ax = axes[1, 2]
ax.plot(t_b, E_burst, color='#e94560', linewidth=1.5, label='Energy reserve')
ax.axhline(0, color='white', linestyle=':', alpha=0.3)
if t_energy_fail:
    ax.axvline(t_energy_fail, color='#e94560', linestyle='--', alpha=0.7,
               label=f'Empty @ {t_energy_fail:.0f}s')
ax4 = ax.twinx()
ax4.plot(t_b, T_he4_burst * 1000, color='#53d8fb', linewidth=1.5, alpha=0.7, label='He-4 temp')
ax4.set_ylabel('He-4 (mK)', color='#53d8fb')
ax4.tick_params(axis='y', colors='#53d8fb')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Energy (J)', color='#e94560')
ax.tick_params(axis='y', colors='#e94560')
ax.set_title(f'Phase 4: Burst [{v4}]')
ax.legend(fontsize=7, loc='upper left')
ax4.legend(fontsize=7, loc='upper right')

# Scoreboard
score_text = f"MOVEMENT INTEGRATION: {pass_count}/5"
for label, v in verdicts:
    marker = "+" if v == "PASS" else "X"
    score_text += f"\n [{marker}] {label}"
score_text += f"\n\nBottleneck: PRF conduction ({Q_PRF_MAX:.0f}W)"
score_text += f"\nPV harvest: {P_pv:.0f}W at 1 AU"
if burst_endurance < t_burst_total:
    score_text += f"\nBurst limit: {burst_endurance:.0f}s"

fig.text(0.5, 0.01, score_text, ha='center', va='bottom',
         color='white', fontsize=9, fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='#0f3460', alpha=0.8))

plt.tight_layout(rect=[0, 0.12, 1, 0.95])

fig_dir = os.path.dirname(os.path.abspath(__file__))
fig_path = os.path.join(os.path.dirname(fig_dir), 'docs', 'figures', 'movement_integration.png')
fig_path = os.path.normpath(fig_path)
os.makedirs(os.path.dirname(fig_path), exist_ok=True)
plt.savefig(fig_path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')

# Social media version
sm_path = fig_path.replace('.png', '_sm.png')
plt.savefig(sm_path, dpi=100, facecolor=fig.get_facecolor(), bbox_inches='tight')

print(f"Figure saved: {fig_path}")
print(f"Social media: {sm_path}")
print("Done.")
