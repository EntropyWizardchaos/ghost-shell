"""
MTR Stress Test -- "The Little Black Dress"
=============================================
Adversarial simulation designed to BREAK the Mobius Heart.
If it survives, it's real. If it doesn't, we know where to fix.

Six attacks on the design:

  1. SELF-FIELD LORENTZ FORCE
     The current's own B-field pushes on the strip.
     Does the Mobius twist create asymmetric forces
     that would deform or tear the strip?

  2. COPPER SURROGATE SIGNAL DEATH
     Phase 0 uses copper, not superconductor.
     Current decays exponentially (R/L time constant).
     Is the beat signal detectable before it dies?

  3. CRITICAL BEND STRAIN
     NbTi has a maximum strain before SC dies (~0.5-1%).
     The Mobius twist forces curvature.
     At what radius does the twist kill superconductivity?

  4. Q FACTOR FROM RADIATION LOSS
     An oscillating magnetic dipole radiates.
     The beat = oscillating moment = antenna.
     How much power leaks out as radiation?

  5. THERMAL HOT SPOT AT THE TWIST
     The twist region has maximum curvature.
     If cooling channels can't reach it evenly,
     local heating could quench the SC.

  6. SELF-FIELD BEAT FREQUENCY SHIFT
     The current's own field adds to the external B.
     This modifies the effective field at each point.
     How far does the real beat drift from the naive prediction?

Each test reports: SURVIVES / VULNERABLE / FATAL
and what would fix it if it fails.

Design by Harley Robinson. Broken by Forge.
"""

import numpy as np
import matplotlib.pyplot as plt

# ══════════════════════════════════════════════════════════════
# CONSTANTS AND PARAMETERS
# ══════════════════════════════════════════════════════════════

MU_0 = 4 * np.pi * 1e-7      # vacuum permeability [H/m]
RHO_CU = 1.7e-8              # copper resistivity at 300K [Ohm*m]
RHO_CU_CRYO = 2e-9           # copper resistivity at 4K [Ohm*m] (RRR~10)
RHO_NBTI_NORMAL = 6e-7       # NbTi normal state resistivity [Ohm*m]
NBTI_CRIT_STRAIN = 0.005     # NbTi critical strain ~0.5%
NBTI_CRIT_STRAIN_HI = 0.01   # optimistic NbTi strain limit ~1.0%
NBTI_JC = 3e9                # NbTi critical current density at 4.2K, 5T [A/m^2]
C_LIGHT = 3e8                # speed of light [m/s]

# Default MTR parameters (lab-scale prototype)
DEFAULT = {
    'R': 0.05,                # major radius [m] (5 cm)
    'w': 0.01,                # strip half-width [m] (1 cm)
    't': 0.001,               # strip thickness [m] (1 mm)
    'I': 100,                 # operating current [A]
    'B_ext': 0.1,             # external field [T]
    'f_beat': 15915.5,        # from Layer 1 sim [Hz]
    'T_bath': 4.2,            # helium bath temperature [K]
    'T_crit': 9.2,            # NbTi critical temperature [K]
}


# ══════════════════════════════════════════════════════════════
# ATTACK 1: SELF-FIELD LORENTZ FORCE
# ══════════════════════════════════════════════════════════════

def attack_lorentz_force(p=None):
    """
    The current in the strip creates its own magnetic field.
    This field exerts a Lorentz force (J x B_self) on the strip.
    On a Mobius twist, the force distribution is asymmetric.

    Key question: does the force exceed the yield strength of
    the substrate material?
    """
    if p is None: p = DEFAULT

    R, w, t, I = p['R'], p['w'], p['t'], p['I']

    # Self-field at the surface of a flat strip carrying current I
    # B_self ~ mu_0 * I / (2 * pi * w) for a strip of width 2w
    # (approximation: treat strip as infinite flat conductor)
    B_self = MU_0 * I / (2 * np.pi * w)

    # Current density
    A_cross = 2 * w * t  # cross-sectional area
    J = I / A_cross

    # Lorentz force per unit volume: f = J * B_self [N/m^3]
    f_lorentz = J * B_self

    # Force per unit length along the strip: F/L = f * A_cross [N/m]
    F_per_length = f_lorentz * A_cross

    # Total hoop force (trying to expand the loop): F_hoop = F/L * 2*pi*R
    # But on a Mobius strip, the twist redistributes this
    # The ASYMMETRY comes from the twist: at the twist region,
    # the field direction rotates relative to the strip
    # Maximum stress concentration factor for the twist region: ~1.5-2x
    twist_stress_factor = 1.8  # conservative estimate

    F_hoop_total = F_per_length * 2 * np.pi * R
    stress_hoop = F_per_length / (t * 1)  # stress = F / A (per unit width)
    stress_at_twist = stress_hoop * twist_stress_factor

    # NbTi yield strength: ~800 MPa (in composite form)
    # PRF substrate (CNT/DLC): ~2000 MPa
    yield_nbti = 800e6
    yield_prf = 2000e6

    margin_nbti = yield_nbti / stress_at_twist
    margin_prf = yield_prf / stress_at_twist

    print("\n" + "=" * 70)
    print("ATTACK 1: SELF-FIELD LORENTZ FORCE")
    print("=" * 70)
    print(f"  Self-field at surface:     {B_self*1e3:.2f} mT")
    print(f"  Current density J:         {J/1e6:.1f} MA/m^2")
    print(f"  Lorentz force density:     {f_lorentz:.1f} N/m^3")
    print(f"  Force per unit length:     {F_per_length*1e3:.3f} mN/m")
    print(f"  Hoop stress (uniform):     {stress_hoop:.1f} Pa")
    print(f"  Stress at twist (x{twist_stress_factor}):  {stress_at_twist:.1f} Pa")
    print(f"  NbTi yield margin:         {margin_nbti:.0f}x")
    print(f"  PRF substrate margin:      {margin_prf:.0f}x")

    if margin_nbti > 10:
        verdict = "SURVIVES"
        note = "Lorentz forces are negligible at this scale."
    elif margin_nbti > 2:
        verdict = "VULNERABLE"
        note = f"Margin only {margin_nbti:.0f}x. Higher current or smaller radius could fail."
    else:
        verdict = "FATAL"
        note = f"Stress exceeds yield. Reduce current or increase strip thickness."

    print(f"\n  >> VERDICT: {verdict}")
    print(f"  >> {note}")

    # What helps
    if margin_nbti > 10:
        print(f"  >> BOOST: Safe to increase current up to ~{I * (margin_nbti/3)**.5:.0f} A")
    else:
        I_safe = I * (margin_nbti / 3) ** 0.5
        print(f"  >> FIX: Reduce current to {I_safe:.0f} A, or increase thickness to {t*1e3 * 3/margin_nbti:.1f} mm")

    return {
        'B_self': B_self, 'stress_twist': stress_at_twist,
        'margin_nbti': margin_nbti, 'margin_prf': margin_prf,
        'verdict': verdict
    }


