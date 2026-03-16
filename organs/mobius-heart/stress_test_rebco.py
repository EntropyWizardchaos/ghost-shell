"""
MTR Stress Test v2 -- REBCO Redesign
======================================
The Little Black Dress found one fatal wound: NbTi bend strain at R=5cm.
This is the redesign. Switch to REBCO HTS tape, find the minimum viable radius.

Changes from v1:
  - Material: REBCO (YBa2Cu3O7) on Hastelloy substrate
  - T_crit: 92K (vs 9.2K for NbTi) -- massive thermal margin
  - Tape: 4mm wide x 0.1mm thick (vs 10mm x 1mm NbTi)
  - Radius: 25cm (vs 5cm) -- 5x larger but still benchtop-scale
  - Current: 200A (REBCO at 4K handles this easily)
  - Strain limit: 0.4% (conservative REBCO on Hastelloy)

Same six attacks. No mercy.

Design by Harley Robinson. Redesigned by Forge.
"""

import numpy as np
import matplotlib.pyplot as plt

# ==============================================================
# CONSTANTS
# ==============================================================

MU_0 = 4 * np.pi * 1e-7      # vacuum permeability [H/m]
RHO_CU = 1.7e-8              # copper resistivity at 300K [Ohm*m]
RHO_CU_CRYO = 2e-9           # copper at 4K (RRR~10) [Ohm*m]
C_LIGHT = 3e8                # speed of light [m/s]
k_B = 1.38e-23               # Boltzmann constant [J/K]

# REBCO material properties
REBCO_CRIT_STRAIN = 0.004    # 0.4% conservative (irreversible limit on Hastelloy)
REBCO_CRIT_STRAIN_HI = 0.007 # 0.7% optimistic (some tapes achieve this)
REBCO_JC_4K = 30e9           # critical current density at 4.2K, self-field [A/m^2]
REBCO_JC_77K = 3e9           # critical current density at 77K [A/m^2]
REBCO_T_CRIT = 92.0          # critical temperature [K]

# NbTi for comparison
NBTI_CRIT_STRAIN = 0.005
NBTI_T_CRIT = 9.2

# ==============================================================
# DESIGN CONFIGURATIONS
# ==============================================================

# Original design (FATAL at attack 3)
ORIGINAL = {
    'name': 'Original NbTi (R=5cm)',
    'R': 0.05,                # 5 cm
    'w': 0.01,                # strip half-width 10 mm -> w=10mm
    't': 0.001,               # 1 mm thick
    'I': 100,                 # 100 A
    'B_ext': 0.1,             # 0.1 T external field
    'v_ion': 10000,           # 10 km/s
    'T_bath': 4.2,            # He-4 bath
    'T_crit': NBTI_T_CRIT,
    'crit_strain': NBTI_CRIT_STRAIN,
    'crit_strain_hi': 0.01,
    'Jc': 3e9,               # NbTi Jc
    'd_filament': 50e-6,      # NbTi filament diameter
    'yield_strength': 800e6,  # NbTi yield [Pa]
    'material': 'NbTi',
}

# REBCO narrow tape (previous winner)
REBCO_NARROW = {
    'name': 'REBCO narrow (R=50cm, w=2mm)',
    'R': 0.50,                # 50 cm
    'w': 0.002,               # 2 mm narrow tape
    't': 0.0001,              # 0.1 mm
    'I': 200,                 # 200 A
    'B_ext': 0.1,
    'v_ion': 10000,
    'T_bath': 4.2,
    'T_crit': REBCO_T_CRIT,
    'crit_strain': REBCO_CRIT_STRAIN,
    'crit_strain_hi': REBCO_CRIT_STRAIN_HI,
    'Jc': REBCO_JC_4K,
    'd_filament': 1e-6,
    'yield_strength': 900e6,
    'material': 'REBCO',
}

# REBCO wide tape -- Harley's suggestion: make the track wider
REBCO = {
    'name': 'REBCO wide (R=1.5m, w=12mm)',
    'R': 1.50,                # 1.5 m -- 3m diameter, needs a table not a benchtop
    'w': 0.012,               # 12 mm standard wide REBCO tape
    't': 0.0001,              # 0.1 mm
    'I': 500,                 # 500 A (wide tape handles much more current)
    'B_ext': 0.1,
    'v_ion': 10000,
    'T_bath': 4.2,
    'T_crit': REBCO_T_CRIT,
    'crit_strain': REBCO_CRIT_STRAIN,
    'crit_strain_hi': REBCO_CRIT_STRAIN_HI,
    'Jc': REBCO_JC_4K,
    'd_filament': 1e-6,
    'yield_strength': 900e6,
    'material': 'REBCO',
}


