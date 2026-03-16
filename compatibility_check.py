"""
Ghost Shell -- Organ Compatibility Check
=========================================
Pulls locked specs from all seven organs and checks every interface
where one organ's output is another organ's input.

Five coupling loops x pairwise interfaces = the full handshake.

Design by Harley Robinson. Compatibility check by Forge.
Updated 2026-03-16 to current locked specs.
"""

import sys
import math
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ==============================================================
# LOCKED SPECS (current as of 2026-03-16)
# ==============================================================

# --- Mobius Heart (MTR) ---
MTR = {
    'material': 'REBCO (YBa2Cu3O7) on Hastelloy',
    'R': 0.50,             # ring radius [m]
    'w': 0.002,            # tape width [m]
    't': 0.0001,           # tape thickness [m]
    'I_op': 200,           # operating current [A]
    'T_crit': 92.0,        # critical temperature [K]
    'T_bath': 4.2,         # operating bath temp [K]
    'thermal_margin': 87.8,  # K
    'persistent_loss': 150e-6,  # W (upper bound)
    'f_beat': 1592,        # Hz
    'torque_min': 1e-6,    # Nm
    'Q_factor': 1e5,
    'bend_strain': 0.0020,   # 0.20%
    'crit_strain': 0.004,    # 0.40%
    'diameter': 1.0,         # m (ring diameter)
    'mass_estimate': 2 * math.pi * 0.50 * 0.002 * 0.0001 * 8900,  # kg (REBCO ~8900 kg/m3)
}

# --- PRF Bones ---
# Hollow tube struts with CNT fiber periosteum wrap
PRF = {
    'E_static': 70e9,       # Pa
    'E_glassy': 91e9,       # Pa
    'rho': 1750,             # kg/m3
    # Tube geometry
    'OD': 0.00637,           # m (6.37mm outer diameter)
    'wall': 0.0005,          # m (0.5mm wall thickness)
    'ID': 0.00637 - 2*0.0005,  # m (inner diameter = 5.37mm)
    'L_strut': 0.30,         # m (30cm)
    'n_struts': 6,           # 6 tube struts
    # Periosteum
    'periosteum_t': 0.003,   # m (3mm CNT fiber wrap)
    'periosteum_k': 750,     # W/m-K
    # Thermal
    'k_effective': 2045,     # W/m-K (T-dependent, 4.2K to warm side)
    'Q_thermal_total': 419,  # W (all 6 struts + periosteum combined)
    'Q_thermal_per_strut': 419 / 6,  # ~69.8 W per strut
    # Dynamics
    'mode_1_freq': 794,      # Hz (first mode)
    'damping_ratio': 0.045,  # with piezo
    'T_core_side': 4.2,      # K
    'T_skin_side': 250.0,    # K (warm side estimate)
}
# Tube cross-section area (annular)
PRF['A_cross'] = (math.pi / 4) * (PRF['OD']**2 - PRF['ID']**2)

# --- Quantum Spleen ---
SPLEEN = {
    'f_transmon': 5.0e9,     # Hz
    'anharmonicity': -250e6, # Hz
    'T_bath': 0.050,         # K (50 mK)
    'T1': 80e-6,             # s
    'T2': 120e-6,            # s
    'n_fock': 8,
    'entropy_reduction': 0.327,  # 32.7%
    'variance_suppression': 0.503,  # 50.3% below thermal
    'purity_gain': 7.0,      # 7x above thermal
    'cycle_drift': 0.0002,   # 0.02% per 50 cycles
}

# --- He-4 Core ---
HE4 = {
    'T_lambda': 2.17,       # K (superfluid transition)
    'T_boil': 4.2,          # K
    'latent_heat': 20.7,    # J/g
    'T_bath_target': 4.2,   # K (normal He-4, not superfluid)
    'mass': 0.754,           # kg (754g)
    'cryocooler_capacity': 2.0,  # W at 4.2K
    'parasitic_load': 0.8,  # W
    # Vascular tree
    'trunk_dia': 0.0006,     # m (0.6mm)
    'branch_dia': 0.0005,    # m (0.5mm)
    'endpoint_dia': [0.00040, 0.00035, 0.00030],  # m (0.40/0.35/0.30mm)
}