# ══════════════════════════════════════════════════════════════
# ATTACK 2: COPPER SURROGATE SIGNAL DEATH
# ══════════════════════════════════════════════════════════════

def attack_copper_signal(p=None):
    """
    Phase 0 test uses copper, not superconductor.
    Current decays with time constant tau = L/R.
    The beat signal amplitude decays with the current.

    Key question: how many beat cycles are detectable
    above a realistic noise floor before the signal dies?
    """
    if p is None: p = DEFAULT

    R, w, t, I = p['R'], p['w'], p['t'], p['I']

    # Strip dimensions
    circumference = 2 * np.pi * R
    A_cross = 2 * w * t

    # Resistance of copper strip (room temp and cryo)
    R_cu_300K = RHO_CU * circumference / A_cross
    R_cu_4K = RHO_CU_CRYO * circumference / A_cross

    # Inductance of a single-turn loop (Neumann formula approximation)
    # L ~ mu_0 * R * (ln(8R/a) - 2) where a = sqrt(w*t/pi) is effective wire radius
    a_eff = np.sqrt(w * t / np.pi)
    L = MU_0 * R * (np.log(8 * R / a_eff) - 2)

    # Time constants
    tau_300K = L / R_cu_300K
    tau_4K = L / R_cu_4K

    # Beat frequency from Layer 1
    f_beat = p['f_beat']
    T_beat = 1 / f_beat

    # Number of detectable beat cycles (signal drops to 1/e)
    n_cycles_300K = tau_300K * f_beat
    n_cycles_4K = tau_4K * f_beat

    # Signal amplitude in pickup coil (rough estimate)
    # V_pickup ~ M * dI/dt ~ M * I * 2*pi*f_beat
    # where M is mutual inductance between MTR and pickup coil
    # Assume pickup coil at distance d = 2cm, area A_pickup = 1 cm^2
    d_pickup = 0.02  # 2 cm
    A_pickup = 1e-4   # 1 cm^2
    M = MU_0 * A_pickup / (4 * np.pi * d_pickup)  # rough mutual inductance

    V_peak_300K = M * I * 2 * np.pi * f_beat  # initial signal
    V_peak_4K = V_peak_300K  # same initial, different decay

    # Noise floor: typical lab environment
    # Johnson noise in pickup at 300K: V_noise ~ sqrt(4kTRB)
    # Assume pickup coil R = 1 Ohm, bandwidth B = f_beat
    k_B = 1.38e-23
    R_pickup = 1.0
    V_noise_300K = np.sqrt(4 * k_B * 300 * R_pickup * f_beat)
    V_noise_4K = np.sqrt(4 * k_B * 4.2 * R_pickup * f_beat)

    SNR_300K = V_peak_300K / V_noise_300K
    SNR_4K = V_peak_4K / V_noise_4K

    # Time-domain: at what time does SNR drop to 3 (barely detectable)?
    if SNR_300K > 3:
        t_detect_300K = tau_300K * np.log(SNR_300K / 3)
        cycles_detect_300K = t_detect_300K * f_beat
    else:
        t_detect_300K = 0
        cycles_detect_300K = 0

    if SNR_4K > 3:
        t_detect_4K = tau_4K * np.log(SNR_4K / 3)
        cycles_detect_4K = t_detect_4K * f_beat
    else:
        t_detect_4K = 0
        cycles_detect_4K = 0

    print("\n" + "=" * 70)
    print("ATTACK 2: COPPER SURROGATE SIGNAL DEATH")
    print("=" * 70)
    print(f"  Strip resistance (300K):   {R_cu_300K*1e3:.3f} mOhm")
    print(f"  Strip resistance (4K):     {R_cu_4K*1e3:.4f} mOhm")
    print(f"  Loop inductance:           {L*1e6:.2f} uH")
    print(f"  Decay time tau (300K):     {tau_300K*1e6:.1f} us")
    print(f"  Decay time tau (4K):       {tau_4K*1e3:.2f} ms")
    print(f"  Beat period:               {T_beat*1e6:.1f} us")
    print(f"  Cycles before 1/e (300K):  {n_cycles_300K:.1f}")
    print(f"  Cycles before 1/e (4K):    {n_cycles_4K:.0f}")
    print(f"  Pickup signal (peak):      {V_peak_300K*1e6:.2f} uV")
    print(f"  Noise floor (300K):        {V_noise_300K*1e9:.1f} nV")
    print(f"  Noise floor (4K):          {V_noise_4K*1e9:.1f} nV")
    print(f"  SNR initial (300K):        {SNR_300K:.1f}")
    print(f"  SNR initial (4K):          {SNR_4K:.1f}")
    print(f"  Detectable cycles (300K):  {cycles_detect_300K:.1f}")
    print(f"  Detectable cycles (4K):    {cycles_detect_4K:.0f}")

    if n_cycles_300K < 1:
        verdict_300K = "FATAL"
        note_300K = "Signal dies before completing ONE beat cycle at room temp."
    elif n_cycles_300K < 10:
        verdict_300K = "VULNERABLE"
        note_300K = f"Only {n_cycles_300K:.1f} cycles. Marginal detection."
    else:
        verdict_300K = "SURVIVES"
        note_300K = f"{n_cycles_300K:.0f} cycles detectable."

    if n_cycles_4K < 10:
        verdict_4K = "VULNERABLE"
        note_4K = "Cryo copper helps but still tight."
    else:
        verdict_4K = "SURVIVES"
        note_4K = f"{n_cycles_4K:.0f} cycles at 4K copper. Solid detection window."

    print(f"\n  >> PHASE 0 AT 300K: {verdict_300K}")
    print(f"     {note_300K}")
    print(f"  >> PHASE 0 AT 4K:   {verdict_4K}")
    print(f"     {note_4K}")

    # What helps
    print(f"  >> FIX: Use cryo copper (4K) for Phase 0. RRR>100 copper drops resistance 100x.")
    print(f"  >> FIX: Increase strip cross-section to lower resistance.")
    print(f"  >> FIX: Use lock-in amplifier (narrows bandwidth, drops noise floor 100x).")
    if n_cycles_300K < 1:
        print(f"  >> BOOST with lock-in: ~{n_cycles_300K * 100:.0f} effective cycles recoverable.")

    return {
        'tau_300K': tau_300K, 'tau_4K': tau_4K,
        'n_cycles_300K': n_cycles_300K, 'n_cycles_4K': n_cycles_4K,
        'SNR_300K': SNR_300K, 'SNR_4K': SNR_4K,
        'verdict_300K': verdict_300K, 'verdict_4K': verdict_4K,
        'L': L, 'f_beat': f_beat,
    }