def compute_derived(p):
    """Add derived quantities to parameter dict."""
    p = dict(p)
    p['circumference'] = 2 * np.pi * p['R']
    p['A_cross'] = 2 * p['w'] * p['t']  # cross-sectional area
    p['f_circ'] = p['v_ion'] / (2 * np.pi * p['R'])  # circulation frequency
    p['f_beat'] = p['f_circ'] / 2  # beat = half circulation
    # Inductance (single-turn loop)
    a_eff = np.sqrt(p['w'] * p['t'] / np.pi)
    p['L_ind'] = MU_0 * p['R'] * (np.log(8 * p['R'] / a_eff) - 2)
    return p


# ==============================================================
# ATTACK 1: SELF-FIELD LORENTZ FORCE
# ==============================================================

def attack_lorentz(p):
    R, w, t, I = p['R'], p['w'], p['t'], p['I']

    B_self = MU_0 * I / (2 * np.pi * w)
    J = I / p['A_cross']
    f_lorentz = J * B_self
    stress_hoop = f_lorentz * t  # stress = force_density * thickness
    twist_factor = 1.8
    stress_twist = stress_hoop * twist_factor

    margin = p['yield_strength'] / stress_twist

    verdict = "SURVIVES" if margin > 10 else ("VULNERABLE" if margin > 2 else "FATAL")

    print(f"\n{'='*70}")
    print(f"ATTACK 1: LORENTZ FORCE  [{p['material']}]")
    print(f"{'='*70}")
    print(f"  Self-field:        {B_self*1e3:.2f} mT")
    print(f"  Current density:   {J/1e6:.1f} MA/m^2")
    print(f"  Stress at twist:   {stress_twist:.1f} Pa")
    print(f"  Yield margin:      {margin:.0f}x")
    print(f"  >> VERDICT: {verdict}")

    return {'margin': margin, 'verdict': verdict, 'B_self': B_self}


# ==============================================================
# ATTACK 2: COPPER SIGNAL DEATH (Phase 0)
# ==============================================================

def attack_copper(p):
    R, w, t, I = p['R'], p['w'], p['t'], p['I']

    # For Phase 0, we use copper regardless of SC material
    # But geometry changes affect R_cu and L
    R_cu_300K = RHO_CU * p['circumference'] / p['A_cross']
    R_cu_4K = RHO_CU_CRYO * p['circumference'] / p['A_cross']

    tau_300K = p['L_ind'] / R_cu_300K
    tau_4K = p['L_ind'] / R_cu_4K
    f_beat = p['f_beat']

    n_300K = tau_300K * f_beat
    n_4K = tau_4K * f_beat

    # Pickup signal
    d_pickup = 0.02
    A_pickup = 1e-4
    M = MU_0 * A_pickup / (4 * np.pi * d_pickup)
    V_peak = M * I * 2 * np.pi * f_beat
    V_noise_300K = np.sqrt(4 * k_B * 300 * 1.0 * f_beat)
    V_noise_4K = np.sqrt(4 * k_B * 4.2 * 1.0 * f_beat)
    SNR_300K = V_peak / V_noise_300K
    SNR_4K = V_peak / V_noise_4K

    v_300K = "SURVIVES" if n_300K >= 10 else ("VULNERABLE" if n_300K >= 1 else "FATAL")
    v_4K = "SURVIVES" if n_4K >= 10 else "VULNERABLE"

    print(f"\n{'='*70}")
    print(f"ATTACK 2: COPPER SIGNAL DEATH  [{p['material']}]")
    print(f"{'='*70}")
    print(f"  Beat frequency:        {f_beat:.1f} Hz")
    print(f"  Strip R (300K):        {R_cu_300K*1e3:.3f} mOhm")
    print(f"  Strip R (4K):          {R_cu_4K*1e3:.4f} mOhm")
    print(f"  Inductance:            {p['L_ind']*1e6:.2f} uH")
    print(f"  tau (300K):            {tau_300K*1e6:.1f} us")
    print(f"  tau (4K):              {tau_4K*1e3:.2f} ms")
    print(f"  Cycles/e (300K):       {n_300K:.1f}")
    print(f"  Cycles/e (4K):         {n_4K:.0f}")
    print(f"  SNR initial (300K):    {SNR_300K:.0f}")
    print(f"  SNR initial (4K):      {SNR_4K:.0f}")
    print(f"  >> 300K: {v_300K}   4K: {v_4K}")

    # Note: larger R means HIGHER resistance (longer strip) but also HIGHER inductance
    # and LOWER beat frequency. The balance changes.
    if n_300K < n_4K:
        note = f"Phase 0 at 4K: {n_4K:.0f} cycles. "
        if p['R'] > 0.1:
            note += "Larger loop = more inductance = longer decay, but lower f_beat."
    else:
        note = f"Room temp works: {n_300K:.0f} cycles."
    print(f"  >> NOTE: {note}")

    return {'n_300K': n_300K, 'n_4K': n_4K, 'f_beat': f_beat,
            'verdict_300K': v_300K, 'verdict_4K': v_4K,
            'tau_300K': tau_300K, 'tau_4K': tau_4K}