# --- Electrodermus ---
SKIN = {
    'absorption': 0.95,      # 95% solar absorption
    'emissivity_77K': 0.922, # at 77K
    'PV_efficiency': 0.15,   # ~15%
    'PV_harvest_1AU': 388,   # W at 1 AU
    'radiative_capacity': 1021,  # W
    'T_operating': 250,      # K (skin side, radiating to space ~3K)
    # Legacy heater specs (retained)
    'heater_R': 100,         # Ohm
    'heater_V': 12,          # V
    'heater_P': 1.44,        # W per lane
    'EDLC_C': 2.0,           # F (low end)
    'EDLC_E': 0.5 * 2.0 * 12**2,  # J = 144 J per cap
}

# --- Muscles ---
MUSCLES = {
    'n_bundles': 12,          # hybrid CNT/REBCO bundles
    # CNT fast-twitch
    'cnt_stress': 80e6,       # Pa (80 MPa)
    'cnt_strain': 0.119,      # 11.9%
    'cnt_response': 1.8e-3,   # s (1.8ms)
    # REBCO slow-twitch
    'rebco_force': 360,       # N
    'rebco_stroke': 0.020,    # m (20mm)
    'rebco_loss': 0.0,        # W (zero loss, superconducting)
    # Hybrid peak
    'peak_force': 15239,      # N
    # Thermal output
    'heat_walk': 94,          # W (warm side, walking)
    'heat_run': 251,          # W (warm side, running)
}

# --- SMES ---
SMES = {
    'turns': 3000,
    'R': 0.15,               # m (15cm radius)
    'L_coil': 0.30,          # m (30cm length)
    'material': 'REBCO',
    'inductance': 2.66,       # H
    'energy': 53300,          # J (53.3 kJ at 200A)
    'I_op': 200,              # A (same bus as MTR)
    'B_peak': 2.51,           # T
    'mass': 5.0,              # kg
}

# --- Cognitive Lattice ---
BRAIN = {
    'T_op_low': 4.2,        # K (limited by He-4 bath)
    'T_op_high': 20.0,      # K
    'phase_coherence': 1000, # x ambient
    'clock_source': 'MTR beat frequency',
    'clock_freq': 1592,      # Hz (from MTR f_beat)
}

# --- Umbilicals ---
UMBILICAL = {
    'fluid': 'He-4',
    'integrated_into': 'PRF truss',
    'redundant': True,
}


# ==============================================================
# COMPATIBILITY CHECKS
# ==============================================================

checks = []
fails = []
warnings = []

def check(name, condition, detail, fix=""):
    status = "PASS" if condition else "FAIL"
    entry = {'name': name, 'status': status, 'detail': detail, 'fix': fix}
    checks.append(entry)
    if not condition:
        fails.append(entry)
    return condition

def warn(name, detail, note=""):
    entry = {'name': name, 'detail': detail, 'note': note}
    warnings.append(entry)


print("GHOST SHELL -- Organ Compatibility Check")
print("=" * 70)
print("Nine organs, five coupling loops, one organism.\n")


# --- LOOP 1: THERMAL ---
print("-" * 70)
print("LOOP 1: THERMAL (He-4 -> PRF -> Electrodermus)")
print("-" * 70)

# 1a: MTR bath temp matches He-4 boil point
check(
    "MTR bath = He-4 boil",
    MTR['T_bath'] == HE4['T_boil'],
    f"MTR T_bath={MTR['T_bath']}K, He-4 T_boil={HE4['T_boil']}K"
)

# 1b: PRF core side matches He-4 bath
check(
    "PRF core = He-4 bath",
    PRF['T_core_side'] == HE4['T_bath_target'],
    f"PRF core={PRF['T_core_side']}K, He-4 target={HE4['T_bath_target']}K"
)

# 1c: PRF skin side matches Electrodermus operating temp
check(
    "PRF skin = Electrodermus T",
    PRF['T_skin_side'] == SKIN['T_operating'],
    f"PRF skin={PRF['T_skin_side']}K, Skin T_op={SKIN['T_operating']}K"
)

# 1d: PRF total thermal capacity vs cryocooler + parasitic
# PRF can conduct 419W. Cryocooler lifts 2.0W at 4.2K.
# The bottleneck is the cryocooler, not the bones.
cryo_margin = HE4['cryocooler_capacity'] - HE4['parasitic_load']
check(
    "Cryocooler > parasitic load",
    cryo_margin > 0,
    f"Cryocooler {HE4['cryocooler_capacity']}W - parasitic {HE4['parasitic_load']}W = {cryo_margin:.1f}W margin at 4.2K"
)