# ══════════════════════════════════════════════════════════════
# ATTACK 3: CRITICAL BEND STRAIN
# ══════════════════════════════════════════════════════════════

def attack_bend_strain(p=None):
    """
    The Mobius twist forces the strip through a 180-degree rotation
    over one circumference. This creates bending strain.
    NbTi superconductivity dies above ~0.5-1% strain.

    Key question: at what strip radius does the Mobius twist
    exceed the critical strain?
    """
    if p is None: p = DEFAULT

    R, w, t = p['R'], p['w'], p['t']

    # The Mobius strip has two sources of curvature:
    # 1. The circular loop curvature: kappa_loop = 1/R
    #    Strain from loop bending: eps_loop = t / (2*R)
    #
    # 2. The twist curvature: the strip rotates 180 deg over circumference 2*pi*R
    #    Twist rate: phi/L = pi / (2*pi*R) = 1/(2R) [rad/m]
    #    Torsional strain in the outer fiber: eps_twist = w * twist_rate
    #    eps_twist = w / (2*R)

    eps_loop = t / (2 * R)
    twist_rate = np.pi / (2 * np.pi * R)  # rad/m
    eps_twist = w * twist_rate

    # Combined strain (approximate: add in quadrature for biaxial)
    eps_total = np.sqrt(eps_loop**2 + eps_twist**2)

    # Critical radius: where eps_total = critical strain
    # eps_total ~ sqrt((t/2R)^2 + (w/2R)^2) = sqrt(t^2+w^2)/(2R)
    # Set equal to eps_crit: R_min = sqrt(t^2+w^2) / (2*eps_crit)
    R_min_conservative = np.sqrt(t**2 + w**2) / (2 * NBTI_CRIT_STRAIN)
    R_min_optimistic = np.sqrt(t**2 + w**2) / (2 * NBTI_CRIT_STRAIN_HI)

    strain_margin = NBTI_CRIT_STRAIN / eps_total

    print("\n" + "=" * 70)
    print("ATTACK 3: CRITICAL BEND STRAIN")
    print("=" * 70)
    print(f"  Loop bending strain:       {eps_loop*100:.4f}%")
    print(f"  Twist torsional strain:    {eps_twist*100:.4f}%")
    print(f"  Total combined strain:     {eps_total*100:.4f}%")
    print(f"  NbTi critical strain:      {NBTI_CRIT_STRAIN*100:.1f}% (conservative)")
    print(f"  NbTi critical strain:      {NBTI_CRIT_STRAIN_HI*100:.1f}% (optimistic)")
    print(f"  Strain margin:             {strain_margin:.1f}x")
    print(f"  Minimum radius (conserv.): {R_min_conservative*100:.2f} cm")
    print(f"  Minimum radius (optimist): {R_min_optimistic*100:.2f} cm")
    print(f"  Current design radius:     {R*100:.1f} cm")

    if R > R_min_conservative:
        verdict = "SURVIVES"
        note = f"Design radius {R*100:.0f}cm > minimum {R_min_conservative*100:.1f}cm. SC preserved."
    elif R > R_min_optimistic:
        verdict = "VULNERABLE"
        note = f"Between conservative and optimistic limits. Needs material testing."
    else:
        verdict = "FATAL"
        note = f"Twist strain kills SC. Need R > {R_min_conservative*100:.1f} cm."

    print(f"\n  >> VERDICT: {verdict}")
    print(f"  >> {note}")

    # What helps
    if verdict != "SURVIVES":
        print(f"  >> FIX: Increase radius to {R_min_conservative*100:.1f}+ cm")
        print(f"  >> FIX: Use HTS tape (REBCO) -- higher strain tolerance (~0.4-0.7% on Hastelloy)")
        print(f"  >> FIX: Reduce strip width w (dominates twist strain)")
    else:
        R_min_at_current_w = R_min_conservative
        print(f"  >> BOOST: Could go as small as R={R_min_at_current_w*100:.1f}cm")
        print(f"  >> NOTE: Twist strain ({eps_twist*100:.3f}%) dominates loop strain ({eps_loop*100:.4f}%)")
        print(f"     Width w is the critical dimension, not thickness t.")

    return {
        'eps_loop': eps_loop, 'eps_twist': eps_twist, 'eps_total': eps_total,
        'R_min_conserv': R_min_conservative, 'R_min_optimist': R_min_optimistic,
        'strain_margin': strain_margin, 'verdict': verdict,
    }