# ==============================================================
# ATTACK 3: CRITICAL BEND STRAIN
# ==============================================================

def attack_strain(p):
    R, w, t = p['R'], p['w'], p['t']

    eps_loop = t / (2 * R)
    twist_rate = np.pi / (2 * np.pi * R)  # rad/m
    eps_twist = w * twist_rate
    eps_total = np.sqrt(eps_loop**2 + eps_twist**2)

    crit = p['crit_strain']
    crit_hi = p['crit_strain_hi']

    R_min_cons = np.sqrt(t**2 + w**2) / (2 * crit)
    R_min_opt = np.sqrt(t**2 + w**2) / (2 * crit_hi)

    margin = crit / eps_total

    if R > R_min_cons:
        verdict = "SURVIVES"
    elif R > R_min_opt:
        verdict = "VULNERABLE"
    else:
        verdict = "FATAL"

    print(f"\n{'='*70}")
    print(f"ATTACK 3: BEND STRAIN  [{p['material']}]")
    print(f"{'='*70}")
    print(f"  Loop bending strain:   {eps_loop*100:.4f}%")
    print(f"  Twist torsional strain:{eps_twist*100:.4f}%")
    print(f"  Total strain:          {eps_total*100:.4f}%")
    print(f"  Critical strain:       {crit*100:.1f}% (conserv) / {crit_hi*100:.1f}% (optim)")
    print(f"  Strain margin:         {margin:.2f}x")
    print(f"  Min radius (conserv):  {R_min_cons*100:.1f} cm")
    print(f"  Min radius (optim):    {R_min_opt*100:.1f} cm")
    print(f"  Design radius:         {R*100:.1f} cm")
    print(f"  >> VERDICT: {verdict}")

    if verdict == "SURVIVES":
        headroom = (1 - eps_total/crit) * 100
        print(f"  >> {headroom:.0f}% headroom below critical strain.")
        print(f"  >> Could shrink to R={R_min_cons*100:.1f}cm and still clear.")
    else:
        print(f"  >> Need R > {R_min_cons*100:.1f}cm for this tape width.")
        print(f"  >> Or reduce tape width w to {2*R*crit/twist_rate*1000:.1f}mm")

    return {'eps_total': eps_total, 'margin': margin,
            'R_min_cons': R_min_cons, 'R_min_opt': R_min_opt,
            'verdict': verdict}


# ==============================================================
# ATTACK 4: RADIATION Q
# ==============================================================

def attack_radiation(p):
    R, I = p['R'], p['I']
    f_beat = p['f_beat']
    omega = 2 * np.pi * f_beat

    A_loop = np.pi * R**2
    m_peak = I * A_loop
    P_rad = MU_0 * omega**4 * m_peak**2 / (12 * np.pi * C_LIGHT**3)
    E_stored = 0.5 * p['L_ind'] * I**2
    Q_rad = omega * E_stored / P_rad if P_rad > 0 else float('inf')

    Q_spec = 1e5
    verdict = "SURVIVES" if Q_rad > Q_spec * 1000 else ("VULNERABLE" if Q_rad > Q_spec else "FATAL")

    wavelength = C_LIGHT / f_beat
    frac = p['circumference'] / wavelength

    print(f"\n{'='*70}")
    print(f"ATTACK 4: RADIATION Q  [{p['material']}]")
    print(f"{'='*70}")
    print(f"  Magnetic moment:       {m_peak:.4f} A*m^2")
    print(f"  Beat frequency:        {f_beat:.0f} Hz")
    print(f"  Radiated power:        {P_rad:.2e} W")
    print(f"  Stored energy:         {E_stored:.4f} J")
    print(f"  Q_rad:                 {Q_rad:.2e}")
    print(f"  Wavelength:            {wavelength:.0f} m")
    print(f"  Strip/wavelength:      {frac*100:.4f}%")
    print(f"  >> VERDICT: {verdict}")
    if verdict == "SURVIVES":
        print(f"  >> Still a terrible antenna. Radiation is negligible.")

    return {'Q_rad': Q_rad, 'P_rad': P_rad, 'verdict': verdict, 'm_peak': m_peak}