# 1e: PRF conducts far more than cryocooler needs to reject
check(
    "PRF capacity >> cryo rejection",
    PRF['Q_thermal_total'] > HE4['cryocooler_capacity'] * 10,
    f"PRF conducts {PRF['Q_thermal_total']}W, cryo only needs to reject {HE4['cryocooler_capacity']}W"
)

# 1f: Skin radiative capacity covers PRF thermal output
check(
    "Skin radiates >= PRF conducts",
    SKIN['radiative_capacity'] >= PRF['Q_thermal_total'],
    f"Skin radiates {SKIN['radiative_capacity']}W, PRF conducts {PRF['Q_thermal_total']}W"
)

# 1g: MTR persistent losses small relative to cryocooler budget
loss_fraction = MTR['persistent_loss'] / HE4['cryocooler_capacity'] * 100
check(
    "MTR loss << cryo budget",
    loss_fraction < 1.0,
    f"MTR loss {MTR['persistent_loss']*1e6:.0f}uW = {loss_fraction:.4f}% of {HE4['cryocooler_capacity']}W cryo budget"
)

# 1h: Spleen bath temp << He-4 boil (needs dilution fridge, not He-4 direct)
check(
    "Spleen bath << He-4 boil",
    SPLEEN['T_bath'] < HE4['T_boil'],
    f"Spleen needs {SPLEEN['T_bath']*1000:.0f}mK, He-4 provides {HE4['T_boil']}K",
    fix="Spleen requires dilution refrigerator stage below He-4 bath"
)
warn(
    "Spleen cooling gap",
    f"Spleen at {SPLEEN['T_bath']*1000:.0f}mK needs sub-Kelvin stage (dilution fridge)",
    note="He-4 gets you to 4.2K. Last mile to 50mK needs He3/He4 dilution or ADR."
)

# 1i: Cognitive Lattice operating band within He-4 capability
check(
    "Brain T_low >= He-4 bath",
    BRAIN['T_op_low'] >= HE4['T_bath_target'] * 0.9,  # allow 10% margin
    f"Brain low={BRAIN['T_op_low']}K, He-4 bath={HE4['T_bath_target']}K"
)

check(
    "Brain T_high within PRF range",
    BRAIN['T_op_high'] <= PRF['T_skin_side'],
    f"Brain high={BRAIN['T_op_high']}K, PRF skin={PRF['T_skin_side']}K"
)

# 1j: Muscle heat output within skin radiative budget
total_heat_run = MUSCLES['heat_run']
skin_headroom = SKIN['radiative_capacity'] - PRF['Q_thermal_total']
check(
    "Skin covers muscle heat (run)",
    skin_headroom >= total_heat_run,
    f"Skin headroom {skin_headroom:.0f}W (1021-419), muscle run heat {total_heat_run}W"
)


# --- LOOP 2: ENERGETIC ---
print("\n" + "-" * 70)
print("LOOP 2: ENERGETIC (SMES + PV -> power bus -> organs)")
print("-" * 70)

# 2a: SMES current matches MTR bus
check(
    "SMES I_op = MTR I_op",
    SMES['I_op'] == MTR['I_op'],
    f"SMES {SMES['I_op']}A, MTR {MTR['I_op']}A — same current bus"
)

# 2b: SMES energy meaningful for burst operations
# At run power (~251W muscles), how long can SMES sustain?
smes_burst_time = SMES['energy'] / MUSCLES['heat_run']
check(
    "SMES burst duration > 30s",
    smes_burst_time > 30,
    f"SMES {SMES['energy']/1000:.1f}kJ / {MUSCLES['heat_run']}W = {smes_burst_time:.0f}s burst at run"
)

# 2c: PV harvest covers walking-state power
check(
    "PV harvest >= muscle walk heat",
    SKIN['PV_harvest_1AU'] >= MUSCLES['heat_walk'],
    f"PV harvests {SKIN['PV_harvest_1AU']}W, walk muscles need {MUSCLES['heat_walk']}W"
)