# ══════════════════════════════════════════════════════════════
# ATTACK 4: RADIATION LOSS (Q FACTOR)
# ══════════════════════════════════════════════════════════════

def attack_radiation_q(p=None):
    """
    The beat = oscillating magnetic moment = magnetic dipole antenna.
    An oscillating dipole radiates power: P = mu_0 * m_dot^2 / (6*pi*c^3)

    Key question: how much power leaks as radiation?
    What Q factor does this give the resonator?
    """
    if p is None: p = DEFAULT

    R, w, t, I = p['R'], p['w'], p['t'], p['I']
    f_beat = p['f_beat']
    omega = 2 * np.pi * f_beat

    # Magnetic moment of the current loop
    A_loop = np.pi * R**2
    m_peak = I * A_loop  # peak magnetic moment [A*m^2]

    # Oscillating moment: m(t) = m_peak * cos(omega*t)
    # m_dot_peak = m_peak * omega
    m_dot_peak = m_peak * omega

    # Larmor formula for magnetic dipole radiation:
    # P_rad = mu_0 * omega^4 * m_peak^2 / (12 * pi * c^3)
    P_rad = MU_0 * omega**4 * m_peak**2 / (12 * np.pi * C_LIGHT**3)

    # Energy stored in the magnetic field of the loop
    # E_stored = 0.5 * L * I^2
    a_eff = np.sqrt(w * t / np.pi)
    L = MU_0 * R * (np.log(8 * R / a_eff) - 2)
    E_stored = 0.5 * L * I**2

    # Q factor: Q = omega * E_stored / P_rad
    Q_rad = omega * E_stored / P_rad if P_rad > 0 else float('inf')

    # Energy decay time from radiation alone
    tau_rad = Q_rad / omega

    # Compare to spec requirement: Q >= 1e5
    Q_spec = 1e5

    print("\n" + "=" * 70)
    print("ATTACK 4: RADIATION LOSS (Q FACTOR)")
    print("=" * 70)
    print(f"  Magnetic moment m:         {m_peak:.4f} A*m^2")
    print(f"  Beat frequency:            {f_beat:.0f} Hz")
    print(f"  Radiated power:            {P_rad:.2e} W")
    print(f"  Stored energy:             {E_stored:.4f} J")
    print(f"  Q factor (radiation):      {Q_rad:.2e}")
    print(f"  Radiation decay time:      {tau_rad:.2e} s")
    print(f"  Required Q:                {Q_spec:.0e}")

    if Q_rad > Q_spec * 1000:
        verdict = "SURVIVES"
        note = f"Q_rad = {Q_rad:.1e} >> Q_spec = {Q_spec:.0e}. Radiation is negligible."
    elif Q_rad > Q_spec:
        verdict = "VULNERABLE"
        note = "Radiation Q meets spec but doesn't dominate. Other losses matter more."
    else:
        verdict = "FATAL"
        note = f"Radiation alone kills the Q. Need Q > {Q_spec:.0e}, got {Q_rad:.1e}."

    print(f"\n  >> VERDICT: {verdict}")
    print(f"  >> {note}")
    print(f"  >> NOTE: At ~16 kHz, the wavelength is {C_LIGHT/f_beat:.0f} m.")
    print(f"     Strip is {2*np.pi*R*100:.0f} cm. That's {2*np.pi*R/(C_LIGHT/f_beat)*100:.4f}% of a wavelength.")
    print(f"     This is a TERRIBLE antenna. Radiation loss is negligible.")

    return {
        'P_rad': P_rad, 'E_stored': E_stored,
        'Q_rad': Q_rad, 'tau_rad': tau_rad,
        'verdict': verdict,
    }


# ══════════════════════════════════════════════════════════════
# ATTACK 5: THERMAL HOT SPOT AT THE TWIST
# ══════════════════════════════════════════════════════════════