# ==============================================================
# ATTACK 5: THERMAL HOT SPOT
# ==============================================================

def attack_thermal(p):
    R, w, t, I = p['R'], p['w'], p['t'], p['I']
    T_bath, T_crit = p['T_bath'], p['T_crit']

    B_self = MU_0 * I / (2 * np.pi * w)
    f_beat = p['f_beat']

    # AC loss per volume (hysteretic)
    P_hyst_vol = (2 * MU_0 * p['Jc'] * p['d_filament'] * B_self * f_beat) / (3 * np.pi)

    L_twist = 0.1 * p['circumference']
    V_twist = L_twist * 2 * w * t
    P_twist = P_hyst_vol * V_twist

    # Cooling
    R_kapitza = 0.02e-4  # K*m^2/W
    A_contact = L_twist * 2 * w * 0.5
    G_contact = A_contact / R_kapitza

    delta_T = P_twist / G_contact if G_contact > 0 else float('inf')
    T_twist = T_bath + delta_T
    T_margin = T_crit - T_twist

    verdict = "SURVIVES" if T_margin > 2.0 else ("VULNERABLE" if T_margin > 0.5 else "FATAL")

    print(f"\n{'='*70}")
    print(f"ATTACK 5: THERMAL HOT SPOT  [{p['material']}]")
    print(f"{'='*70}")
    print(f"  Self-field osc:        {B_self*1e3:.2f} mT")
    print(f"  AC loss at twist:      {P_twist*1e6:.3f} uW")
    print(f"  Temperature rise:      {delta_T*1e3:.3f} mK")
    print(f"  Twist temperature:     {T_twist:.4f} K")
    print(f"  T_crit ({p['material']}):         {T_crit} K")
    print(f"  Thermal margin:        {T_margin:.1f} K")
    print(f"  >> VERDICT: {verdict}")
    if T_margin > 10:
        print(f"  >> REBCO at 4K has {T_margin:.0f}K of thermal headroom. Virtually unquenchable.")

    return {'delta_T': delta_T, 'T_margin': T_margin, 'verdict': verdict, 'P_twist': P_twist}


# ==============================================================
# ATTACK 6: FREQUENCY SHIFT
# ==============================================================

def attack_freq_shift(p):
    R, w, I = p['R'], p['w'], p['I']
    B_ext = p['B_ext']

    B_self_local = MU_0 * I / (2 * np.pi * w)
    B_far = MU_0 * I / (2 * np.pi * (2 * R))  # field from opposite side
    ratio = B_far / B_ext

    f_naive = p['f_beat']
    f_shift = f_naive * ratio
    frac_shift = ratio

    if frac_shift < 0.001:
        verdict = "SURVIVES"
    elif frac_shift < 0.01:
        verdict = "VULNERABLE"
    else:
        verdict = "FATAL"

    print(f"\n{'='*70}")
    print(f"ATTACK 6: FREQUENCY SHIFT  [{p['material']}]")
    print(f"{'='*70}")
    print(f"  B_ext:                 {B_ext*1e3:.1f} mT")
    print(f"  B_self (local):        {B_self_local*1e3:.2f} mT")
    print(f"  B_far (opposite):      {B_far*1e6:.1f} uT")
    print(f"  B_far / B_ext:         {ratio:.2e}")
    print(f"  Naive beat freq:       {f_naive:.1f} Hz")
    print(f"  Frequency shift:       {f_shift:.4f} Hz")
    print(f"  Fractional shift:      {frac_shift*1e6:.1f} ppm")
    print(f"  >> VERDICT: {verdict}")
    if verdict == "SURVIVES":
        print(f"  >> Larger radius REDUCES self-field at far side. Geometry helps.")

    return {'frac_shift': frac_shift, 'verdict': verdict, 'f_shift': f_shift}