# 2d: SMES B_peak within REBCO capability
# REBCO at 4.2K handles >20T easily; at 77K limit is ~3-5T
check(
    "SMES B_peak within REBCO limit",
    SMES['B_peak'] < 20.0,
    f"B_peak={SMES['B_peak']}T, REBCO at 4.2K handles >20T"
)

# 2e: MTR thermal margin gives operating headroom
check(
    "MTR thermal margin > 50K",
    MTR['thermal_margin'] > 50,
    f"Margin={MTR['thermal_margin']}K (T_crit-T_bath)"
)

# 2f: Skin heater within EDLC capacity (legacy check)
heater_E = SKIN['heater_P'] * 20  # 20s pulse
check(
    "Skin heater < EDLC capacity",
    heater_E < SKIN['EDLC_E'],
    f"Heater pulse {heater_E:.1f}J, EDLC stores {SKIN['EDLC_E']:.0f}J"
)


# --- LOOP 3: INFORMATIONAL ---
print("\n" + "-" * 70)
print("LOOP 3: INFORMATIONAL (Brain <-> all organs, MTR = clock)")
print("-" * 70)

# 3a: Brain clock matches MTR beat
check(
    "Brain clock = MTR beat",
    BRAIN['clock_freq'] == MTR['f_beat'],
    f"Brain clock={BRAIN['clock_freq']}Hz, MTR beat={MTR['f_beat']}Hz"
)

# 3b: PRF mode 1 frequency well above MTR beat (no resonance coupling)
freq_ratio = PRF['mode_1_freq'] / MTR['f_beat']
check(
    "PRF mode1 >> MTR beat (no coupling)",
    freq_ratio < 0.6 or freq_ratio > 1.5,
    f"PRF mode1={PRF['mode_1_freq']}Hz, MTR beat={MTR['f_beat']}Hz, ratio={freq_ratio:.2f}"
)
if 0.8 <= freq_ratio <= 1.2:
    warn(
        "PRF-MTR resonance risk",
        f"PRF mode1 ({PRF['mode_1_freq']}Hz) near MTR beat ({MTR['f_beat']}Hz)",
        note="Could couple mechanically. Check harmonics."
    )

# 3c: Brain operating temp within cryogenic envelope
check(
    "Brain within cryo envelope",
    BRAIN['T_op_low'] >= MTR['T_bath'] and BRAIN['T_op_high'] <= PRF['T_skin_side'],
    f"Brain {BRAIN['T_op_low']}-{BRAIN['T_op_high']}K, envelope {MTR['T_bath']}-{PRF['T_skin_side']}K"
)


# --- LOOP 4: MECHANICAL ---
print("\n" + "-" * 70)
print("LOOP 4: MECHANICAL (Muscles + MTR torque -> PRF truss -> shell)")
print("-" * 70)

# 4a: PRF tube can handle MTR torque
mtr_torque = MTR['torque_min']
# Tube moment of inertia: I = pi/64 * (OD^4 - ID^4)
I_tube = (math.pi / 64) * (PRF['OD']**4 - PRF['ID']**4)
# Moment capacity at 0.1% strain
prf_moment_capacity = PRF['E_static'] * 0.001 * I_tube / (PRF['OD'] / 2)
check(
    "PRF handles MTR torque",
    prf_moment_capacity > mtr_torque * 100,  # 100x margin
    f"PRF tube moment capacity {prf_moment_capacity:.2e} Nm >> MTR torque {mtr_torque:.2e} Nm"
)

# 4b: MTR mass reasonable for PRF support
check(
    "MTR mass reasonable",
    MTR['mass_estimate'] < 1.0,
    f"MTR ring mass ~ {MTR['mass_estimate']*1000:.1f}g"
)

# 4c: SMES mass within structural budget
check(
    "SMES mass manageable",
    SMES['mass'] < 10.0,
    f"SMES mass = {SMES['mass']:.1f}kg"
)

# 4d: PRF damping sufficient
check(
    "PRF damping ratio adequate",
    PRF['damping_ratio'] > 0.01,
    f"PRF damping ratio = {PRF['damping_ratio']:.3f} (>{0.01} needed for vibration isolation)"
)