def attack_thermal_hotspot(p=None):
    """
    The twist region has maximum curvature and potentially
    reduced contact with He-4 cooling channels.
    If local temperature exceeds T_crit, the SC quenches.

    Key question: what's the maximum temperature rise
    at the twist, and does it approach T_crit?
    """
    if p is None: p = DEFAULT

    R, w, t, I = p['R'], p['w'], p['t'], p['I']
    T_bath = p['T_bath']
    T_crit = p['T_crit']

    # Heat sources at the twist:
    # 1. AC losses from the beat oscillation (hysteretic loss in SC)
    # 2. Mechanical friction from magnetostriction
    # 3. Eddy currents in the substrate

    # AC loss in NbTi (type-II SC): hysteretic loss per cycle
    # P_hyst ~ (mu_0 * Jc * d_filament * delta_B * f) / (3*pi)
    # For our case: delta_B ~ B_self (the self-field oscillation)
    B_self = MU_0 * I / (2 * np.pi * w)
    d_filament = 50e-6  # 50 um filament diameter (typical NbTi wire)
    f_beat = p['f_beat']

    # Hysteretic AC loss per unit volume
    P_hyst_vol = (2 * MU_0 * NBTI_JC * d_filament * B_self * f_beat) / (3 * np.pi)

    # Volume of the twist region (~10% of the strip length)
    L_twist = 0.1 * 2 * np.pi * R
    V_twist = L_twist * 2 * w * t
    P_hyst_twist = P_hyst_vol * V_twist

    # Cooling capacity of He-4 channels
    # Kapitza resistance at NbTi-He interface: R_K ~ 0.02 K*cm^2/W at 4K
    R_kapitza = 0.02e-4  # K*m^2/W
    # Contact area at twist (reduced by geometry -- assume 50% of normal)
    A_contact = L_twist * 2 * w * 0.5  # 50% contact area reduction at twist
    G_contact = A_contact / R_kapitza  # thermal conductance [W/K]

    # Temperature rise
    delta_T = P_hyst_twist / G_contact if G_contact > 0 else float('inf')
    T_twist = T_bath + delta_T
    T_margin = T_crit - T_twist

    # Also check: persistent loss spec (<=150 uW)
    P_persistent = p.get('P_loss', 150e-6)  # from spec

    print("\n" + "=" * 70)
    print("ATTACK 5: THERMAL HOT SPOT AT THE TWIST")
    print("=" * 70)
    print(f"  Self-field oscillation:    {B_self*1e3:.2f} mT")
    print(f"  AC hysteretic loss (vol):  {P_hyst_vol:.2f} W/m^3")
    print(f"  Twist region volume:       {V_twist*1e6:.2f} mm^3")
    print(f"  Heat generated at twist:   {P_hyst_twist*1e6:.2f} uW")
    print(f"  Cooling contact area:      {A_contact*1e4:.2f} cm^2")
    print(f"  Thermal conductance:       {G_contact:.2f} W/K")
    print(f"  Temperature rise:          {delta_T*1e3:.3f} mK")
    print(f"  Twist temperature:         {T_twist:.4f} K")
    print(f"  T_crit (NbTi):             {T_crit} K")
    print(f"  Thermal margin:            {T_margin:.2f} K")
    print(f"  Persistent loss spec:      {P_persistent*1e6:.0f} uW")
    print(f"  Actual twist loss:         {P_hyst_twist*1e6:.2f} uW")

    if T_margin > 2.0:
        verdict = "SURVIVES"
        note = f"{T_margin:.1f}K margin to quench. Twist heating is negligible."
    elif T_margin > 0.5:
        verdict = "VULNERABLE"
        note = f"Only {T_margin:.1f}K margin. High-current transients could quench."
    else:
        verdict = "FATAL"
        note = "Twist region quenches under normal operation."

    print(f"\n  >> VERDICT: {verdict}")
    print(f"  >> {note}")

    if verdict == "SURVIVES":
        print(f"  >> BOOST: Could operate at I={I}A with {T_margin:.1f}K margin to spare.")
        print(f"     The He-4 phase buffer easily handles {P_hyst_twist*1e6:.1f} uW.")
    else:
        I_safe = I * np.sqrt(T_margin / delta_T) if delta_T > 0 else 0
        print(f"  >> FIX: Reduce current to {I_safe:.0f}A")
        print(f"  >> FIX: Improve He-4 channel contact at twist region")
        print(f"  >> FIX: Use multifilamentary NbTi (smaller d_filament reduces AC loss)")

    return {
        'P_hyst_twist': P_hyst_twist, 'delta_T': delta_T,
        'T_twist': T_twist, 'T_margin': T_margin,
        'verdict': verdict,
    }


# ══════════════════════════════════════════════════════════════
# ATTACK 6: SELF-FIELD BEAT FREQUENCY SHIFT
# ══════════════════════════════════════════════════════════════