# ==============================================================
# MAIN: RUN BOTH CONFIGURATIONS
# ==============================================================

def run_all(p):
    p = compute_derived(p)
    print(f"\n{'#'*70}")
    print(f"  CONFIGURATION: {p['name']}")
    print(f"  R={p['R']*100:.0f}cm  w={p['w']*1000:.1f}mm  t={p['t']*1000:.2f}mm")
    print(f"  I={p['I']}A  Material={p['material']}  T_crit={p['T_crit']}K")
    print(f"  f_beat={p['f_beat']:.1f} Hz  L={p['L_ind']*1e6:.2f} uH")
    print(f"{'#'*70}")

    r1 = attack_lorentz(p)
    r2 = attack_copper(p)
    r3 = attack_strain(p)
    r4 = attack_radiation(p)
    r5 = attack_thermal(p)
    r6 = attack_freq_shift(p)

    results = [r1, r2, r3, r4, r5, r6]
    verdicts = [
        r1['verdict'],
        r2['verdict_4K'],
        r3['verdict'],
        r4['verdict'],
        r5['verdict'],
        r6['verdict'],
    ]

    print(f"\n{'='*70}")
    print(f"SUMMARY: {p['name']}")
    print(f"{'='*70}")
    labels = [
        "1. Lorentz Force",
        "2. Copper Signal (4K)",
        "3. Bend Strain",
        "4. Radiation Q",
        "5. Thermal Hot Spot",
        "6. Frequency Shift",
    ]
    for label, v in zip(labels, verdicts):
        tag = "[ . ]" if v == "SURVIVES" else ("[ ! ]" if v == "VULNERABLE" else "[XXX]")
        print(f"  {tag} {label:30s} {v}")

    n_s = verdicts.count("SURVIVES")
    n_v = verdicts.count("VULNERABLE")
    n_f = verdicts.count("FATAL")
    print(f"\n  SURVIVES: {n_s}  VULNERABLE: {n_v}  FATAL: {n_f}")

    if n_f == 0 and n_v == 0:
        print(f"\n  ALL CLEAR. The heart beats clean.")
    elif n_f == 0:
        print(f"\n  HEART LIVES. {n_v} issues to watch.")
    else:
        print(f"\n  HEART HAS WOUNDS. {n_f} fatal issues.")

    return results, verdicts, p


