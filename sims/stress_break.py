"""
Stress Break Test — Find the Failure Envelope
==============================================
The movement integration passed at walking pace. Now push until
something shatters. Five scenarios designed to find the real limits.

Phase 0: Shadow Sprint — moving with no sunlight (orbital shadow)
Phase 1: Marathon — moderate activity for 8 hours. Cryo drift.
Phase 2: Resonance Hunt — muscle freq sweeps through PRF modes
Phase 3: Strut Failure — one PRF strut breaks. Can 5 carry the load?
Phase 4: Worst Day — shadow + running + damage. Combined stressors.

Design by Harley Robinson. Stress test by Forge.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ==============================================================
# SYSTEM PARAMETERS (from organ bench tests + integration)
# ==============================================================

SIGMA_SB = 5.670374419e-8

# Electrodermus PV
SOLAR_FLUX_1AU = 1361.0
A_ILLUMINATED = 2.0
SKIN_ABSORPTION = 0.95
PV_EFFICIENCY = 0.15
P_PV_1AU = SOLAR_FLUX_1AU * A_ILLUMINATED * SKIN_ABSORPTION * PV_EFFICIENCY  # 388W

# Skin radiation
A_SKIN = 5.0
T_SKIN = 250.0
T_SPACE = 3.0
SKIN_EMISSIVITY = 0.93
Q_RAD_MAX = SKIN_EMISSIVITY * SIGMA_SB * A_SKIN * (T_SKIN**4 - T_SPACE**4)

# PRF + Periosteum (per strut)
# REDESIGN: hollow tube instead of flat beam (same cross-sectional area)
# Tube pushes bending Mode 1 from ~72 Hz to well above 200 Hz
PRF_K_EFF = 2045.0
PRF_LENGTH = 0.30
PRF_DENSITY = 1750.0

# Hollow tube geometry (same area as old 10mm x 1mm flat beam = 10 mm^2)
PRF_TUBE_OD = 6.37e-3      # m (6.37 mm outer diameter)
PRF_TUBE_WALL = 0.5e-3     # m (0.5 mm wall thickness)
PRF_TUBE_ID = PRF_TUBE_OD - 2 * PRF_TUBE_WALL  # 5.37 mm
PRF_CROSS = np.pi / 4 * (PRF_TUBE_OD**2 - PRF_TUBE_ID**2)  # ~10 mm^2

# Periosteum sheath: 3mm CNT fiber wrap around tube
SHEATH_THICKNESS = 3.0e-3
SHEATH_K = 750.0
SHEATH_DENSITY = 1400.0
SHEATH_CP = 700.0
SHEATH_OD = PRF_TUBE_OD + 2 * SHEATH_THICKNESS  # 12.37 mm
SHEATH_CROSS = np.pi / 4 * (SHEATH_OD**2 - PRF_TUBE_OD**2)  # ~88 mm^2

# Thermal capacity
PRF_DT_MAX = 246.0
Q_CORE_PER_STRUT = PRF_K_EFF * PRF_CROSS * PRF_DT_MAX / PRF_LENGTH
Q_SHEATH_PER_STRUT = SHEATH_K * SHEATH_CROSS * PRF_DT_MAX / PRF_LENGTH
Q_PER_STRUT = Q_CORE_PER_STRUT + Q_SHEATH_PER_STRUT

# PRF thermal mass
PRF_CP = 700.0
PRF_MASS_STRUT = PRF_DENSITY * PRF_CROSS * PRF_LENGTH
SHEATH_MASS_STRUT = SHEATH_DENSITY * SHEATH_CROSS * PRF_LENGTH
THERMAL_MASS_PER_STRUT = PRF_MASS_STRUT * PRF_CP + SHEATH_MASS_STRUT * SHEATH_CP

# PRF mechanical resonance — HOLLOW TUBE
E_STATIC = 70e9
# Second moment of area: tube vs flat beam
# Flat was: I = bh^3/12 = 0.01 * 0.001^3 / 12 = 8.33e-13 m^4
# Tube:     I = pi/64 * (OD^4 - ID^4)
I_CORE = np.pi / 64 * (PRF_TUBE_OD**4 - PRF_TUBE_ID**4)

# Periosteum structural contribution (CNT fiber wrap under tension)
# E_sheath ~ 100 GPa (aligned CNT fiber, conservative)
# Contributes to bending stiffness but at reduced coupling (~50%)
E_SHEATH_STRUCT = 100e9
SHEATH_COUPLING = 0.50  # 50% structural contribution (wrapped fiber, not monolithic)
I_SHEATH = np.pi / 64 * (SHEATH_OD**4 - PRF_TUBE_OD**4)
EI_TOTAL = E_STATIC * I_CORE + SHEATH_COUPLING * E_SHEATH_STRUCT * I_SHEATH

# Effective mass per unit length (both core and sheath)
RHO_A_EFF = PRF_DENSITY * PRF_CROSS + SHEATH_DENSITY * SHEATH_CROSS

# Free-free bending modes: beta_L values
BETA_L = np.array([4.7300, 7.8532, 10.9956, 14.1372, 17.2788, 20.4204])
C_BEND = np.sqrt(EI_TOTAL / RHO_A_EFF)
F_MODES = (BETA_L**2) / (2 * np.pi * PRF_LENGTH**2) * C_BEND

# He-4
HE4_MASS = 0.754
HE4_LATENT = 20.7e3
HE4_BUFFER = HE4_MASS * HE4_LATENT
HE4_T_BATH = 4.2
HE4_T_MAX = 4.5
HE4_CP = 5193.0
CRYOCOOLER_POWER = 2.0
PARASITIC_LOAD = 0.8
CRYO_HEADROOM = CRYOCOOLER_POWER - PARASITIC_LOAD
HE4_THERMAL_MASS = HE4_MASS * HE4_CP

# Muscles
N_YARNS_SMALL = 500
ENERGY_PER_STROKE_SMALL = 9.621e-3
N_YARNS_HYBRID = 95999
ENERGY_PER_YARN = ENERGY_PER_STROKE_SMALL / N_YARNS_SMALL
ENERGY_PER_HYBRID = N_YARNS_HYBRID * ENERGY_PER_YARN
REBCO_WIRE_LENGTH = 28.3
REBCO_AC_LOSS_PER_M = 0.5e-3

WARM_FRACTION = 0.85
N_BUNDLES_TOTAL = 12

# Energy storage — SMES (Superconducting Magnetic Energy Storage)
# Dedicated REBCO solenoid coil, separate from MTR (MTR keeps clock/torque role)
# Located inside MTR ring (R=50cm), immersed in He-4 bath
# Wound as double-pancake coils: R=15cm former, 30cm long, 3000 turns
# REBCO tape: 2mm wide, 0.1mm thick. Ic = 500A at 4.2K self-field.
# B_peak ~ 2.5T at center — REBCO Ic still ~300A at this field. 200A is safe.
SMES_N_TURNS = 3000
SMES_RADIUS = 0.15          # m
SMES_LENGTH = 0.30           # m
SMES_CURRENT = 200.0         # A (same as MTR operating current)
MU_0 = 4 * np.pi * 1e-7
SMES_INDUCTANCE = MU_0 * SMES_N_TURNS**2 * np.pi * SMES_RADIUS**2 / SMES_LENGTH
SMES_ENERGY = 0.5 * SMES_INDUCTANCE * SMES_CURRENT**2  # J
SMES_B_PEAK = MU_0 * SMES_N_TURNS * SMES_CURRENT / SMES_LENGTH  # T

# SMES conductor: 3000 turns × 2π × 0.15m = 2827m of REBCO tape
# Mass: 2827m × 2mm × 0.1mm × 8900 kg/m³ ≈ 5 kg
SMES_TAPE_LENGTH = SMES_N_TURNS * 2 * np.pi * SMES_RADIUS
SMES_MASS = SMES_TAPE_LENGTH * 0.002 * 0.0001 * 8900  # kg

E_CAPACITY = SMES_ENERGY  # replaces the old 30s capacitor bank

def muscle_power(n, f):
    return n * ENERGY_PER_HYBRID * f

def cryo_heat(n, f):
    return n * REBCO_AC_LOSS_PER_M * REBCO_WIRE_LENGTH * f

# Baseline damping ratio and piezo-enhanced
ZETA_BASE = 0.005
ZETA_PIEZO = 0.045  # with piezo shunt

print("STRESS BREAK TEST (v2 — SMES + Tube Geometry)")
print("=" * 70)
print("Five scenarios. Two redesigns: SMES energy storage + hollow tube struts.\n")

print(f"  SMES coil: {SMES_N_TURNS} turns REBCO, R={SMES_RADIUS*100:.0f}cm, L={SMES_LENGTH*100:.0f}cm")
print(f"  SMES inductance: {SMES_INDUCTANCE:.2f} H")
print(f"  SMES energy: {SMES_ENERGY/1000:.1f} kJ at {SMES_CURRENT:.0f}A")
print(f"  SMES B_peak: {SMES_B_PEAK:.2f} T")
print(f"  SMES conductor: {SMES_TAPE_LENGTH:.0f}m REBCO tape, {SMES_MASS:.1f} kg")
print(f"  Shadow walk endurance: {SMES_ENERGY/muscle_power(6,10):.0f}s ({SMES_ENERGY/muscle_power(6,10)/60:.1f} min)")
print(f"  Shadow run endurance: {SMES_ENERGY/muscle_power(8,20):.0f}s ({SMES_ENERGY/muscle_power(8,20)/60:.1f} min)")
print(f"\n  PRF tube: OD={PRF_TUBE_OD*1000:.2f}mm, wall={PRF_TUBE_WALL*1000:.1f}mm, ID={PRF_TUBE_ID*1000:.2f}mm")
print(f"  Core area: {PRF_CROSS*1e6:.1f} mm2 (same as old flat beam)")
print(f"  Core I: {I_CORE:.3e} m4 (old flat: 8.33e-13 m4, ratio: {I_CORE/8.33e-13:.0f}x)")
print(f"  Periosteum I: {I_SHEATH:.3e} m4 (at {SHEATH_COUPLING*100:.0f}% coupling)")
print(f"  EI_total: {EI_TOTAL:.2f} N*m2")
print(f"  Sheath area: {SHEATH_CROSS*1e6:.1f} mm2")
print(f"  Thermal per strut: {Q_PER_STRUT:.1f} W (core {Q_CORE_PER_STRUT:.1f} + sheath {Q_SHEATH_PER_STRUT:.1f})")
print(f"  Mode 1: {F_MODES[0]:.1f} Hz (old: 72.2 Hz)")
print()

# ==============================================================
# PHASE 0: SHADOW SPRINT
# ==============================================================
print("=" * 70)
print("PHASE 0: SHADOW SPRINT (full activity, no sunlight)")
print("=" * 70)

# Orbital shadow: body enters eclipse. PV drops to zero.
# Already moving at walk pace. Ramps to run. No power income.
dt = 0.1
t_max = 300.0  # 5 minutes
t = np.arange(0, t_max, dt)
N = len(t)

# Movement profile: walking when shadow hits, ramps to run at t=30s
n_active_0 = np.ones(N) * 6
freq_0 = np.ones(N) * 10.0
# Ramp to run at t=30
ramp = (t >= 30) & (t < 35)
n_active_0[ramp] = 6 + 2 * (t[ramp] - 30) / 5
n_active_0[t >= 35] = 8
freq_0[t >= 35] = 20.0

P_muscle_0 = np.array([muscle_power(n, f) for n, f in zip(n_active_0, freq_0)])
Q_warm_0 = P_muscle_0 * WARM_FRACTION
Q_cryo_0 = np.array([cryo_heat(n, f) for n, f in zip(n_active_0, freq_0)])

# PV = 0 (shadow)
E_reserve_0 = np.zeros(N)
E_reserve_0[0] = E_CAPACITY  # start fully charged

# PRF thermal
n_struts_0 = 6
Q_prf_cap_0 = n_struts_0 * Q_PER_STRUT
thermal_mass_0 = n_struts_0 * THERMAL_MASS_PER_STRUT
T_prf_0 = np.zeros(N)
T_prf_0[0] = 127.0

# He-4
T_he4_0 = np.zeros(N)
T_he4_0[0] = HE4_T_BATH
he4_boiloff_0 = np.zeros(N)  # cumulative kg boiled

t_energy_fail_0 = None
t_prf_fail_0 = None
t_he4_fail_0 = None

for i in range(1, N):
    # Energy: no PV
    dE = -P_muscle_0[i] * dt
    E_reserve_0[i] = max(0, E_reserve_0[i-1] + dE)
    if E_reserve_0[i] <= 0 and t_energy_fail_0 is None:
        t_energy_fail_0 = t[i]

    # PRF
    Q_out_frac = min(1.0, max(0, (T_prf_0[i-1] - 4.2) / PRF_DT_MAX))
    Q_out = Q_prf_cap_0 * Q_out_frac
    dT = (Q_warm_0[i] - Q_out) * dt / thermal_mass_0
    T_prf_0[i] = T_prf_0[i-1] + dT
    if T_prf_0[i] > 300 and t_prf_fail_0 is None:
        t_prf_fail_0 = t[i]

    # He-4
    Q_in_c = Q_cryo_0[i] + PARASITIC_LOAD
    Q_out_c = CRYOCOOLER_POWER
    net_cryo = Q_in_c - Q_out_c
    if net_cryo > 0:
        # Excess heat boils He-4
        dm = net_cryo * dt / HE4_LATENT
        he4_boiloff_0[i] = he4_boiloff_0[i-1] + dm
    else:
        he4_boiloff_0[i] = he4_boiloff_0[i-1]
    # Temperature rises slightly when boiloff exceeds buffer
    if he4_boiloff_0[i] >= HE4_MASS:
        T_he4_0[i] = HE4_T_MAX + 1  # total boiloff = catastrophic
        if t_he4_fail_0 is None:
            t_he4_fail_0 = t[i]
    else:
        frac_remaining = 1 - he4_boiloff_0[i] / HE4_MASS
        T_he4_0[i] = HE4_T_BATH + 0.01 * (1 - frac_remaining)

print(f"\n  Scenario: Walking in shadow, ramp to run at t=30s")
print(f"  PV power: 0 W (eclipse)")
print(f"  Initial reserve: {E_CAPACITY:.0f} J")
print(f"  Walk demand: {muscle_power(6, 10):.0f} W, Run demand: {muscle_power(8, 20):.0f} W")

failures_0 = []
if t_energy_fail_0:
    failures_0.append(("ENERGY DEPLETED", t_energy_fail_0))
    print(f"\n  ** ENERGY DEPLETED at t={t_energy_fail_0:.1f}s **")
    print(f"     Walk phase consumed {muscle_power(6, 10) * min(30, t_energy_fail_0):.0f} J")
if t_prf_fail_0:
    failures_0.append(("PRF OVERLOAD", t_prf_fail_0))
    print(f"  ** PRF OVERLOADED at t={t_prf_fail_0:.1f}s **")
if t_he4_fail_0:
    failures_0.append(("He-4 TOTAL BOILOFF", t_he4_fail_0))
    print(f"  ** He-4 TOTAL BOILOFF at t={t_he4_fail_0:.1f}s **")

print(f"\n  He-4 boiloff at end: {he4_boiloff_0[-1]*1000:.1f} g of {HE4_MASS*1000:.0f} g ({he4_boiloff_0[-1]/HE4_MASS*100:.1f}%)")

if failures_0:
    failures_0.sort(key=lambda x: x[1])
    first = failures_0[0]
    print(f"  FIRST BREAK: {first[0]} at t={first[1]:.1f}s")
    v0 = "FAIL"
else:
    print(f"  No failure in {t_max:.0f}s")
    v0 = "PASS"
print(f"  >> VERDICT: {v0}")

# ==============================================================
# PHASE 1: MARATHON (8 hours moderate activity)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 1: MARATHON (6 bundles @ 10 Hz for 8 hours, sunlit)")
print("=" * 70)

# 8 hours = 28800 seconds. Too many timesteps at dt=0.1, use dt=1.0
dt_m = 1.0
t_marathon = 8 * 3600  # 28800 s
t_m = np.arange(0, t_marathon, dt_m)
N_m = len(t_m)

P_walk = muscle_power(6, 10)
Q_cryo_walk = cryo_heat(6, 10)

# He-4 cryo balance over 8 hours
# cryo_heat at walk = 0.849 W, headroom = 1.2 W → margin 0.351 W
# But this is continuous — does it slowly drift?
he4_boiloff_m = np.zeros(N_m)
T_he4_m = np.zeros(N_m)
T_he4_m[0] = HE4_T_BATH

# Energy: PV covers walk easily (388W vs 111W)
E_reserve_m = np.zeros(N_m)
E_reserve_m[0] = E_CAPACITY

# Add intermittent sprint bursts every 30 minutes (terrain changes)
for i in range(1, N_m):
    t_sec = t_m[i]
    # Sprint burst for 60s every 1800s
    in_sprint = (t_sec % 1800) < 60
    if in_sprint:
        n_act = 8
        f_act = 20.0
    else:
        n_act = 6
        f_act = 10.0

    p_mus = muscle_power(n_act, f_act)
    q_cryo = cryo_heat(n_act, f_act)

    # Energy
    dE = (P_PV_1AU - p_mus) * dt_m
    E_reserve_m[i] = np.clip(E_reserve_m[i-1] + dE, 0, E_CAPACITY)

    # He-4
    Q_in_c = q_cryo + PARASITIC_LOAD
    Q_out_c = CRYOCOOLER_POWER
    net = Q_in_c - Q_out_c
    if net > 0:
        dm = net * dt_m / HE4_LATENT
        he4_boiloff_m[i] = he4_boiloff_m[i-1] + dm
    else:
        # Cryocooler can recondense if below capacity
        # Recondense rate limited by cryocooler
        dm_recondense = min(he4_boiloff_m[i-1], (-net) * dt_m / HE4_LATENT)
        he4_boiloff_m[i] = he4_boiloff_m[i-1] - dm_recondense

    frac_left = max(0, 1 - he4_boiloff_m[i] / HE4_MASS)
    T_he4_m[i] = HE4_T_BATH + 0.3 * (1 - frac_left)**2  # mild drift

print(f"\n  Walk: {P_walk:.0f} W, Sprint bursts: {muscle_power(8,20):.0f} W (60s every 30 min)")
print(f"  PV supply: {P_PV_1AU:.0f} W (sunlit)")
print(f"  Cryo load (walk): {Q_cryo_walk:.3f} W, headroom: {CRYO_HEADROOM:.1f} W")
print(f"  Cryo load (sprint): {cryo_heat(8,20):.3f} W")

total_boiloff = he4_boiloff_m[-1]
peak_boiloff = np.max(he4_boiloff_m)
print(f"\n  He-4 boiloff after 8 hours: {total_boiloff*1000:.1f} g of {HE4_MASS*1000:.0f} g ({total_boiloff/HE4_MASS*100:.2f}%)")
print(f"  Peak boiloff: {peak_boiloff*1000:.1f} g ({peak_boiloff/HE4_MASS*100:.2f}%)")
print(f"  He-4 temp at end: {T_he4_m[-1]*1000:.1f} mK")
print(f"  Energy reserve final: {E_reserve_m[-1]:.0f} J (min: {np.min(E_reserve_m):.0f} J)")

# Does the boiloff accumulate dangerously?
he4_critical = total_boiloff / HE4_MASS > 0.50  # >50% loss is critical
v1 = "FAIL" if he4_critical else "PASS"
if he4_critical:
    # Find when 50% is reached
    t_50 = t_m[np.argmax(he4_boiloff_m / HE4_MASS > 0.50)]
    print(f"\n  ** He-4 50% BOILOFF at t={t_50/3600:.1f} hours **")
print(f"  >> VERDICT: {v1}")

# ==============================================================
# PHASE 2: RESONANCE HUNT
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 2: RESONANCE HUNT (muscle freq sweeps through PRF modes)")
print("=" * 70)

print(f"\n  PRF bending modes:")
for i, f in enumerate(F_MODES):
    print(f"    Mode {i+1}: {f:.1f} Hz")

# Muscle force transmission to struts:
# Muscles don't bolt directly to struts — they attach through tendons
# (non-actuating CNT rope). The tendon has compliance that acts as a
# mechanical low-pass filter, attenuating high-frequency force ripple.
#
# Force path: Muscle bundle → Tendon → Strut attachment point
#
# The AC component at the strut depends on:
#   1. Bundle firing pattern: 96k yarns don't fire simultaneously in
#      a coordinated system — staggered firing reduces ripple
#   2. Tendon compliance: spring-like coupling filters the pulse shape
#   3. Antagonist cancellation: opposing muscle pairs absorb each other's ripple
#   4. Multi-point attachment: force distributed across attachment area
#
# Model: tendon as 2nd-order low-pass with natural frequency f_tendon
# For CNT rope tendon (k~50,000 N/m, m_eff~0.1 kg): f_tendon ≈ 112 Hz
# Above f_tendon, force transmission drops as 1/f^2

F_muscle = 15239.0  # N peak (from bench test)

# AC ripple at muscle output: ~5% of peak from pulsed firing
F_AC_MUSCLE = F_muscle * 0.05  # 762 N at muscle

# Tendon filter
# CNT rope tendons: stiff fiber bundle with significant internal friction
# under cyclic loading. Hysteresis in yarn-to-yarn sliding dissipates energy.
# Damping ratio 0.3-0.7 for multi-strand CNT fiber (higher than steel cable).
TENDON_K = 50000.0      # N/m (stiff CNT rope, ~5cm length)
TENDON_M = 0.10         # kg (effective mass at attachment)
F_TENDON = np.sqrt(TENDON_K / TENDON_M) / (2 * np.pi)  # ~112 Hz
TENDON_ZETA = 0.50      # CNT fiber rope — high internal friction from yarn sliding

# Antagonist cancellation: opposing muscle absorbs ~60% of ripple
ANTAGONIST_FACTOR = 0.40  # 40% of ripple survives

# Sweep muscle frequency from 1 to 1000 Hz (wider range to see Mode 1)
f_sweep = np.linspace(1, 1000, 2000)

# Force transmitted through tendon at each frequency
def tendon_filter(f, f_n, zeta):
    """2nd-order low-pass transfer function magnitude."""
    r = f / f_n
    return 1.0 / np.sqrt((1 - r**2)**2 + (2 * zeta * r)**2)

F_AC_at_strut = np.array([F_AC_MUSCLE * ANTAGONIST_FACTOR * tendon_filter(f, F_TENDON, TENDON_ZETA)
                          for f in f_sweep])

# Structural response: sum of modal contributions
# x_total = sum_modes F_AC / (k_mode * sqrt((1-r^2)^2 + (2*zeta*r)^2))
# where r = f/f_mode, k_mode = omega_n^2 * m_eff

# Effective modal mass (core + sheath per unit length × length × modal factor)
m_strut = RHO_A_EFF * PRF_LENGTH  # total strut mass (core + sheath)
m_eff = m_strut * 0.5  # effective modal mass (roughly half for bending)

# Compute vibration amplitude at each sweep frequency
vib_amplitude = np.zeros(len(f_sweep))
vib_amplitude_bare = np.zeros(len(f_sweep))  # without piezo damping

for j, f in enumerate(f_sweep):
    F_at_strut = F_AC_at_strut[j]
    for f_mode in F_MODES:
        omega_n = 2 * np.pi * f_mode
        k_mode = omega_n**2 * m_eff
        r = f / f_mode
        # With piezo
        H = 1.0 / np.sqrt((1 - r**2)**2 + (2 * ZETA_PIEZO * r)**2)
        vib_amplitude[j] += F_at_strut * H / k_mode
        # Bare (no piezo)
        H_bare = 1.0 / np.sqrt((1 - r**2)**2 + (2 * ZETA_BASE * r)**2)
        vib_amplitude_bare[j] += F_at_strut * H_bare / k_mode

# Convert to microns
vib_um = vib_amplitude * 1e6
vib_um_bare = vib_amplitude_bare * 1e6

# Critical threshold for mid-span strut vibration
# He-4 capillaries run ALONG struts in grooves — they move WITH the strut,
# not relative to it. Vibration doesn't pinch them.
# Joint fatigue depends on strain (tiny for bending), not displacement.
# The real limit is photonic waveguide coupling at strut ends (low displacement)
# and differential motion between struts at shared nodes.
# 1mm (1000 um) is conservative for a body-scale structure during movement.
# For comparison: biological bone deflects several mm during walking.
VIB_LIMIT = 1000.0  # um (1 mm)

peak_vib = np.max(vib_um)
peak_vib_bare = np.max(vib_um_bare)
peak_f = f_sweep[np.argmax(vib_um)]
peak_f_bare = f_sweep[np.argmax(vib_um_bare)]

print(f"\n  Muscle AC ripple (at source): {F_AC_MUSCLE:.0f} N")
print(f"  Tendon filter: f_n = {F_TENDON:.0f} Hz, zeta = {TENDON_ZETA}")
print(f"  Antagonist cancellation: {(1-ANTAGONIST_FACTOR)*100:.0f}%")
print(f"  AC force at strut (10 Hz walk): {F_AC_at_strut[np.argmin(np.abs(f_sweep-10))]:.1f} N")
print(f"  AC force at strut (100 Hz):     {F_AC_at_strut[np.argmin(np.abs(f_sweep-100))]:.1f} N")
print(f"  AC force at strut (200 Hz):     {F_AC_at_strut[np.argmin(np.abs(f_sweep-200))]:.1f} N")
print(f"  Damping: zeta = {ZETA_PIEZO:.3f} (with piezo), {ZETA_BASE:.3f} (bare)")
print(f"\n  WITH piezo damping:")
print(f"    Peak vibration: {peak_vib:.1f} um at {peak_f:.1f} Hz")
print(f"    vs limit: {VIB_LIMIT:.0f} um")
print(f"  WITHOUT piezo damping:")
print(f"    Peak vibration: {peak_vib_bare:.1f} um at {peak_f_bare:.1f} Hz")
print(f"    vs limit: {VIB_LIMIT:.0f} um")

resonance_danger = peak_vib > VIB_LIMIT
resonance_bare_danger = peak_vib_bare > VIB_LIMIT

if resonance_danger:
    # Find dangerous frequency bands
    danger_mask = vib_um > VIB_LIMIT
    danger_bands = f_sweep[danger_mask]
    if len(danger_bands) > 0:
        print(f"\n  ** RESONANCE DANGER: {danger_bands[0]:.0f}-{danger_bands[-1]:.0f} Hz exceeds {VIB_LIMIT:.0f} um **")
        # Check if danger is in the muscle operating band (1-200 Hz)
        danger_in_band = danger_bands[danger_bands <= 200]
        if len(danger_in_band) > 0:
            print(f"     {len(danger_in_band)} dangerous frequencies in muscle band (1-200 Hz)")
        else:
            print(f"     All danger above 200 Hz — outside muscle operating band")

if resonance_bare_danger and not resonance_danger:
    print(f"\n  Piezo damping SAVES the system — bare struts would hit {peak_vib_bare:.0f} um")

# Key safety check: is Mode 1 above the muscle operating band?
MUSCLE_BAND_MAX = 200.0  # Hz
mode1_safe = F_MODES[0] > MUSCLE_BAND_MAX
print(f"\n  Mode 1 ({F_MODES[0]:.0f} Hz) above muscle band ({MUSCLE_BAND_MAX:.0f} Hz)? {'YES' if mode1_safe else 'NO'}")

# Quasi-static deflection at walking frequency (beam formula)
F_walk_strut = F_AC_at_strut[np.argmin(np.abs(f_sweep - 10))]
delta_static = F_walk_strut * PRF_LENGTH**3 / (48 * EI_TOTAL)
print(f"  Quasi-static deflection at 10 Hz walk: {delta_static*1e6:.0f} um ({delta_static*1e3:.2f} mm)")

v2 = "FAIL" if (resonance_danger or not mode1_safe) else "PASS"
print(f"  >> VERDICT: {v2}")

# ==============================================================
# PHASE 3: STRUT FAILURE (lose one PRF strut)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 3: STRUT FAILURE (5 remaining struts, walking)")
print("=" * 70)

# One strut snaps. Can the remaining 5 handle walking thermal load?
n_struts_3 = 5
Q_prf_cap_3 = n_struts_3 * Q_PER_STRUT
thermal_mass_3 = n_struts_3 * THERMAL_MASS_PER_STRUT

print(f"\n  Struts remaining: {n_struts_3} (lost 1)")
print(f"  Thermal capacity: {Q_prf_cap_3:.1f} W (was {6*Q_PER_STRUT:.1f} W)")

# Walk for 5 minutes on 5 struts
dt_3 = 0.1
t_3 = np.arange(0, 300, dt_3)
N_3 = len(t_3)

Q_walk_warm = muscle_power(6, 10) * WARM_FRACTION
T_prf_3 = np.zeros(N_3)
T_prf_3[0] = 127.0

for i in range(1, N_3):
    Q_out_frac = min(1.0, max(0, (T_prf_3[i-1] - 4.2) / PRF_DT_MAX))
    Q_out = Q_prf_cap_3 * Q_out_frac
    dT = (Q_walk_warm - Q_out) * dt_3 / thermal_mass_3
    T_prf_3[i] = T_prf_3[i-1] + dT

prf_3_max = np.max(T_prf_3)
prf_3_stable = T_prf_3[-1] < 300

print(f"  Walk heat load: {Q_walk_warm:.1f} W")
print(f"  PRF temp after 5 min: {T_prf_3[-1]:.1f} K (limit 300K)")
print(f"  PRF temp peak: {prf_3_max:.1f} K")

# Can it run?
Q_run_warm = muscle_power(8, 20) * WARM_FRACTION
print(f"\n  Run heat load: {Q_run_warm:.1f} W (capacity {Q_prf_cap_3:.1f} W)")
run_ok = Q_run_warm < Q_prf_cap_3
print(f"  5 struts handle running? {'YES' if run_ok else 'NO'}")

# Can it handle 25W baseline?
print(f"  5 struts handle 25W baseline? {'YES' if Q_prf_cap_3 > 25 else 'NO'}")

# What about 2 struts lost?
n_struts_4 = 4
Q_prf_cap_4 = n_struts_4 * Q_PER_STRUT
print(f"\n  With 2 struts lost ({n_struts_4} remaining): {Q_prf_cap_4:.1f} W capacity")
print(f"    Walk? {'YES' if Q_prf_cap_4 > Q_walk_warm else 'NO'} ({Q_walk_warm:.0f}W needed)")
print(f"    Run?  {'YES' if Q_prf_cap_4 > Q_run_warm else 'NO'} ({Q_run_warm:.0f}W needed)")

# 3 struts lost?
n_struts_half = 3
Q_prf_cap_half = n_struts_half * Q_PER_STRUT
print(f"\n  With 3 struts lost ({n_struts_half} remaining): {Q_prf_cap_half:.1f} W capacity")
print(f"    Walk? {'YES' if Q_prf_cap_half > Q_walk_warm else 'NO'} ({Q_walk_warm:.0f}W needed)")
print(f"    Idle? {'YES' if Q_prf_cap_half > 25 else 'NO'} (25W baseline)")

v3 = "PASS" if prf_3_stable else "FAIL"
print(f"\n  Walking on 5 struts: stable at {T_prf_3[-1]:.1f} K [{v3}]")
print(f"  >> VERDICT: {v3}")

# ==============================================================
# PHASE 4: WORST DAY (shadow + running + strut damage)
# ==============================================================
print(f"\n{'='*70}")
print("PHASE 4: WORST DAY (shadow + running + 1 strut lost)")
print("=" * 70)

# Combined: No PV, running pace, one strut down
dt_4 = 0.1
t_4_max = 300.0
t_4 = np.arange(0, t_4_max, dt_4)
N_4 = len(t_4)

n_act_4 = 8
freq_4 = 20.0
P_run = muscle_power(n_act_4, freq_4)
Q_warm_4 = P_run * WARM_FRACTION
Q_cryo_4 = cryo_heat(n_act_4, freq_4)
n_struts_4_wd = 5  # one lost
Q_prf_cap_4_wd = n_struts_4_wd * Q_PER_STRUT
thermal_mass_4 = n_struts_4_wd * THERMAL_MASS_PER_STRUT

print(f"\n  Conditions: no PV, running (8 @ 20 Hz), 5 struts")
print(f"  Power demand: {P_run:.0f} W (from reserves only)")
print(f"  Warm-side heat: {Q_warm_4:.0f} W (capacity: {Q_prf_cap_4_wd:.0f} W)")
print(f"  Cryo heat: {Q_cryo_4:.3f} W (headroom: {CRYO_HEADROOM:.1f} W)")

E_reserve_4 = np.zeros(N_4)
E_reserve_4[0] = E_CAPACITY
T_prf_4 = np.zeros(N_4)
T_prf_4[0] = 127.0
T_he4_4 = np.zeros(N_4)
T_he4_4[0] = HE4_T_BATH
he4_boiloff_4 = np.zeros(N_4)

t_fail_energy_4 = None
t_fail_prf_4 = None
t_fail_he4_4 = None

for i in range(1, N_4):
    # Energy: no PV
    E_reserve_4[i] = max(0, E_reserve_4[i-1] - P_run * dt_4)
    if E_reserve_4[i] <= 0 and t_fail_energy_4 is None:
        t_fail_energy_4 = t_4[i]

    # PRF (5 struts)
    Q_out_frac = min(1.0, max(0, (T_prf_4[i-1] - 4.2) / PRF_DT_MAX))
    Q_out = Q_prf_cap_4_wd * Q_out_frac
    dT = (Q_warm_4 - Q_out) * dt_4 / thermal_mass_4
    T_prf_4[i] = T_prf_4[i-1] + dT
    if T_prf_4[i] > 300 and t_fail_prf_4 is None:
        t_fail_prf_4 = t_4[i]

    # He-4
    Q_in_c = Q_cryo_4 + PARASITIC_LOAD
    net_cryo = Q_in_c - CRYOCOOLER_POWER
    if net_cryo > 0:
        dm = net_cryo * dt_4 / HE4_LATENT
        he4_boiloff_4[i] = he4_boiloff_4[i-1] + dm
    else:
        he4_boiloff_4[i] = he4_boiloff_4[i-1]
    if he4_boiloff_4[i] >= HE4_MASS and t_fail_he4_4 is None:
        t_fail_he4_4 = t_4[i]

failures_4 = []
if t_fail_energy_4:
    failures_4.append(("ENERGY DEPLETED", t_fail_energy_4))
    print(f"\n  ** ENERGY DEPLETED at t={t_fail_energy_4:.1f}s **")
if t_fail_prf_4:
    failures_4.append(("PRF OVERLOAD", t_fail_prf_4))
    print(f"  ** PRF OVERLOADED at t={t_fail_prf_4:.1f}s **")
if t_fail_he4_4:
    failures_4.append(("He-4 BOILOFF", t_fail_he4_4))
    print(f"  ** He-4 BOILOFF at t={t_fail_he4_4:.1f}s **")

if failures_4:
    failures_4.sort(key=lambda x: x[1])
    first_4 = failures_4[0]
    print(f"\n  FIRST BREAK: {first_4[0]} at t={first_4[1]:.1f}s")
    # What if it drops to walk when reserves hit 50%?
    half_energy_t = E_CAPACITY * 0.5 / P_run
    print(f"\n  Survival strategy: drop to walk when reserves < 50%")
    print(f"    Time to 50% reserves: {half_energy_t:.1f}s")
    walk_drain = muscle_power(6, 10)
    remaining_time = (E_CAPACITY * 0.5) / walk_drain
    print(f"    Walk on remaining 50%: {remaining_time:.0f}s ({remaining_time/60:.1f} min)")
    total_survival = half_energy_t + remaining_time
    print(f"    Total shadow survival: {total_survival:.0f}s ({total_survival/60:.1f} min)")

v4 = "FAIL" if failures_4 else "PASS"
print(f"  >> VERDICT: {v4}")

# ==============================================================
# SUMMARY
# ==============================================================
print(f"\n{'='*70}")
print("SUMMARY — FAILURE ENVELOPE")
print("=" * 70)

verdicts = [
    ("Phase 0: Shadow Sprint", v0),
    ("Phase 1: Marathon", v1),
    ("Phase 2: Resonance Hunt", v2),
    ("Phase 3: Strut Failure", v3),
    ("Phase 4: Worst Day", v4),
]

pass_count = sum(1 for _, v in verdicts if v == "PASS")
for label, v in verdicts:
    print(f"  [{v}] {label}")

print(f"\n  {pass_count}/5 survive.")

print(f"\n  FAILURE ENVELOPE:")
print(f"    SMES energy: {SMES_ENERGY/1000:.1f} kJ ({SMES_INDUCTANCE:.2f} H, {SMES_CURRENT:.0f}A, {SMES_MASS:.1f} kg)")
print(f"    Shadow endurance (walk): {E_CAPACITY / muscle_power(6,10):.0f}s ({E_CAPACITY/muscle_power(6,10)/60:.1f} min)")
print(f"    Shadow endurance (run):  {E_CAPACITY / muscle_power(8,20):.0f}s ({E_CAPACITY/muscle_power(8,20)/60:.1f} min)")
print(f"    Max sustained power (sunlit): {P_PV_1AU:.0f} W ({P_PV_1AU/ENERGY_PER_HYBRID:.1f} Hz on 6 bundles)")
print(f"    PRF tube Mode 1: {F_MODES[0]:.0f} Hz (old flat beam: 72 Hz)")
print(f"    PRF capacity (6 struts): {6*Q_PER_STRUT:.0f} W")
print(f"    PRF capacity (5 struts): {5*Q_PER_STRUT:.0f} W")
print(f"    Cryo headroom: {CRYO_HEADROOM:.1f} W (walk uses {cryo_heat(6,10):.2f}W)")
print(f"    Marathon cryo drift: {'SAFE' if not he4_critical else 'DANGEROUS'}")
if not resonance_danger:
    print(f"    Resonance: tube geometry + piezo keeps vibration to {peak_vib:.0f} um (limit {VIB_LIMIT:.0f})")
    if resonance_bare_danger:
        print(f"    WITHOUT piezo: {peak_vib_bare:.0f} um — still needs damping")
print()

# ==============================================================
# FIGURE — 6-panel dark theme
# ==============================================================
print("Generating figure...")

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.patch.set_facecolor('#1a1a2e')
fig.suptitle('Ghost Shell — Stress Break Test v2 (SMES + Tube Geometry)',
             color='white', fontsize=16, fontweight='bold', y=0.98)

dark_bg = '#16213e'

for ax in axes.flat:
    ax.set_facecolor(dark_bg)
    ax.tick_params(colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    for spine in ax.spines.values():
        spine.set_color('#444')

# Panel 0: Shadow Sprint — energy drain
ax = axes[0, 0]
ax.plot(t, E_reserve_0, color='#e94560', linewidth=2, label='Energy reserve')
ax.axhline(0, color='white', linestyle=':', alpha=0.3)
if t_energy_fail_0:
    ax.axvline(t_energy_fail_0, color='#f5a623', linestyle='--',
               label=f'Empty @ {t_energy_fail_0:.0f}s')
ax2 = ax.twinx()
ax2.plot(t, P_muscle_0, color='#53d8fb', linewidth=1, alpha=0.7, label='Power demand')
ax2.set_ylabel('Power (W)', color='#53d8fb')
ax2.tick_params(axis='y', colors='#53d8fb')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Energy (J)', color='#e94560')
ax.tick_params(axis='y', colors='#e94560')
vc0 = '#e94560' if v0 == 'FAIL' else '#7bed9f'
ax.set_title(f'Phase 0: Shadow Sprint [{v0}]', color=vc0)
ax.legend(fontsize=7, loc='center left')
ax2.legend(fontsize=7, loc='center right')

# Panel 1: Marathon — He-4 boiloff over 8 hours
ax = axes[0, 1]
ax.plot(t_m / 3600, he4_boiloff_m * 1000, color='#53d8fb', linewidth=2)
ax.axhline(HE4_MASS * 1000 * 0.5, color='#e94560', linestyle='--', alpha=0.5, label='50% loss')
ax.set_xlabel('Time (hours)')
ax.set_ylabel('He-4 boiloff (g)', color='#53d8fb')
ax.tick_params(axis='y', colors='#53d8fb')
ax3 = ax.twinx()
ax3.plot(t_m / 3600, E_reserve_m, color='#7bed9f', linewidth=1, alpha=0.7, label='Energy')
ax3.set_ylabel('Energy (J)', color='#7bed9f')
ax3.tick_params(axis='y', colors='#7bed9f')
vc1 = '#e94560' if v1 == 'FAIL' else '#7bed9f'
ax.set_title(f'Phase 1: Marathon [{v1}]', color=vc1)
ax.legend(fontsize=7, loc='upper left')
ax3.legend(fontsize=7, loc='lower right')

# Panel 2: Resonance Hunt
ax = axes[0, 2]
ax.semilogy(f_sweep, vib_um_bare, color='#e94560', linewidth=1, alpha=0.5, label='Bare (no piezo)')
ax.semilogy(f_sweep, vib_um, color='#7bed9f', linewidth=2, label='With piezo')
ax.axhline(VIB_LIMIT, color='#f5a623', linestyle='--', label=f'Limit ({VIB_LIMIT:.0f} um)')
for i, f_mode in enumerate(F_MODES):
    ax.axvline(f_mode, color='#53d8fb', linestyle=':', alpha=0.3)
    if i < 3:
        ax.text(f_mode + 5, np.max(vib_um) * 0.5, f'M{i+1}', color='#53d8fb', fontsize=7)
ax.set_xlabel('Muscle firing freq (Hz)')
ax.set_ylabel('Vibration amplitude (um)')
vc2 = '#e94560' if v2 == 'FAIL' else '#7bed9f'
ax.set_title(f'Phase 2: Resonance Hunt [{v2}]', color=vc2)
ax.legend(fontsize=7, loc='upper right')

# Panel 3: Strut failure — PRF temp
ax = axes[1, 0]
ax.plot(t_3, T_prf_3, color='#f5a623', linewidth=2, label='5 struts, walking')
ax.axhline(300, color='#e94560', linestyle='--', alpha=0.5, label='Limit (300K)')
ax.set_xlabel('Time (s)')
ax.set_ylabel('PRF Temperature (K)')
vc3 = '#e94560' if v3 == 'FAIL' else '#7bed9f'
ax.set_title(f'Phase 3: Strut Failure [{v3}]', color=vc3)
ax.legend(fontsize=7)

# Panel 4: Worst Day — triple threat
ax = axes[1, 1]
ax.plot(t_4, E_reserve_4, color='#e94560', linewidth=2, label='Energy')
if t_fail_energy_4:
    ax.axvline(t_fail_energy_4, color='#e94560', linestyle='--', alpha=0.5)
ax4 = ax.twinx()
ax4.plot(t_4, T_prf_4, color='#f5a623', linewidth=1.5, alpha=0.7, label='PRF temp')
ax4.axhline(300, color='#f5a623', linestyle=':', alpha=0.3)
ax4.set_ylabel('PRF Temp (K)', color='#f5a623')
ax4.tick_params(axis='y', colors='#f5a623')
ax.set_xlabel('Time (s)')
ax.set_ylabel('Energy (J)', color='#e94560')
ax.tick_params(axis='y', colors='#e94560')
vc4 = '#e94560' if v4 == 'FAIL' else '#7bed9f'
ax.set_title(f'Phase 4: Worst Day [{v4}]', color=vc4)
ax.legend(fontsize=7, loc='center left')
ax4.legend(fontsize=7, loc='center right')

# Panel 5: Scoreboard
ax = axes[1, 2]
ax.axis('off')
ax.text(0.5, 0.92, 'STRESS BREAK TEST', color='white', fontsize=16,
        fontweight='bold', ha='center', transform=ax.transAxes)

for i, (label, v) in enumerate(verdicts):
    y = 0.75 - i * 0.12
    color = '#7bed9f' if v == 'PASS' else '#e94560'
    ax.text(0.05, y, label, color='#ccc', fontsize=11, transform=ax.transAxes)
    ax.text(0.90, y, v, color=color, fontsize=12, fontweight='bold',
            ha='center', transform=ax.transAxes)

msg = f'{pass_count}/5 SURVIVE'
mc = '#7bed9f' if pass_count >= 4 else '#e94560'
ax.text(0.5, 0.10, msg, color=mc, fontsize=18,
        fontweight='bold', ha='center', transform=ax.transAxes)

plt.tight_layout(rect=[0, 0.02, 1, 0.95])

fig_path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          '..', 'docs', 'figures', 'stress_break.png'))
os.makedirs(os.path.dirname(fig_path), exist_ok=True)
plt.savefig(fig_path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
sm_path = fig_path.replace('.png', '_sm.png')
plt.savefig(sm_path, dpi=100, facecolor=fig.get_facecolor(), bbox_inches='tight')
plt.close()

print(f"Figure saved: {fig_path}")
print(f"Social media: {sm_path}")
print("Done.")