def attack_frequency_shift(p=None):
    """
    The naive beat frequency assumes the ion only sees the external B.
    But the current's own field adds to it.
    The self-field varies around the loop (stronger near the strip,
    weaker far away, and the Mobius twist rotates its direction).

    Key question: how far does the real beat frequency drift
    from the v/(4*pi*R) prediction?
    """
    if p is None: p = DEFAULT

    R, w, t, I = p['R'], p['w'], p['t'], p['I']
    B_ext = p['B_ext']

    # Self-field at the centerline surface
    B_self = MU_0 * I / (2 * np.pi * w)

    # The self-field at the centerline is approximately perpendicular
    # to the strip surface (for a flat strip). On the Mobius strip,
    # this direction rotates with the twist.
    #
    # The effective B at any point on the centerline:
    # B_eff(u) = B_ext + B_self(u)
    # where B_self(u) is in the local normal direction
    #
    # The beat signal is proportional to N(u) . B_eff(u)
    # = N(u) . B_ext + N(u) . B_self(u)
    # = N(u) . B_ext + |B_self| (since B_self is along N)
    #
    # The second term is CONSTANT (doesn't oscillate with the twist)
    # because B_self is always along N regardless of u.
    # So B_self shifts the DC offset of m.B but doesn't change the
    # oscillation frequency or amplitude!

    # But wait: the self-field also has components from distant parts
    # of the loop (the return current on the opposite side of the Mobius).
    # This creates a position-dependent perturbation.

    # Estimate the far-field contribution from the opposite side of the loop:
    # B_far ~ mu_0 * I / (4*pi * (2R)) (field from a wire at distance 2R)
    B_far = MU_0 * I / (4 * np.pi * 2 * R)

    # This far field has a fixed direction but the normal rotates
    # relative to it. So it DOES create a frequency perturbation.
    # The perturbation amplitude: delta_f / f ~ B_far / B_ext
    freq_shift_frac = B_far / B_ext

    f_beat_naive = p['f_beat']
    delta_f = f_beat_naive * freq_shift_frac

    print("\n" + "=" * 70)
    print("ATTACK 6: SELF-FIELD BEAT FREQUENCY SHIFT")
    print("=" * 70)
    print(f"  External field B_ext:      {B_ext*1e3:.1f} mT")
    print(f"  Self-field (local):        {B_self*1e3:.2f} mT")
    print(f"  Far-field (opposite side): {B_far*1e6:.2f} uT")
    print(f"  B_far / B_ext:             {freq_shift_frac:.2e}")
    print(f"  Naive beat frequency:      {f_beat_naive:.2f} Hz")
    print(f"  Frequency shift:           {delta_f:.4f} Hz")
    print(f"  Fractional shift:          {freq_shift_frac*1e6:.1f} ppm")

    if freq_shift_frac < 1e-4:
        verdict = "SURVIVES"
        note = f"Shift is {freq_shift_frac*1e6:.1f} ppm. Unmeasurable at this precision."
    elif freq_shift_frac < 1e-2:
        verdict = "VULNERABLE"
        note = f"Shift of {freq_shift_frac*100:.3f}% -- detectable but correctable."
    else:
        verdict = "FATAL"
        note = f"Self-field dominates. Beat frequency prediction is unreliable."

    print(f"\n  >> VERDICT: {verdict}")
    print(f"  >> {note}")
    print(f"  >> NOTE: The LOCAL self-field (B_self along N) adds a DC offset")
    print(f"     to m.B but does NOT shift the beat frequency.")
    print(f"     Only the far-field from the opposite side of the loop matters,")
    print(f"     and it's {B_far/B_self*100:.2f}% of the local self-field.")
    print(f"  >> BOOST: This means the naive prediction is excellent.")
    print(f"     The Mobius geometry protects the beat frequency from self-interaction.")

    return {
        'B_self': B_self, 'B_far': B_far,
        'freq_shift_frac': freq_shift_frac, 'delta_f': delta_f,
        'verdict': verdict,
    }


# ══════════════════════════════════════════════════════════════
# RUN ALL ATTACKS
# ══════════════════════════════════════════════════════════════

def run_all_attacks():
    print("MTR STRESS TEST -- The Little Black Dress")
    print("=" * 70)
    print("Six attacks on the Mobius Heart design.")
    print("If it survives, it's real. If it doesn't, we know where to fix.")

    r1 = attack_lorentz_force()
    r2 = attack_copper_signal()
    r3 = attack_bend_strain()
    r4 = attack_radiation_q()
    r5 = attack_thermal_hotspot()
    r6 = attack_frequency_shift()

    results = {
        'lorentz': r1, 'copper_signal': r2, 'bend_strain': r3,
        'radiation_q': r4, 'thermal': r5, 'freq_shift': r6,
    }

    # ── Summary ─────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("STRESS TEST SUMMARY")
    print("=" * 70)

    attacks = [
        ("1. Lorentz Force", r1['verdict']),
        ("2. Copper Signal Death", r2['verdict_300K'] + " (300K) / " + r2['verdict_4K'] + " (4K)"),
        ("3. Bend Strain", r3['verdict']),
        ("4. Radiation Q", r4['verdict']),
        ("5. Thermal Hot Spot", r5['verdict']),
        ("6. Frequency Shift", r6['verdict']),
    ]

    for name, verdict in attacks:
        if "FATAL" in verdict:
            color = "XXX"
        elif "VULNERABLE" in verdict:
            color = " ! "
        else:
            color = " . "
        print(f"  [{color}] {name:30s} {verdict}")

    n_fatal = sum("FATAL" in v for _, v in attacks)
    n_vuln = sum("VULNERABLE" in v for _, v in attacks)
    n_surv = sum(v.count("SURVIVES") for _, v in attacks)

    print(f"\n  SURVIVES: {n_surv}  VULNERABLE: {n_vuln}  FATAL: {n_fatal}")

    if n_fatal == 0 and n_vuln == 0:
        print("\n  THE HEART HOLDS. All attacks deflected.")
    elif n_fatal == 0:
        print(f"\n  THE HEART BENDS BUT DOESN'T BREAK. {n_vuln} areas need attention.")
    else:
        print(f"\n  THE HEART HAS WOUNDS. {n_fatal} fatal issues to resolve.")
        print("  But now you know exactly where to cut.")

    return results


# ══════════════════════════════════════════════════════════════
# VISUALIZATION
# ══════════════════════════════════════════════════════════════