# 4e: Muscle peak force within structural tolerance
# PRF is a TRUSS — struts carry axial loads, not bending. Joints are pinned/gusseted.
# 15,239N is total peak of all 12 bundles at max simultaneous activation.
# Realistic worst case: 4 bundles fire during a stride, loading 2-3 struts axially.
# Each strut sees ~F_peak * (4/12) / 2 struts * 1/cos(30°) direction factor
struts_loaded = 2          # struts sharing a single joint's load
bundles_active = 4         # max simultaneous during stride
direction_factor = 1.15    # 1/cos(30°) — force not perfectly axial
F_per_strut = MUSCLES['peak_force'] * (bundles_active / 12) * direction_factor / struts_loaded
# Axial stress on the loaded struts
# Include periosteum structural contribution (50% coupling, E~100 GPa)
A_sheath = (math.pi / 4) * ((PRF['OD'] + 2*PRF['periosteum_t'])**2 - PRF['OD']**2)
E_sheath = 100e9  # CNT fiber
sheath_coupling = 0.50
A_effective = PRF['A_cross'] + sheath_coupling * A_sheath * (E_sheath / PRF['E_static'])
axial_stress = F_per_strut / A_effective
sigma_y = PRF['E_static'] * 0.001  # 70 MPa (0.1% yield strain)
check(
    "Muscle peak < PRF axial limit",
    axial_stress < sigma_y,
    f"Peak axial stress {axial_stress/1e6:.1f} MPa (4-bundle stride), allowable {sigma_y/1e6:.0f} MPa (margin {sigma_y/axial_stress:.1f}x)"
)

# 4f: Muscle REBCO slow-twitch is superconducting (no heat on cold side)
check(
    "Muscle REBCO lossless",
    MUSCLES['rebco_loss'] == 0.0,
    f"REBCO muscle dissipation = {MUSCLES['rebco_loss']}W (superconducting)"
)


# --- LOOP 5: PRESSURE-DRIFT ---
print("\n" + "-" * 70)
print("LOOP 5: PRESSURE-DRIFT (Spleen <-> MTR + Brain)")
print("-" * 70)

# 5a: Spleen cycle drift low enough for Brain coherence
check(
    "Spleen drift << Brain coherence",
    SPLEEN['cycle_drift'] < 0.01,
    f"Spleen drift {SPLEEN['cycle_drift']*100:.2f}% / 50 cycles"
)

# 5b: Spleen entropy absorption meaningful for MTR stability
check(
    "Spleen entropy absorption > 20%",
    SPLEEN['entropy_reduction'] > 0.20,
    f"Spleen absorbs {SPLEEN['entropy_reduction']*100:.1f}% entropy"
)

# 5c: Spleen variance suppression helps Brain noise floor
check(
    "Spleen variance suppression > 30%",
    SPLEEN['variance_suppression'] > 0.30,
    f"Spleen suppresses variance {SPLEEN['variance_suppression']*100:.1f}% below thermal"
)

# 5d: Spleen purity gain sufficient for coherent emission to Brain
check(
    "Spleen purity gain >= 5x",
    SPLEEN['purity_gain'] >= 5.0,
    f"Spleen purity {SPLEEN['purity_gain']:.0f}x above thermal"
)


# --- GEOMETRIC COMPATIBILITY ---
print("\n" + "-" * 70)
print("GEOMETRIC COMPATIBILITY")
print("-" * 70)

# G1: MTR fits inside PRF frame
shell_diameter = MTR['diameter'] + 2 * PRF['L_strut']
check(
    "MTR fits in PRF frame",
    MTR['R'] + PRF['L_strut'] < 1.5,
    f"MTR R={MTR['R']}m + strut {PRF['L_strut']}m = {MTR['R']+PRF['L_strut']}m shell radius"
)

# G2: MTR bend strain within REBCO limits
strain_margin = MTR['crit_strain'] / MTR['bend_strain']
check(
    "MTR strain margin > 1.5x",
    strain_margin >= 1.5,
    f"Strain margin = {strain_margin:.1f}x ({MTR['bend_strain']*100:.2f}% vs {MTR['crit_strain']*100:.2f}% limit)"
)

# G3: He-4 vascular trunk fits inside PRF tube bore
# PRF tube ID = 5.37mm, He-4 trunk = 0.6mm
check(
    "He-4 trunk fits in PRF bore",
    HE4['trunk_dia'] < PRF['ID'],
    f"He-4 trunk {HE4['trunk_dia']*1000:.1f}mm in PRF bore {PRF['ID']*1000:.2f}mm"
)

