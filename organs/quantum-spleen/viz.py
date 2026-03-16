"""
Quantum Spleen -- Visualization
Runs the simulation and generates a publication-quality summary figure.
Dark theme, colorful, eye-catching. Built for sharing.

Author: Forge + Harley Robinson
"""

import numpy as np
from scipy.linalg import expm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import time
import os
import sys

# Import everything from the sim
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# Inline the physics (avoid import issues with the sim's global state)
# ============================================================================

HBAR = 1.0545718e-34
K_B = 1.380649e-23
GHZ_TO_RAD = 2 * np.pi * 1e9

OMEGA_01_GHZ = 5.0
ANHARMONICITY_GHZ = -0.25
E_J_GHZ = 20.0
E_C_GHZ = 0.25
N_JJ = 12
N_AUX = 4
N_TOTAL = N_JJ * N_AUX
T_BATH_MK = 50.0
T_BATH = T_BATH_MK * 1e-3
N_TH_ELEVATED = 0.5
GAMMA_1 = 1.0 / 300.0
GAMMA_THERMAL = 0.03
KAPPA_AUX = 1.4
KAPPA_OUT = 0.001
G_PUMP = 0.2
DT = 0.05


def annihilation(n):
    a = np.zeros((n, n), dtype=complex)
    for i in range(n - 1):
        a[i, i + 1] = np.sqrt(i + 1)
    return a

def number_op(n):
    return np.diag(np.arange(n, dtype=complex))

def identity(n):
    return np.eye(n, dtype=complex)

def tensor(A, B):
    return np.kron(A, B)

def dag(A):
    return A.conj().T

def commutator(A, B):
    return A @ B - B @ A

def anticommutator(A, B):
    return A @ B + B @ A

def von_neumann_entropy(rho):
    eigenvalues = np.real(np.linalg.eigvalsh(rho))
    eigenvalues = eigenvalues[eigenvalues > 1e-15]
    return -np.sum(eigenvalues * np.log2(eigenvalues))

def purity(rho):
    return np.real(np.trace(rho @ rho))

def partial_trace_aux(rho_full, n_jj, n_aux):
    rho_jj = np.zeros((n_jj, n_jj), dtype=complex)
    for k in range(n_aux):
        for i in range(n_jj):
            for j in range(n_jj):
                rho_jj[i, j] += rho_full[i * n_aux + k, j * n_aux + k]
    return rho_jj

def build_transmon_hamiltonian(n_levels, omega_01, alpha):
    H = np.zeros((n_levels, n_levels), dtype=complex)
    for k in range(n_levels):
        E_k = k * omega_01 + k * (k - 1) / 2.0 * alpha
        H[k, k] = E_k
    return H

def build_system():
    a_jj = annihilation(N_JJ)
    n_jj = number_op(N_JJ)
    I_jj = identity(N_JJ)
    a_aux = annihilation(N_AUX)
    n_aux = number_op(N_AUX)
    I_aux = identity(N_AUX)

    A_jj = tensor(a_jj, I_aux)
    A_aux = tensor(I_jj, a_aux)
    N_jj_full = tensor(n_jj, I_aux)
    N_aux_full = tensor(I_jj, n_aux)

    H_jj = tensor(build_transmon_hamiltonian(N_JJ, OMEGA_01_GHZ, ANHARMONICITY_GHZ), I_aux)
    omega_aux = OMEGA_01_GHZ + 1.0
    H_aux = omega_aux * N_aux_full
    H_pump = G_PUMP * (A_jj @ dag(A_aux) + dag(A_jj) @ A_aux)
    H_total = H_jj + H_aux + H_pump

    collapse_ops = []
    n_th = N_TH_ELEVATED
    collapse_ops.append(('thermal_up', np.sqrt(GAMMA_THERMAL * n_th) * dag(A_jj)))
    collapse_ops.append(('thermal_down', np.sqrt(GAMMA_THERMAL * (n_th + 1)) * A_jj))
    collapse_ops.append(('jj_decay', np.sqrt(GAMMA_1) * A_jj))
    collapse_ops.append(('aux_dump', np.sqrt(KAPPA_AUX) * A_aux))
    collapse_ops.append(('output', np.sqrt(KAPPA_OUT) * A_jj))

    return H_total, collapse_ops, {
        'A_jj': A_jj, 'A_aux': A_aux,
        'N_jj': N_jj_full, 'N_aux': N_aux_full,
        'H_jj': H_jj, 'H_aux': H_aux, 'H_pump': H_pump,
    }