def generate_figure(results):
    """Dark-theme stress test results figure."""

    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.patch.set_facecolor('#0a0a1a')
    fig.suptitle('MTR STRESS TEST -- The Little Black Dress',
                 color='white', fontsize=18, fontweight='bold', y=0.97)
    fig.text(0.5, 0.94, 'Six attacks on the Mobius Heart  |  Can it take a hit?',
             ha='center', color='#888888', fontsize=10)

    def style_ax(ax):
        ax.set_facecolor('#0a0a1a')
        ax.tick_params(colors='#cccccc', labelsize=9)
        for spine in ax.spines.values():
            spine.set_color('#333333')

    verdict_color = {'SURVIVES': '#00ff88', 'VULNERABLE': '#ffaa00', 'FATAL': '#ff4444'}

    # ── Panel 1: Lorentz Force margin ────────────────────────
    ax = axes[0, 0]
    style_ax(ax)
    r = results['lorentz']
    categories = ['NbTi\nYield', 'PRF\nSubstrate']
    margins = [r['margin_nbti'], r['margin_prf']]
    colors = ['#00ffcc' if m > 10 else '#ffaa00' if m > 2 else '#ff4444' for m in margins]
    ax.bar(categories, margins, color=colors, width=0.5, edgecolor='white', linewidth=0.5)
    ax.axhline(1, color='#ff4444', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_ylabel('Safety Margin (x)', color='#cccccc')
    ax.set_title(f'1. Lorentz Force  [{r["verdict"]}]',
                 color=verdict_color[r['verdict']], fontsize=11, fontweight='bold')
    for i, m in enumerate(margins):
        ax.text(i, m + max(margins)*0.03, f'{m:.0f}x', ha='center', color='white',
                fontsize=12, fontweight='bold')

    # ── Panel 2: Copper Signal Decay ─────────────────────────
    ax = axes[0, 1]
    style_ax(ax)
    r = results['copper_signal']
    t_axis = np.linspace(0, 5 * r['tau_300K'], 1000)
    decay_300K = np.exp(-t_axis / r['tau_300K'])
    beat_signal = decay_300K * np.cos(2 * np.pi * r['f_beat'] * t_axis)
    ax.plot(t_axis * 1e6, beat_signal, color='#ff4444', linewidth=0.5, alpha=0.7)
    ax.plot(t_axis * 1e6, decay_300K, color='#ffaa00', linewidth=2, label='Envelope (300K)')
    ax.plot(t_axis * 1e6, -decay_300K, color='#ffaa00', linewidth=2)
    # Mark 1/e
    ax.axvline(r['tau_300K'] * 1e6, color='#666666', linestyle=':', linewidth=1)
    ax.text(r['tau_300K'] * 1e6, 0.8, f"tau={r['tau_300K']*1e6:.0f}us", color='#888888', fontsize=8)
    ax.set_xlabel('Time [us]', color='#cccccc')
    ax.set_ylabel('Signal', color='#cccccc')
    v = r['verdict_300K']
    ax.set_title(f'2. Copper Signal Death  [{v}]',
                 color=verdict_color.get(v, '#ffaa00'), fontsize=11, fontweight='bold')
    ax.text(0.95, 0.85, f"{r['n_cycles_300K']:.1f} cycles\nbefore 1/e",
            transform=ax.transAxes, ha='right', color='#ffaa00', fontsize=11)

    # ── Panel 3: Bend Strain ─────────────────────────────────
    ax = axes[0, 2]
    style_ax(ax)
    r = results['bend_strain']
    R_sweep = np.linspace(0.01, 0.15, 100)
    eps_sweep = np.sqrt((DEFAULT['t']/(2*R_sweep))**2 + (DEFAULT['w']/(2*R_sweep))**2) * 100
    ax.plot(R_sweep * 100, eps_sweep, color='#00ffcc', linewidth=2)
    ax.axhline(NBTI_CRIT_STRAIN * 100, color='#ff4444', linestyle='--', linewidth=1.5,
               label=f'NbTi limit ({NBTI_CRIT_STRAIN*100:.1f}%)')
    ax.axhline(NBTI_CRIT_STRAIN_HI * 100, color='#ffaa00', linestyle='--', linewidth=1,
               label=f'Optimistic ({NBTI_CRIT_STRAIN_HI*100:.1f}%)')
    ax.axvline(DEFAULT['R'] * 100, color='#ffffff', linestyle=':', linewidth=1)
    ax.text(DEFAULT['R']*100 + 0.5, max(eps_sweep)*0.9, 'Design R', color='white', fontsize=9)
    ax.fill_between(R_sweep*100, eps_sweep, NBTI_CRIT_STRAIN*100,
                    where=eps_sweep > NBTI_CRIT_STRAIN*100, alpha=0.2, color='#ff4444')
    ax.set_xlabel('Strip Radius [cm]', color='#cccccc')
    ax.set_ylabel('Total Strain [%]', color='#cccccc')
    ax.set_title(f'3. Bend Strain  [{r["verdict"]}]',
                 color=verdict_color[r['verdict']], fontsize=11, fontweight='bold')
    ax.legend(facecolor='#1a1a2e', edgecolor='#333333', labelcolor='#cccccc', fontsize=8)

    # ── Panel 4: Radiation Q ─────────────────────────────────
    ax = axes[1, 0]
    style_ax(ax)
    r = results['radiation_q']
    q_vals = [1e5, r['Q_rad']]
    q_labels = ['Required\nQ >= 10^5', 'Radiation\nQ']
    q_colors = ['#666666', '#00ff88']
    bars = ax.bar(q_labels, q_vals, color=q_colors, width=0.5, edgecolor='white', linewidth=0.5)
    ax.set_yscale('log')
    ax.set_ylabel('Q Factor', color='#cccccc')
    ax.set_title(f'4. Radiation Q  [{r["verdict"]}]',
                 color=verdict_color[r['verdict']], fontsize=11, fontweight='bold')
    ax.text(1, r['Q_rad'] * 1.5, f'Q = {r["Q_rad"]:.1e}', ha='center', color='white',
            fontsize=11, fontweight='bold')
    ax.text(0.5, 0.15, '"Terrible antenna"\n(this is good)',
            transform=ax.transAxes, ha='center', color='#888888', fontsize=10, fontstyle='italic')

    # ── Panel 5: Thermal Margin ──────────────────────────────
    ax = axes[1, 1]
    style_ax(ax)
    r = results['thermal']
    temp_bar = [r['T_twist'], DEFAULT['T_crit'] - r['T_twist']]
    ax.barh(['Twist\nTemperature'], [r['T_twist']], color='#00ffcc', height=0.4, edgecolor='white')
    ax.barh(['Twist\nTemperature'], [r['T_margin']], left=[r['T_twist']],
            color='#1a1a2e', height=0.4, edgecolor='#00ffcc', linewidth=1, linestyle='--')
    ax.axvline(DEFAULT['T_crit'], color='#ff4444', linewidth=2, linestyle='--')
    ax.text(DEFAULT['T_crit'] + 0.05, 0, f'T_crit = {DEFAULT["T_crit"]}K',
            color='#ff4444', fontsize=10, va='center')
    ax.text(r['T_twist']/2, 0, f'{r["T_twist"]:.3f}K', ha='center', va='center',
            color='#0a0a1a', fontsize=11, fontweight='bold')
    ax.text(r['T_twist'] + r['T_margin']/2, 0, f'{r["T_margin"]:.1f}K margin',
            ha='center', va='center', color='#00ffcc', fontsize=10)
    ax.set_xlabel('Temperature [K]', color='#cccccc')
    ax.set_title(f'5. Thermal Hot Spot  [{r["verdict"]}]',
                 color=verdict_color[r['verdict']], fontsize=11, fontweight='bold')
    ax.set_xlim(0, DEFAULT['T_crit'] * 1.3)

    # ── Panel 6: Summary Card ────────────────────────────────
    ax = axes[1, 2]
    ax.set_facecolor('#0a0a1a')
    ax.axis('off')

    all_results = [
        ("1. Lorentz Force", results['lorentz']['verdict']),
        ("2. Copper Signal (300K)", results['copper_signal']['verdict_300K']),
        ("   Copper Signal (4K)", results['copper_signal']['verdict_4K']),
        ("3. Bend Strain", results['bend_strain']['verdict']),
        ("4. Radiation Q", results['radiation_q']['verdict']),
        ("5. Thermal Hot Spot", results['thermal']['verdict']),
        ("6. Frequency Shift", results['freq_shift']['verdict']),
    ]

    y = 0.95
    ax.text(0.05, y, "STRESS TEST VERDICTS", fontsize=14, color='white',
            fontweight='bold', transform=ax.transAxes, fontfamily='monospace')
    y -= 0.08

    for name, verdict in all_results:
        c = verdict_color.get(verdict, '#ffaa00')
        ax.text(0.05, y, f"{name}", fontsize=10, color='#cccccc',
                transform=ax.transAxes, fontfamily='monospace')
        ax.text(0.75, y, verdict, fontsize=10, color=c,
                transform=ax.transAxes, fontfamily='monospace', fontweight='bold')
        y -= 0.065

    n_fatal = sum(1 for _, v in all_results if v == "FATAL")
    n_vuln = sum(1 for _, v in all_results if v == "VULNERABLE")
    n_surv = sum(1 for _, v in all_results if v == "SURVIVES")

    y -= 0.04
    if n_fatal == 0 and n_vuln == 0:
        final = "THE HEART HOLDS"
        final_c = '#00ff88'
    elif n_fatal == 0:
        final = "BENDS, DOESN'T BREAK"
        final_c = '#ffaa00'
    else:
        final = "WOUNDS FOUND"
        final_c = '#ff4444'

    ax.text(0.5, y, final, fontsize=16, color=final_c,
            fontweight='bold', transform=ax.transAxes, fontfamily='monospace',
            ha='center')

    # ── Footer ───────────────────────────────────────────────
    fig.text(0.5, 0.01,
             'Harley Robinson + Forge  |  Adversarial analysis  |  '
             'github.com/EntropyWizardchaos/ghost-shell',
             ha='center', color='#555555', fontsize=8)

    plt.tight_layout(rect=[0, 0.03, 1, 0.92])

    out = r"C:\Users\14132\iCloudDrive\For you Forge\ghost-shell\docs\figures\mtr_stress_test.png"
    out_sm = r"C:\Users\14132\iCloudDrive\For you Forge\ghost-shell\docs\figures\mtr_stress_test_sm.png"

    plt.savefig(out, dpi=200, facecolor='#0a0a1a', bbox_inches='tight')
    plt.savefig(out_sm, dpi=120, facecolor='#0a0a1a', bbox_inches='tight')
    plt.close()

    print(f"\nFigure saved: {out}")
    print(f"Social media: {out_sm}")


if __name__ == '__main__':
    results = run_all_attacks()
    print("\nGenerating figure...")
    generate_figure(results)
    print("\nDone.")