def make_figure(res_orig, v_orig, p_orig, res_rebco, v_rebco, p_rebco):
    """Side-by-side comparison figure."""

    fig = plt.figure(figsize=(18, 10))
    fig.patch.set_facecolor('#0a0a1a')
    fig.suptitle('MTR REDESIGN: NbTi vs REBCO',
                 color='white', fontsize=20, fontweight='bold', y=0.98)
    fig.text(0.5, 0.94, 'Same six attacks. New material. New geometry.',
             ha='center', color='#888888', fontsize=12)

    # Color scheme
    c_fail = '#ff4444'
    c_vuln = '#ffaa00'
    c_pass = '#00ffcc'
    c_bg = '#0a0a1a'

    def verdict_color(v):
        return c_pass if v == "SURVIVES" else (c_vuln if v == "VULNERABLE" else c_fail)

    # --- Panel 1: Strain comparison (the critical fix) ---
    ax1 = fig.add_subplot(2, 3, 1)
    ax1.set_facecolor(c_bg)

    R_range = np.linspace(0.02, 0.60, 200)

    # NbTi strain curve
    w_orig, t_orig = p_orig['w'], p_orig['t']
    eps_orig = np.sqrt((t_orig/(2*R_range))**2 + (w_orig/(2*R_range))**2)
    ax1.semilogy(R_range*100, eps_orig*100, color=c_fail, linewidth=2, label=f'NbTi (w={w_orig*1000:.0f}mm)')

    # REBCO strain curve
    w_new, t_new = p_rebco['w'], p_rebco['t']
    eps_new = np.sqrt((t_new/(2*R_range))**2 + (w_new/(2*R_range))**2)
    ax1.semilogy(R_range*100, eps_new*100, color=c_pass, linewidth=2, label=f'REBCO (w={w_new*1000:.0f}mm)')

    # Critical strain lines
    ax1.axhline(NBTI_CRIT_STRAIN*100, color=c_fail, linestyle='--', alpha=0.5, linewidth=1)
    ax1.text(55, NBTI_CRIT_STRAIN*100*1.1, 'NbTi limit', color=c_fail, fontsize=8)
    ax1.axhline(REBCO_CRIT_STRAIN*100, color=c_pass, linestyle='--', alpha=0.5, linewidth=1)
    ax1.text(55, REBCO_CRIT_STRAIN*100*1.1, 'REBCO limit', color=c_pass, fontsize=8)

    # Design points
    ax1.plot(p_orig['R']*100, res_orig[2]['eps_total']*100, 'x', color=c_fail, markersize=15, markeredgewidth=3)
    ax1.plot(p_rebco['R']*100, res_rebco[2]['eps_total']*100, 'o', color=c_pass, markersize=12, markeredgewidth=2)

    ax1.set_xlabel('Radius [cm]', color='#cccccc')
    ax1.set_ylabel('Total Strain [%]', color='#cccccc')
    ax1.set_title('ATTACK 3: Bend Strain (THE FIX)', color='white', fontweight='bold')
    ax1.legend(fontsize=9, facecolor='#1a1a2e', edgecolor='#333', labelcolor='#cccccc')
    ax1.tick_params(colors='#cccccc')
    ax1.set_xlim(0, 60)
    for spine in ax1.spines.values(): spine.set_color('#333')

    # --- Panel 2: Thermal margin comparison ---
    ax2 = fig.add_subplot(2, 3, 2)
    ax2.set_facecolor(c_bg)

    materials = ['NbTi\n(original)', 'REBCO\n(redesign)']
    T_margins = [res_orig[4]['T_margin'], res_rebco[4]['T_margin']]
    T_crits = [p_orig['T_crit'], p_rebco['T_crit']]
    T_bath = 4.2

    bars = ax2.bar(materials, T_margins, color=[c_vuln, c_pass], width=0.5,
                   edgecolor='white', linewidth=0.5, alpha=0.9)
    for bar, tm, tc in zip(bars, T_margins, T_crits):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f'{tm:.1f} K', ha='center', color='white', fontsize=14, fontweight='bold')

    ax2.set_ylabel('Thermal Margin [K]', color='#cccccc')
    ax2.set_title('ATTACK 5: Thermal Headroom', color='white', fontweight='bold')
    ax2.tick_params(colors='#cccccc')
    for spine in ax2.spines.values(): spine.set_color('#333')

    # --- Panel 3: Frequency comparison ---
    ax3 = fig.add_subplot(2, 3, 3)
    ax3.set_facecolor(c_bg)

    freqs = [p_orig['f_beat'], p_rebco['f_beat']]
    shifts_ppm = [res_orig[5]['frac_shift']*1e6, res_rebco[5]['frac_shift']*1e6]

    x_pos = [0, 1]
    bars_f = ax3.bar(x_pos, freqs, color=[c_fail, c_pass], width=0.4,
                     edgecolor='white', linewidth=0.5, alpha=0.9)
    for bar, f, s in zip(bars_f, freqs, shifts_ppm):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
                 f'{f:.0f} Hz', ha='center', color='white', fontsize=12, fontweight='bold')
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                 f'shift: {s:.0f} ppm', ha='center', color='#0a0a1a', fontsize=9, fontweight='bold')

    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(['NbTi\n(original)', 'REBCO\n(redesign)'])
    ax3.set_ylabel('Beat Frequency [Hz]', color='#cccccc')
    ax3.set_title('ATTACK 6: Beat Frequency & Shift', color='white', fontweight='bold')
    ax3.tick_params(colors='#cccccc')
    for spine in ax3.spines.values(): spine.set_color('#333')

    # --- Panel 4: Copper signal comparison ---
    ax4 = fig.add_subplot(2, 3, 4)
    ax4.set_facecolor(c_bg)

    # Show signal decay for both
    t_ax = np.linspace(0, 20, 1000)  # time in ms

    tau_orig_4K = res_orig[1]['tau_4K']
    tau_rebco_4K = res_rebco[1]['tau_4K']
    f_orig = res_orig[1]['f_beat']
    f_rebco = res_rebco[1]['f_beat']

    sig_orig = np.exp(-t_ax*1e-3/tau_orig_4K) * np.cos(2*np.pi*f_orig*t_ax*1e-3)
    sig_rebco = np.exp(-t_ax*1e-3/tau_rebco_4K) * np.cos(2*np.pi*f_rebco*t_ax*1e-3)
    env_orig = np.exp(-t_ax*1e-3/tau_orig_4K)
    env_rebco = np.exp(-t_ax*1e-3/tau_rebco_4K)

    ax4.plot(t_ax, env_orig, color=c_fail, linewidth=2, alpha=0.7, label=f'NbTi tau={tau_orig_4K*1e3:.1f}ms')
    ax4.plot(t_ax, env_rebco, color=c_pass, linewidth=2, alpha=0.7, label=f'REBCO tau={tau_rebco_4K*1e3:.1f}ms')
    ax4.axhline(1/np.e, color='#666', linestyle=':', linewidth=1, alpha=0.5)
    ax4.text(18, 1/np.e + 0.02, '1/e', color='#666', fontsize=9)

    ax4.set_xlabel('Time [ms]', color='#cccccc')
    ax4.set_ylabel('Signal Envelope', color='#cccccc')
    ax4.set_title('ATTACK 2: Copper Signal Decay (4K)', color='white', fontweight='bold')
    ax4.legend(fontsize=9, facecolor='#1a1a2e', edgecolor='#333', labelcolor='#cccccc')
    ax4.tick_params(colors='#cccccc')
    for spine in ax4.spines.values(): spine.set_color('#333')

    # --- Panel 5: Q factor comparison ---
    ax5 = fig.add_subplot(2, 3, 5)
    ax5.set_facecolor(c_bg)

    Q_vals = [res_orig[3]['Q_rad'], res_rebco[3]['Q_rad']]
    bars_q = ax5.bar(['NbTi', 'REBCO'], Q_vals, color=[c_vuln, c_pass], width=0.4,
                     edgecolor='white', linewidth=0.5, alpha=0.9)
    for bar, q in zip(bars_q, Q_vals):
        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 0.5,
                 f'Q = {q:.1e}', ha='center', color='#0a0a1a', fontsize=11, fontweight='bold',
                 rotation=90)
    ax5.axhline(1e5, color='#666', linestyle=':', linewidth=1.5)
    ax5.text(1.4, 1e5*1.5, 'Q_spec', color='#666', fontsize=9)
    ax5.set_yscale('log')
    ax5.set_ylabel('Q Factor', color='#cccccc')
    ax5.set_title('ATTACK 4: Radiation Q', color='white', fontweight='bold')
    ax5.tick_params(colors='#cccccc')
    for spine in ax5.spines.values(): spine.set_color('#333')

    # --- Panel 6: Verdict scoreboard ---
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.set_facecolor(c_bg)
    ax6.axis('off')

    labels = ['1. Lorentz Force', '2. Copper Signal', '3. Bend Strain',
              '4. Radiation Q', '5. Thermal Hot Spot', '6. Frequency Shift']

    ax6.text(0.5, 0.95, 'VERDICT COMPARISON', color='white', fontsize=16,
             fontweight='bold', ha='center', va='top', transform=ax6.transAxes)

    ax6.text(0.02, 0.82, 'Attack', color='#888', fontsize=10,
             fontweight='bold', transform=ax6.transAxes)
    ax6.text(0.55, 0.82, 'NbTi', color=c_fail, fontsize=10,
             fontweight='bold', ha='center', transform=ax6.transAxes)
    ax6.text(0.85, 0.82, 'REBCO', color=c_pass, fontsize=10,
             fontweight='bold', ha='center', transform=ax6.transAxes)

    for i, (label, vo, vr) in enumerate(zip(labels, v_orig, v_rebco)):
        y = 0.72 - i * 0.10
        ax6.text(0.02, y, label, color='#cccccc', fontsize=11, transform=ax6.transAxes)
        ax6.text(0.55, y, vo, color=verdict_color(vo), fontsize=11,
                 fontweight='bold', ha='center', transform=ax6.transAxes)
        ax6.text(0.85, y, vr, color=verdict_color(vr), fontsize=11,
                 fontweight='bold', ha='center', transform=ax6.transAxes)

    # Bottom line
    n_f_orig = v_orig.count("FATAL")
    n_f_rebco = v_rebco.count("FATAL")
    if n_f_rebco == 0:
        msg = "REBCO CLEARS ALL SIX."
        msg_color = c_pass
    else:
        msg = f"REBCO still has {n_f_rebco} fatal."
        msg_color = c_fail

    ax6.text(0.5, 0.05, msg, color=msg_color, fontsize=16,
             fontweight='bold', ha='center', transform=ax6.transAxes)

    # Footer
    fig.text(0.5, 0.01,
             'Harley Robinson + Forge  |  REBCO redesign  |  github.com/EntropyWizardchaos/ghost-shell',
             ha='center', color='#555555', fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.92])

    out = r"C:\Users\14132\iCloudDrive\For you Forge\ghost-shell\docs\figures\mtr_rebco_redesign.png"
    out_sm = r"C:\Users\14132\iCloudDrive\For you Forge\ghost-shell\docs\figures\mtr_rebco_redesign_sm.png"
    plt.savefig(out, dpi=200, facecolor=c_bg, bbox_inches='tight')
    plt.savefig(out_sm, dpi=120, facecolor=c_bg, bbox_inches='tight')
    plt.close()
    print(f"\nFigure saved: {out}")
    print(f"Social media: {out_sm}")