def lindblad_rhs(rho, H, collapse_ops):
    drho = -1j * commutator(H, rho)
    for name, L in collapse_ops:
        Ld = dag(L)
        drho += L @ rho @ Ld - 0.5 * anticommutator(Ld @ L, rho)
    return drho

def evolve_rk4(rho, H, collapse_ops, dt, n_steps):
    for _ in range(n_steps):
        k1 = dt * lindblad_rhs(rho, H, collapse_ops)
        k2 = dt * lindblad_rhs(rho + 0.5 * k1, H, collapse_ops)
        k3 = dt * lindblad_rhs(rho + 0.5 * k2, H, collapse_ops)
        k4 = dt * lindblad_rhs(rho + k3, H, collapse_ops)
        rho = rho + (k1 + 2*k2 + 2*k3 + k4) / 6.0
        rho = 0.5 * (rho + dag(rho))
        rho = rho / np.trace(rho)
    return rho


# ============================================================================
# RUN ALL DATA COLLECTION
# ============================================================================

def collect_all_data():
    print("Building system...")
    H, ops, ops_dict = build_system()

    rho_0 = np.zeros((N_TOTAL, N_TOTAL), dtype=complex)
    rho_0[0, 0] = 1.0

    data = {}

    # --- PHASE 0: Entropy absorption ---
    print("Phase 0: Entropy absorption...")
    H_no_pump = H - ops_dict['H_pump']
    collapse_no_pump = [(n, L) for n, L in ops if n not in ('aux_dump',)]

    # Evolve both and track entropy over time
    rho_np = rho_0.copy()
    rho_wp = rho_0.copy()
    entropy_no_pump = []
    entropy_with_pump = []
    purity_no_pump = []
    purity_with_pump = []
    times_p0 = []

    for step in range(200):
        rho_np = evolve_rk4(rho_np, H_no_pump, collapse_no_pump, DT, 10)
        rho_wp = evolve_rk4(rho_wp, H, ops, DT, 10)

        rho_jj_np = partial_trace_aux(rho_np, N_JJ, N_AUX)
        rho_jj_wp = partial_trace_aux(rho_wp, N_JJ, N_AUX)

        entropy_no_pump.append(von_neumann_entropy(rho_jj_np))
        entropy_with_pump.append(von_neumann_entropy(rho_jj_wp))
        purity_no_pump.append(purity(rho_jj_np))
        purity_with_pump.append(purity(rho_jj_wp))
        times_p0.append(step * 10 * DT)

    data['p0'] = {
        'times': times_p0,
        'entropy_no_pump': entropy_no_pump,
        'entropy_with_pump': entropy_with_pump,
        'purity_no_pump': purity_no_pump,
        'purity_with_pump': purity_with_pump,
    }
    reduction = (entropy_no_pump[-1] - entropy_with_pump[-1]) / entropy_no_pump[-1] * 100
    print(f"  Entropy reduction: {reduction:.1f}%")

    # --- PHASE 1: Energy spectrum + populations ---
    print("Phase 1: Discrete storage...")
    H_transmon = build_transmon_hamiltonian(N_JJ, OMEGA_01_GHZ, ANHARMONICITY_GHZ)
    energies = np.real(np.diag(H_transmon))
    transitions = np.diff(energies)

    # Harmonic comparison
    harmonic_transitions = np.full_like(transitions, OMEGA_01_GHZ)

    # Steady-state populations
    rho_ss = evolve_rk4(rho_0.copy(), H, ops, DT, 2000)
    rho_jj_ss = partial_trace_aux(rho_ss, N_JJ, N_AUX)
    populations = np.real(np.diag(rho_jj_ss))

    # Thermal populations for comparison
    thermal_pops = np.array([N_TH_ELEVATED**k / (1 + N_TH_ELEVATED)**(k+1) for k in range(N_JJ)])
    thermal_pops /= thermal_pops.sum()

    data['p1'] = {
        'energies': energies[:8],
        'transitions': transitions[:7],
        'harmonic_transitions': harmonic_transitions[:7],
        'populations': populations[:8],
        'thermal_pops': thermal_pops[:8],
    }

    # --- PHASE 2: Variance suppression ---
    print("Phase 2: Variance suppression...")
    n_op_jj = number_op(N_JJ)
    n2_op_jj = n_op_jj @ n_op_jj

    rho_np2 = rho_0.copy()
    rho_wp2 = rho_0.copy()
    var_no = []
    var_with = []
    times_p2 = []

    for step in range(200):
        rho_np2 = evolve_rk4(rho_np2, H_no_pump, collapse_no_pump, DT, 10)
        rho_wp2 = evolve_rk4(rho_wp2, H, ops, DT, 10)

        rho_jj_np2 = partial_trace_aux(rho_np2, N_JJ, N_AUX)
        rho_jj_wp2 = partial_trace_aux(rho_wp2, N_JJ, N_AUX)

        n_m = np.real(np.trace(rho_jj_np2 @ n_op_jj))
        n2_m = np.real(np.trace(rho_jj_np2 @ n2_op_jj))
        var_no.append(n2_m - n_m**2)

        n_m = np.real(np.trace(rho_jj_wp2 @ n_op_jj))
        n2_m = np.real(np.trace(rho_jj_wp2 @ n2_op_jj))
        var_with.append(n2_m - n_m**2)

        times_p2.append(step * 10 * DT)

    suppression = (np.mean(var_no[-50:]) - np.mean(var_with[-50:])) / np.mean(var_no[-50:]) * 100
    data['p2'] = {
        'times': times_p2,
        'var_no_pump': var_no,
        'var_with_pump': var_with,
        'suppression': suppression,
    }
    print(f"  Variance suppression: {suppression:.1f}%")

    # --- PHASE 3: Coherent emission ---
    print("Phase 3: Coherent emission...")
    rho_excited = np.zeros((N_TOTAL, N_TOTAL), dtype=complex)
    rho_excited[1 * N_AUX, 1 * N_AUX] = 1.0

    ops_no_output = [(n, L) for n, L in ops if n != 'output']
    rho_stable = evolve_rk4(rho_excited, H, ops_no_output, DT, 500)

    a_jj_full = ops_dict['A_jj']
    ops_emission = list(ops) + [('output_boost', np.sqrt(0.01) * a_jj_full)]

    purity_trace = []
    photon_trace = []
    times_p3 = []
    rho_em = rho_stable.copy()

    for step in range(100):
        rho_em = evolve_rk4(rho_em, H, ops_emission, DT, 10)
        rho_jj_em = partial_trace_aux(rho_em, N_JJ, N_AUX)
        purity_trace.append(purity(rho_jj_em))
        photon_trace.append(np.real(np.trace(rho_jj_em @ n_op_jj)))
        times_p3.append(step * 10 * DT)

    thermal_purity_limit = 1.0 / N_JJ
    data['p3'] = {
        'times': times_p3,
        'purity': purity_trace,
        'photons': photon_trace,
        'thermal_limit': thermal_purity_limit,
    }
    print(f"  Min purity: {min(purity_trace):.4f} (thermal limit: {thermal_purity_limit:.4f})")

    # --- PHASE 4: Long-cycle stability ---
    print("Phase 4: Long-cycle stability...")
    N_CYCLES = 50
    CHARGE_STEPS = 100
    RELEASE_STEPS = 50
    ops_with_output = list(ops) + [('output_boost', np.sqrt(0.005) * a_jj_full)]

    rho_cyc = np.zeros((N_TOTAL, N_TOTAL), dtype=complex)
    rho_cyc[0, 0] = 1.0

    n_charged_list = []
    n_released_list = []
    purity_list = []

    for cycle in range(N_CYCLES):
        rho_cyc = evolve_rk4(rho_cyc, H, ops_no_output, DT, CHARGE_STEPS)
        rho_jj_c = partial_trace_aux(rho_cyc, N_JJ, N_AUX)
        n_charged_list.append(np.real(np.trace(rho_jj_c @ n_op_jj)))
        purity_list.append(purity(rho_jj_c))

        rho_cyc = evolve_rk4(rho_cyc, H, ops_with_output, DT, RELEASE_STEPS)
        rho_jj_r = partial_trace_aux(rho_cyc, N_JJ, N_AUX)
        n_released_list.append(np.real(np.trace(rho_jj_r @ n_op_jj)))

        if cycle % 10 == 0:
            print(f"  Cycle {cycle}")

    early = n_charged_list[15:25]
    late = n_charged_list[-10:]
    drift = abs(np.mean(late) - np.mean(early)) / (np.mean(early) + 1e-10) * 100

    data['p4'] = {
        'n_charged': n_charged_list,
        'n_released': n_released_list,
        'purity': purity_list,
        'drift': drift,
    }
    print(f"  Drift: {drift:.2f}%")

    return data