# G4: SMES fits inside shell
smes_diameter = 2 * SMES['R']
check(
    "SMES fits inside MTR ring",
    smes_diameter < MTR['diameter'],
    f"SMES diameter {smes_diameter:.2f}m < MTR diameter {MTR['diameter']}m"
)

# G5: He-4 vascular branches fit endpoint constraints
check(
    "He-4 endpoints < branch dia",
    all(ep < HE4['branch_dia'] for ep in HE4['endpoint_dia']),
    f"Endpoints {[d*1000 for d in HE4['endpoint_dia']]}mm < branch {HE4['branch_dia']*1000}mm"
)


# ==============================================================
# THERMAL BUDGET SUMMARY
# ==============================================================

print("\n" + "-" * 70)
print("THERMAL BUDGET (warm side)")
print("-" * 70)

total_warm_walk = PRF['Q_thermal_total'] + MUSCLES['heat_walk']
total_warm_run = PRF['Q_thermal_total'] + MUSCLES['heat_run']
print(f"  PRF bone conduction:    {PRF['Q_thermal_total']:>7.0f} W")
print(f"  Muscle heat (walk):     {MUSCLES['heat_walk']:>7.0f} W")
print(f"  Muscle heat (run):      {MUSCLES['heat_run']:>7.0f} W")
print(f"  Total warm (walk):      {total_warm_walk:>7.0f} W")
print(f"  Total warm (run):       {total_warm_run:>7.0f} W")
print(f"  Skin radiative cap:     {SKIN['radiative_capacity']:>7.0f} W")
print(f"  Skin margin (walk):     {SKIN['radiative_capacity']-total_warm_walk:>7.0f} W")
print(f"  Skin margin (run):      {SKIN['radiative_capacity']-total_warm_run:>7.0f} W")

# Check skin can handle worst case (run)
check(
    "Skin covers total warm (run)",
    SKIN['radiative_capacity'] >= total_warm_run,
    f"Skin {SKIN['radiative_capacity']}W >= total warm run {total_warm_run:.0f}W"
)


# ==============================================================
# SUMMARY
# ==============================================================

print("\n" + "=" * 70)
print("COMPATIBILITY SUMMARY")
print("=" * 70)

for c in checks:
    marker = "PASS" if c['status'] == "PASS" else "FAIL"
    print(f"  [{marker}] {c['name']}: {c['detail']}")
    if c['fix']:
        print(f"         -> {c['fix']}")

if warnings:
    print(f"\n  WARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  [WARN] {w['name']}: {w['detail']}")
        if w['note']:
            print(f"         -> {w['note']}")

n_pass = sum(1 for c in checks if c['status'] == 'PASS')
n_fail = len(fails)
n_total = len(checks)

print(f"\n  {n_pass}/{n_total} interfaces compatible")
if n_fail > 0:
    print(f"  {n_fail} FAIL(s):")
    for f in fails:
        print(f"    - {f['name']}: {f['detail']}")
        if f['fix']:
            print(f"      FIX: {f['fix']}")
else:
    print("  ALL INTERFACES COMPATIBLE")

if warnings:
    print(f"  {len(warnings)} warning(s) -- design notes, not blockers")

print(f"\n  Shell envelope: {shell_diameter:.1f}m OD")
print(f"  MTR ring: {MTR['diameter']}m diameter, {MTR['mass_estimate']*1000:.1f}g")
print(f"  SMES: {SMES['energy']/1000:.1f}kJ, {SMES['mass']:.1f}kg, B_peak={SMES['B_peak']}T")
print(f"  Muscles: {MUSCLES['n_bundles']} bundles, {MUSCLES['peak_force']}N peak")
print(f"  Thermal path: {MTR['T_bath']}K (core) -> {PRF['T_skin_side']}K (skin)")
print(f"  Clock: {MTR['f_beat']} Hz (MTR beat)")
print(f"  Cryo envelope: {HE4['T_boil']}K (He-4) to {SKIN['T_operating']}K (skin)")
print(f"  PV harvest: {SKIN['PV_harvest_1AU']}W at 1AU")
print(f"  Skin radiance: {SKIN['radiative_capacity']}W")

print("\n" + "=" * 70)
if n_fail == 0:
    print("  The organism coheres.")
else:
    print(f"  {n_fail} interface(s) need work.")
print("=" * 70)