# ==============================================================
# RUN
# ==============================================================

if __name__ == '__main__':
    print("=" * 70)
    print("MTR STRESS TEST v2 -- REBCO REDESIGN")
    print("=" * 70)
    print("The Little Black Dress found a wound. This is the surgery.")
    print()

    print("\n\n" + "*" * 70)
    print("*  ORIGINAL DESIGN (for comparison)")
    print("*" * 70)
    res_orig, v_orig, p_orig = run_all(ORIGINAL)

    print("\n\n" + "*" * 70)
    print("*  REBCO REDESIGN")
    print("*" * 70)
    res_rebco, v_rebco, p_rebco = run_all(REBCO)

    # --- Head-to-head ---
    print("\n\n" + "=" * 70)
    print("HEAD-TO-HEAD COMPARISON")
    print("=" * 70)
    print(f"  {'':30s} {'NbTi (orig)':>15s} {'REBCO (new)':>15s}")
    print(f"  {'-'*60}")
    print(f"  {'Radius':30s} {p_orig['R']*100:>12.0f} cm {p_rebco['R']*100:>12.0f} cm")
    print(f"  {'Strip width':30s} {p_orig['w']*1000:>12.0f} mm {p_rebco['w']*1000:>12.0f} mm")
    print(f"  {'Strip thickness':30s} {p_orig['t']*1000:>12.1f} mm {p_rebco['t']*1000:>12.2f} mm")
    print(f"  {'Current':30s} {p_orig['I']:>12.0f} A  {p_rebco['I']:>12.0f} A ")
    print(f"  {'T_crit':30s} {p_orig['T_crit']:>12.1f} K  {p_rebco['T_crit']:>12.1f} K ")
    print(f"  {'Thermal margin':30s} {res_orig[4]['T_margin']:>12.1f} K  {res_rebco[4]['T_margin']:>12.1f} K ")
    print(f"  {'Beat frequency':30s} {p_orig['f_beat']:>12.0f} Hz {p_rebco['f_beat']:>12.0f} Hz")
    print(f"  {'Bend strain':30s} {res_orig[2]['eps_total']*100:>11.3f}%  {res_rebco[2]['eps_total']*100:>11.4f}% ")
    print(f"  {'Strain margin':30s} {res_orig[2]['margin']:>12.2f}x  {res_rebco[2]['margin']:>12.2f}x ")
    print(f"  {'Freq shift':30s} {res_orig[5]['frac_shift']*1e6:>10.0f} ppm {res_rebco[5]['frac_shift']*1e6:>10.0f} ppm")
    print(f"  {'Q_rad':30s} {res_orig[3]['Q_rad']:>12.1e}  {res_rebco[3]['Q_rad']:>12.1e} ")
    print()

    n_f_orig = v_orig.count("FATAL")
    n_f_rebco = v_rebco.count("FATAL")
    print(f"  NbTi:  {v_orig.count('SURVIVES')} survive, {v_orig.count('VULNERABLE')} vulnerable, {n_f_orig} fatal")
    print(f"  REBCO: {v_rebco.count('SURVIVES')} survive, {v_rebco.count('VULNERABLE')} vulnerable, {n_f_rebco} fatal")

    if n_f_rebco == 0:
        print(f"\n  THE HEART BEATS CLEAN.")
    else:
        print(f"\n  Still wounded. {n_f_rebco} fatal issues remain.")

    print("\nGenerating comparison figure...")
    make_figure(res_orig, v_orig, p_orig, res_rebco, v_rebco, p_rebco)

    print("\nDone.")