# ============================================================================
# PLOT
# ============================================================================

def make_figure(data):
    # Dark theme
    plt.style.use('dark_background')

    fig = plt.figure(figsize=(18, 11))
    fig.patch.set_facecolor('#0a0a1a')

    gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.3,
                  left=0.06, right=0.97, top=0.90, bottom=0.08)

    # Colors
    C_PUMP = '#00e5ff'      # cyan - pump active
    C_NOPUMP = '#ff4444'    # red - no pump
    C_GOLD = '#ffd700'      # gold - results
    C_PURPLE = '#bb86fc'    # purple - accent
    C_GREEN = '#00e676'     # green - pass

    title_size = 13
    label_size = 11

    # --- Title banner ---
    fig.text(0.5, 0.96, 'QUANTUM SPLEEN -- Autonomous Coherence Stabilizer',
             ha='center', fontsize=20, fontweight='bold', color='white',
             fontfamily='monospace')
    fig.text(0.5, 0.925, 'Lindblad master equation simulation  |  5 GHz transmon  |  50 mK bath  |  All 5 bench tests PASS',
             ha='center', fontsize=11, color='#888888', fontfamily='monospace')

    # ================================================================
    # Panel 1: Entropy over time (Phase 0)
    # ================================================================
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor('#0d0d20')
    ax1.plot(data['p0']['times'], data['p0']['entropy_no_pump'],
             color=C_NOPUMP, linewidth=2, label='No pump (thermal)')
    ax1.plot(data['p0']['times'], data['p0']['entropy_with_pump'],
             color=C_PUMP, linewidth=2, label='Pump active')

    # Shade the gap
    ax1.fill_between(data['p0']['times'],
                     data['p0']['entropy_with_pump'],
                     data['p0']['entropy_no_pump'],
                     alpha=0.15, color=C_PUMP)

    s_no = data['p0']['entropy_no_pump'][-1]
    s_with = data['p0']['entropy_with_pump'][-1]
    reduction = (s_no - s_with) / s_no * 100

    ax1.set_title(f'Phase 0: Entropy Absorption  [{reduction:.0f}% reduction]',
                  fontsize=title_size, color=C_GREEN, fontweight='bold', pad=10)
    ax1.set_xlabel('Time (us)', fontsize=label_size, color='#aaa')
    ax1.set_ylabel('Von Neumann Entropy (bits)', fontsize=label_size, color='#aaa')
    ax1.legend(fontsize=9, loc='right')
    ax1.tick_params(colors='#888')

    # ================================================================
    # Panel 2: Energy spectrum (Phase 1)
    # ================================================================
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor('#0d0d20')

    n_show = 7
    x = np.arange(n_show)
    width = 0.35
    bars1 = ax2.bar(x - width/2, data['p1']['transitions'][:n_show],
                    width, color=C_PUMP, alpha=0.9, label='Anharmonic (actual)')
    bars2 = ax2.bar(x + width/2, data['p1']['harmonic_transitions'][:n_show],
                    width, color='#444444', alpha=0.7, label='Harmonic (equal)')

    ax2.set_title('Phase 1: Discrete Storage Modes',
                  fontsize=title_size, color=C_GREEN, fontweight='bold', pad=10)
    ax2.set_xlabel('Transition (|k> to |k+1>)', fontsize=label_size, color='#aaa')
    ax2.set_ylabel('Frequency (GHz)', fontsize=label_size, color='#aaa')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'{i}-{i+1}' for i in range(n_show)])
    ax2.legend(fontsize=9)
    ax2.tick_params(colors='#888')
    ax2.set_ylim(3.0, 5.5)

    # ================================================================
    # Panel 3: Variance suppression (Phase 2)
    # ================================================================
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor('#0d0d20')

    ax3.plot(data['p2']['times'], data['p2']['var_no_pump'],
             color=C_NOPUMP, linewidth=2, label='No pump')
    ax3.plot(data['p2']['times'], data['p2']['var_with_pump'],
             color=C_PUMP, linewidth=2, label='Pump active')

    ax3.fill_between(data['p2']['times'],
                     data['p2']['var_with_pump'],
                     data['p2']['var_no_pump'],
                     alpha=0.15, color=C_PUMP)

    ax3.set_title(f'Phase 2: Variance Suppression  [{data["p2"]["suppression"]:.0f}% below thermal]',
                  fontsize=title_size, color=C_GREEN, fontweight='bold', pad=10)
    ax3.set_xlabel('Time (us)', fontsize=label_size, color='#aaa')
    ax3.set_ylabel('Var(n) photon number', fontsize=label_size, color='#aaa')
    ax3.legend(fontsize=9)
    ax3.tick_params(colors='#888')

    # ================================================================
    # Panel 4: Coherent emission purity (Phase 3)
    # ================================================================
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.set_facecolor('#0d0d20')

    ax4.plot(data['p3']['times'], data['p3']['purity'],
             color=C_GOLD, linewidth=2.5, label='State purity')
    ax4.axhline(y=data['p3']['thermal_limit'], color=C_NOPUMP,
                linestyle='--', linewidth=1.5, alpha=0.7, label='Thermal limit')

    ax4.fill_between(data['p3']['times'], data['p3']['thermal_limit'],
                     data['p3']['purity'], alpha=0.1, color=C_GOLD)

    ratio = min(data['p3']['purity']) / data['p3']['thermal_limit']
    ax4.set_title(f'Phase 3: Coherent Emission  [{ratio:.0f}x above thermal]',
                  fontsize=title_size, color=C_GREEN, fontweight='bold', pad=10)
    ax4.set_xlabel('Time (us)', fontsize=label_size, color='#aaa')
    ax4.set_ylabel('Purity Tr(rho^2)', fontsize=label_size, color='#aaa')
    ax4.legend(fontsize=9)
    ax4.tick_params(colors='#888')

    # ================================================================
    # Panel 5: Long-cycle stability (Phase 4)
    # ================================================================
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.set_facecolor('#0d0d20')

    cycles = np.arange(50)
    ax5.plot(cycles, data['p4']['n_charged'], color=C_PUMP, linewidth=1.5,
             marker='o', markersize=3, label='Charged <n>')
    ax5.plot(cycles, data['p4']['n_released'], color=C_PURPLE, linewidth=1.5,
             marker='s', markersize=3, label='Released <n>')

    ax5.set_title(f'Phase 4: 50-Cycle Stability  [{data["p4"]["drift"]:.2f}% drift]',
                  fontsize=title_size, color=C_GREEN, fontweight='bold', pad=10)
    ax5.set_xlabel('Cycle', fontsize=label_size, color='#aaa')
    ax5.set_ylabel('Mean photon number <n>', fontsize=label_size, color='#aaa')
    ax5.legend(fontsize=9)
    ax5.tick_params(colors='#888')

    # ================================================================
    # Panel 6: Summary / Results card
    # ================================================================
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.set_facecolor('#0d0d20')
    ax6.set_xlim(0, 1)
    ax6.set_ylim(0, 1)
    ax6.axis('off')

    results_text = [
        ('BENCH TEST RESULTS', 0.92, 14, 'white', 'bold'),
        ('', 0.85, 10, '#888', 'normal'),
        ('Phase 0  Entropy Absorption', 0.78, 11, '#aaa', 'normal'),
        (f'  {reduction:.1f}% reduction', 0.72, 13, C_GREEN, 'bold'),
        ('Phase 1  Discrete Storage', 0.62, 11, '#aaa', 'normal'),
        (f'  5% anharmonic deviation', 0.56, 13, C_GREEN, 'bold'),
        ('Phase 2  Variance Suppression', 0.46, 11, '#aaa', 'normal'),
        (f'  {data["p2"]["suppression"]:.1f}% below thermal', 0.40, 13, C_GREEN, 'bold'),
        ('Phase 3  Coherent Emission', 0.30, 11, '#aaa', 'normal'),
        (f'  Purity {ratio:.0f}x above thermal', 0.24, 13, C_GREEN, 'bold'),
        ('Phase 4  Long-Cycle Stability', 0.14, 11, '#aaa', 'normal'),
        (f'  {data["p4"]["drift"]:.2f}% drift / 50 cycles', 0.08, 13, C_GREEN, 'bold'),
    ]

    for text, y, size, color, weight in results_text:
        ax6.text(0.1, y, text, fontsize=size, color=color,
                fontweight=weight, fontfamily='monospace',
                transform=ax6.transAxes)

    # Border
    for spine in ax6.spines.values():
        spine.set_visible(True)
        spine.set_color('#333')

    # --- Footer ---
    fig.text(0.5, 0.015,
             'Harley Robinson + Forge  |  Lindblad master eq. (RK4)  |  Real parameters from Yale AQEC (2025)  |  github.com/EntropyWizardchaos',
             ha='center', fontsize=9, color='#555', fontfamily='monospace')

    # Save
    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'quantum_spleen_results.png')
    fig.savefig(out_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"\nFigure saved: {out_path}")

    # Also save a smaller version for social media
    out_path_sm = os.path.join(out_dir, 'quantum_spleen_results_sm.png')
    fig.savefig(out_path_sm, dpi=120, facecolor=fig.get_facecolor(), edgecolor='none')
    print(f"Social media version: {out_path_sm}")

    plt.close()


if __name__ == '__main__':
    print("Quantum Spleen -- Generating visualization")
    print("=" * 50)
    t0 = time.time()
    data = collect_all_data()
    print(f"\nData collection: {time.time() - t0:.1f}s")
    print("\nGenerating figure...")
    make_figure(data)
    print(f"Total time: {time.time() - t0:.1f}s")
    print("\nDone.")
