# cognitive_lattice_v1.py
# GHOST SHELL — Brain Organ: Cognitive Lattice (Photonic Neural Core)
# Completes the Heart (MTR) / Brain (this) / Spleen (Quantum Spleen) triad
#
# Blueprint bench tests:
#   Phase 0: 4x4 MZI mesh — linear algebra fidelity >= 95%
#   Phase 1: Optical phase stability — drift < 0.05 rad/min under cryo
#   Phase 2: Adaptive tuning — gradient update converges
#   Phase 3: Myridian interface — bioluminescent pulse -> optical weight shift
#   Phase 4: Memory store/retrieve — >= 80% recall after cold storage
#
# Architecture layers:
#   PRF cranial frame    — structural (implicit, provides cryogenic envelope)
#   MZI tile array       — logic & transformation (this file, core)
#   Quantum buffer       — short-term coherence store (He-4 cavity)
#   Myridian interface   — sensory bridge (bioluminescent optical input)
#   Cryo-control plane   — phase stabilization (superconducting trim coils)
#
# UEES coupling: entropy drain lambda_D driven by MTR thermal leakage

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import time


# ============================================================
# 1. MZI MESH — Reck decomposition, 4x4 unitary
# ============================================================

class MZIMesh:
    """
    4x4 Mach-Zehnder interferometer mesh.
    Implements Reck decomposition: any unitary U(N) as a product of
    N(N-1)/2 two-mode beam splitters with tunable phases.

    Each MZI unit: U_ij(theta, phi) applies a 2x2 rotation in the
    (i,j) subspace with phase shift phi on one arm.
    """

    def __init__(self, n: int = 4, seed: int = 42):
        self.n = n
        rng = np.random.RandomState(seed)
        # Reck triangle: n(n-1)/2 = 6 MZI units for n=4
        self.n_units = n * (n - 1) // 2
        self.theta = rng.uniform(0, np.pi, self.n_units)
        self.phi = rng.uniform(0, 2 * np.pi, self.n_units)
        # Diagonal output phases (completes the parameterization)
        # Without these, can only reach a subgroup of U(N)
        self.diag_phase = rng.uniform(0, 2 * np.pi, n)
        # Build index pairs for Reck triangle (column-major)
        self.pairs = []
        for col in range(n - 1):
            for row in range(n - 1, col, -1):
                self.pairs.append((row - 1, row))

    def _unit_matrix(self, idx: int) -> np.ndarray:
        """2x2 MZI unitary for unit idx."""
        t = np.cos(self.theta[idx])
        r = np.sin(self.theta[idx])
        p = np.exp(1j * self.phi[idx])
        return np.array([[t, -r * np.conj(p)],
                         [r * p, t]], dtype=np.complex128)

    def build_unitary(self) -> np.ndarray:
        """Construct the full NxN unitary from all MZI units + diagonal phases."""
        U = np.eye(self.n, dtype=np.complex128)
        for idx, (i, j) in enumerate(self.pairs):
            T = np.eye(self.n, dtype=np.complex128)
            u2 = self._unit_matrix(idx)
            T[i, i] = u2[0, 0]
            T[i, j] = u2[0, 1]
            T[j, i] = u2[1, 0]
            T[j, j] = u2[1, 1]
            U = T @ U
        # Apply diagonal phase screen (output phases)
        D = np.diag(np.exp(1j * self.diag_phase))
        return D @ U

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass: x (real or complex, length n) -> y (complex)."""
        x = np.asarray(x, dtype=np.complex128)
        U = self.build_unitary()
        return U @ x

    def fidelity_vs_target(self, U_target: np.ndarray) -> float:
        """Fidelity = |Tr(U_target^dag @ U)|^2 / N^2."""
        U = self.build_unitary()
        overlap = np.trace(U_target.conj().T @ U)
        return float(np.abs(overlap) ** 2 / self.n ** 2)

    def set_to_target(self, U_target: np.ndarray, lr: float = 0.01,
                      steps: int = 2000, noise_std: float = 0.0) -> List[float]:
        """
        Optimize MZI phases to realize U_target.
        Uses Frobenius norm ||U - U_target||_F as loss (smoother landscape
        than fidelity metric, avoids local optima).
        Returns fidelity history.
        """
        history = []
        eps = 1e-4

        def frob_loss():
            U = self.build_unitary()
            return float(np.sum(np.abs(U - U_target) ** 2))

        for step in range(steps):
            f0 = self.fidelity_vs_target(U_target)
            history.append(f0)
            if f0 > 0.9999:
                break

            # Finite-difference gradient on Frobenius loss (minimizing)
            for k in range(self.n_units):
                self.theta[k] += eps
                lp = frob_loss()
                self.theta[k] -= 2 * eps
                lm = frob_loss()
                self.theta[k] += eps
                self.theta[k] -= lr * (lp - lm) / (2 * eps)

                self.phi[k] += eps
                lp = frob_loss()
                self.phi[k] -= 2 * eps
                lm = frob_loss()
                self.phi[k] += eps
                self.phi[k] -= lr * (lp - lm) / (2 * eps)

            # Also optimize diagonal output phases
            for k in range(self.n):
                self.diag_phase[k] += eps
                lp = frob_loss()
                self.diag_phase[k] -= 2 * eps
                lm = frob_loss()
                self.diag_phase[k] += eps
                self.diag_phase[k] -= lr * (lp - lm) / (2 * eps)

            if noise_std > 0:
                self.theta += np.random.randn(self.n_units) * noise_std
                self.phi += np.random.randn(self.n_units) * noise_std

        return history


# ============================================================
# 2. CRYO-CONTROL PLANE — Phase stabilization
# ============================================================

class CryoControlPlane:
    """
    Superconducting trim coils + micro-thermo-optic tuners.
    Maintains phase stability under thermal noise.

    Models:
    - Thermal drift: Brownian noise on phases, amplitude ~ T_he4
    - Trim correction: PID-like feedback that measures output fidelity
      and applies compensating phase shifts
    - Interlock: if T_he4 > 7.5 K, disable all drive (safety)
    """

    def __init__(self, mesh: MZIMesh, T_he4: float = 4.2):
        self.mesh = mesh
        self.T_he4 = T_he4  # Kelvin
        self.trim_gain = 0.3  # correction strength
        self.drift_history = []
        # Store reference phases for trim correction
        self.ref_theta = mesh.theta.copy()
        self.ref_phi = mesh.phi.copy()
        self.ref_diag = mesh.diag_phase.copy()

    def thermal_drift_step(self, dt_seconds: float = 1.0) -> float:
        """
        Apply one step of thermal drift. Returns max phase drift (rad).
        Drift amplitude scales with T_he4: at 4.2K, drift is minimal.
        At 7.5K (interlock), drift is significant.

        Physical basis: phase noise ~ sqrt(k_B * T / E_photon)
        For He-4 at 4.2K with optical photons (~1eV):
          sigma ~ sqrt(1.38e-23 * 4.2 / 1.6e-19) ~ 6e-13 rad/sqrt(s)
        We scale this up for simulation visibility while keeping
        the ratio between 4.2K and 7.5K correct.
        """
        if self.T_he4 > 7.5:
            return float('inf')  # interlock: system unsafe

        # Scale factor: normalized so 4.2K gives ~0.001 rad/step
        sigma = 0.001 * np.sqrt(self.T_he4 / 4.2) * np.sqrt(dt_seconds)
        noise_theta = np.random.randn(self.mesh.n_units) * sigma
        noise_phi = np.random.randn(self.mesh.n_units) * sigma
        noise_diag = np.random.randn(self.mesh.n) * sigma

        self.mesh.theta += noise_theta
        self.mesh.phi += noise_phi
        self.mesh.diag_phase += noise_diag

        max_drift = max(np.max(np.abs(noise_theta)),
                        np.max(np.abs(noise_phi)),
                        np.max(np.abs(noise_diag)))
        self.drift_history.append(max_drift)
        return max_drift

    def trim_correct(self):
        """
        Apply trim correction to pull phases back toward reference.
        Models superconducting trim coils that sense drift and compensate.
        """
        if self.T_he4 > 7.5:
            return  # interlock active, no correction

        d_theta = self.ref_theta - self.mesh.theta
        d_phi = self.ref_phi - self.mesh.phi
        d_diag = self.ref_diag - self.mesh.diag_phase
        self.mesh.theta += self.trim_gain * d_theta
        self.mesh.phi += self.trim_gain * d_phi
        self.mesh.diag_phase += self.trim_gain * d_diag

    def update_reference(self):
        """Snapshot current phases as new reference (after learning)."""
        self.ref_theta = self.mesh.theta.copy()
        self.ref_phi = self.mesh.phi.copy()
        self.ref_diag = self.mesh.diag_phase.copy()

    def measure_drift_rate(self, duration_steps: int = 60,
                           dt_per_step: float = 1.0) -> float:
        """
        Measure phase drift rate in rad/min over duration.
        Applies trim correction each step (as the real system would).
        Returns max drift rate in rad/min.
        """
        self.update_reference()
        theta_start = self.mesh.theta.copy()
        phi_start = self.mesh.phi.copy()
        diag_start = self.mesh.diag_phase.copy()

        for _ in range(duration_steps):
            self.thermal_drift_step(dt_per_step)
            self.trim_correct()

        max_theta_drift = np.max(np.abs(self.mesh.theta - theta_start))
        max_phi_drift = np.max(np.abs(self.mesh.phi - phi_start))
        max_diag_drift = np.max(np.abs(self.mesh.diag_phase - diag_start))
        total_minutes = duration_steps * dt_per_step / 60.0
        drift_rate = max(max_theta_drift, max_phi_drift, max_diag_drift) / total_minutes

        # Restore
        self.mesh.theta = theta_start
        self.mesh.phi = phi_start
        self.mesh.diag_phase = diag_start

        return drift_rate


# ============================================================
# 3. MYRIDIAN INTERFACE — Sensory bridge
# ============================================================

class MyridianInterface:
    """
    Bioluminescent optical input grid.
    Converts ionic/chemical signals from Myridian neural substrate
    into phase-encoded optical pulses for the MZI mesh.

    Physical basis:
    - Myridian operates at 280-310K (bio-compatible)
    - Bioluminescent proteins emit photons at specific wavelengths
    - Photons are fiber-coupled into the cryo PRF cranial frame
    - Wavelength -> phase mapping: phi = 2*pi*n*L / lambda

    In simulation: input vectors (representing sensor readings)
    are converted to optical amplitudes + phases.
    """

    def __init__(self, n_channels: int = 4, sensitivity: float = 1.0):
        self.n_channels = n_channels
        self.sensitivity = sensitivity
        # Wavelength-to-phase conversion factors (per channel)
        self.phase_offsets = np.linspace(0, np.pi / 2, n_channels)
        # Gain adaptation (models bioluminescent protein expression levels)
        self.gain = np.ones(n_channels)
        self.gain_adapt_rate = 0.01

    def encode(self, raw_signal: np.ndarray) -> np.ndarray:
        """
        Convert raw sensor signal to optical input for MZI mesh.
        raw_signal: real-valued array of length n_channels
        Returns: complex optical field amplitudes
        """
        raw = np.asarray(raw_signal[:self.n_channels], dtype=float)
        # Normalize to [0, 1] range
        amplitude = np.clip(raw * self.sensitivity * self.gain, 0, 1)
        # Phase encoding: amplitude modulates intensity,
        # channel position determines phase offset
        optical = amplitude * np.exp(1j * self.phase_offsets)
        return optical

    def adapt_gain(self, raw_signal: np.ndarray, mesh_output: np.ndarray):
        """
        Adjust bioluminescent gain based on output utilization.
        If a channel's output is always near zero, boost its gain.
        If saturated, reduce gain. Models protein expression adaptation.
        """
        output_power = np.abs(mesh_output) ** 2
        target_power = np.mean(output_power)
        for i in range(self.n_channels):
            if output_power[i] < target_power * 0.5:
                self.gain[i] *= (1 + self.gain_adapt_rate)
            elif output_power[i] > target_power * 2.0:
                self.gain[i] *= (1 - self.gain_adapt_rate)
        self.gain = np.clip(self.gain, 0.1, 10.0)

    def pulse(self, raw_signal: np.ndarray, mesh: MZIMesh) -> np.ndarray:
        """
        Full Myridian pulse: encode -> mesh forward -> adapt.
        Returns mesh output (complex optical field).
        """
        optical_in = self.encode(raw_signal)
        optical_out = mesh.forward(optical_in)
        self.adapt_gain(raw_signal, optical_out)
        return optical_out


# ============================================================
# 4. QUANTUM BUFFER — Superconducting memory
# ============================================================

class QuantumBuffer:
    """
    He-4 cavity with photon-phonon coupling nodes.
    Stores phase patterns in superconducting loops.

    Physical basis:
    - Persistent current loops in superconducting material
    - Each loop stores a phase state (theta, phi pair)
    - Recall fidelity degrades with time and temperature
    - At 4.2K: coherence time >> 1 hour
    - At 7.5K: coherence time ~ minutes (approaching Tc)

    Memory model:
    - Store: snapshot MZI phases + associated input/output pattern
    - Recall: restore phases, measure fidelity vs original
    - Decay: exponential decay of phase precision with time
    """

    @dataclass
    class MemorySlot:
        theta: np.ndarray
        phi: np.ndarray
        diag_phase: np.ndarray
        input_pattern: np.ndarray
        output_pattern: np.ndarray
        store_time: float
        label: str = ""

    def __init__(self, n_slots: int = 16, T_he4: float = 4.2):
        self.n_slots = n_slots
        self.T_he4 = T_he4
        self.slots: List[Optional['QuantumBuffer.MemorySlot']] = [None] * n_slots
        self.clock = 0.0  # internal time counter

    def store(self, mesh: MZIMesh, input_pattern: np.ndarray,
              output_pattern: np.ndarray, label: str = "") -> int:
        """
        Store current mesh state + I/O pattern in next available slot.
        Returns slot index, or -1 if full.
        """
        for i, slot in enumerate(self.slots):
            if slot is None:
                self.slots[i] = self.MemorySlot(
                    theta=mesh.theta.copy(),
                    phi=mesh.phi.copy(),
                    diag_phase=mesh.diag_phase.copy(),
                    input_pattern=input_pattern.copy(),
                    output_pattern=output_pattern.copy(),
                    store_time=self.clock,
                    label=label
                )
                return i
        return -1  # buffer full

    def recall(self, slot_idx: int, mesh: MZIMesh) -> Tuple[float, np.ndarray]:
        """
        Restore mesh to stored state. Returns (fidelity, output).
        Fidelity accounts for time-dependent decoherence.
        """
        slot = self.slots[slot_idx]
        if slot is None:
            return 0.0, np.zeros(mesh.n)

        elapsed = self.clock - slot.store_time
        # Coherence decay: T1 time depends on temperature
        # At 4.2K: T1 ~ 10000 time units (hours)
        # At 7.0K: T1 ~ 100 time units (minutes)
        T1 = 10000.0 * np.exp(-0.5 * (self.T_he4 - 4.2))
        decay = np.exp(-elapsed / T1)

        # Apply stored phases with decay-induced noise
        noise_std = 0.01 * (1 - decay)
        mesh.theta = slot.theta.copy() + np.random.randn(mesh.n_units) * noise_std
        mesh.phi = slot.phi.copy() + np.random.randn(mesh.n_units) * noise_std
        mesh.diag_phase = slot.diag_phase.copy() + np.random.randn(mesh.n) * noise_std

        # Measure recall fidelity via cosine similarity of output power
        recalled_output = mesh.forward(slot.input_pattern)
        # Use power distributions (real, positive) for stable comparison
        p_orig = np.abs(slot.output_pattern) ** 2
        p_recall = np.abs(recalled_output) ** 2
        dot = np.sum(p_orig * p_recall)
        norm = np.sqrt(np.sum(p_orig ** 2) * np.sum(p_recall ** 2))
        fidelity = float(dot / (norm + 1e-15))

        return fidelity, recalled_output

    def advance_clock(self, dt: float):
        self.clock += dt

    def clear(self, slot_idx: int):
        self.slots[slot_idx] = None

    def occupancy(self) -> int:
        return sum(1 for s in self.slots if s is not None)


# ============================================================
# 5. UEES COUPLING — Energy dynamics (from Ghost Shell Codex)
# ============================================================

@dataclass
class UEESState:
    E_G: float = 0.3   # Growth energy
    E_M: float = 0.4   # Maintenance energy
    E_R: float = 0.1   # Retention energy (need/tension)
    C: float = 0.1     # Coherence
    O: float = 0.0     # Optimism
    V: float = 0.0     # Tension (bad-mass)
    Tm: float = 0.5    # Mentor trust
    h: int = 0         # Hysteresis bit
    V_ema: float = 0.0 # Smoothed tension
    stage: str = "Infant"
    t: int = 0


class UEESBrainCoupling:
    """
    Couples UEES energy dynamics to the Cognitive Lattice.

    Key mappings:
    - lambda_D (entropy drain) <- MTR thermal leakage per cycle (0.003 K)
      NOT a constant. Scales with mesh computational load.
    - Coherence C drives MZI learning rate (higher C = finer tuning)
    - E_R (retention) modulates memory store urgency
    - V (tension) triggers memory recall (search for solutions)
    - Stage gates control which lattice layers are active

    The brain doesn't just USE UEES — it IS a UEES subsystem.
    The lattice's computational activity generates E_R (unresolved
    patterns), and successful pattern matching drains E_R into E_G.
    """

    # UEES parameters
    a = 1.0       # tension coefficient
    b = 0.5       # optimism damping on V
    theta_lo = 0.25
    theta_hi = 0.35
    d_max = 0.8
    lam_R = 0.1
    k_c1 = 0.6
    k_c2 = 0.3
    k_o1 = 0.8
    k_o2 = 0.2
    lam_O = 0.15
    kappa_T = 0.5
    T0 = 0.5
    eps_T = 0.1
    alpha_ema = 0.1

    def __init__(self):
        self.state = UEESState()
        self.history: List[Dict] = []

    def compute_lambda_D(self, mesh: MZIMesh, input_signal: np.ndarray) -> float:
        """
        Entropy drain from MTR thermal leakage.
        Scales with computational load: more interference operations
        = more energy dissipated as heat into the He-4 bath.

        Physical: each MZI switching event leaks delta_T = 0.003 K.
        More active modes = more leakage.
        """
        output = mesh.forward(input_signal)
        # Computational load ~ how much the mesh transforms the input
        # (distance between input and output distributions)
        power_in = np.sum(np.abs(input_signal) ** 2)
        power_out = np.sum(np.abs(output) ** 2)
        redistribution = np.sum(np.abs(
            np.abs(output) ** 2 / (power_out + 1e-15) -
            np.abs(input_signal) ** 2 / (power_in + 1e-15)
        ))
        # Base drain + load-dependent component
        lambda_D = 0.15 + 0.15 * redistribution
        return float(np.clip(lambda_D, 0.1, 0.5))

    def step(self, A_t: float, lambda_D: float, learning_success: float):
        """
        One UEES timestep for the brain subsystem.

        A_t: adversity (unresolved input patterns)
        lambda_D: entropy drain from MTR (computed from mesh load)
        learning_success: how well the mesh learned this step [0,1]
        """
        s = self.state

        # Tension
        V = self.a * s.E_R * (1 - s.C) - self.b * s.O

        # Hysteresis
        if V > self.theta_hi:
            h = 1
        elif V < self.theta_lo:
            h = 0
        else:
            h = s.h

        # Effort (brain's internal reflection drive)
        u = 0.5  # base internal effort
        u_eff = min(u + h * s.Tm * 0.3, 1.0)

        # Core flows
        # learning_success converts E_R -> E_G (resolved patterns)
        dER = A_t + (1 - s.C) - self.d_max * u_eff - self.lam_R * s.E_R
        dER -= learning_success * 0.3  # successful learning drains retention
        dC = self.k_c1 * u_eff * (1 - s.C) - self.k_c2 * s.E_R * s.C
        dC += learning_success * 0.1  # successful learning builds coherence
        dO = self.k_o1 * s.C - self.k_o2 * s.E_R - self.lam_O * s.O

        dt = 1.0
        ER_new = np.clip(s.E_R + dt * dER, 0.0, 2.0)
        C_new = np.clip(s.C + dt * dC, 0.0, 1.0)
        O_new = np.clip(s.O + dt * dO, 0.0, 1.0)

        # Mentor trust
        V_ema = (1 - self.alpha_ema) * s.V_ema + self.alpha_ema * V
        delta_V = s.V_ema - V
        Tm_new = self.kappa_T * np.tanh(delta_V / self.eps_T) + \
                 (1 - self.kappa_T) * (s.Tm - self.T0)
        Tm_new = np.clip(Tm_new, 0.0, 1.0)

        # Stage transitions
        stage = s.stage
        stages = ["Infant", "Juvenile", "Apprentice", "Adult"]
        idx = stages.index(stage)
        C_thresholds = [0.6, 0.8, 0.9]
        if idx < 3 and C_new >= C_thresholds[idx]:
            stage = stages[idx + 1]
        elif idx > 0 and C_new < C_thresholds[idx - 1]:
            stage = stages[idx - 1]

        # Learning rate modulation by coherence
        # Higher C = finer, more precise phase adjustments
        # Lower C = coarser, more exploratory
        self.current_lr = 0.005 + 0.045 * C_new  # 0.005 at C=0, 0.05 at C=1

        log = {
            't': s.t, 'V': V, 'h': h, 'u_eff': u_eff,
            'lambda_D': lambda_D, 'stage': stage,
            'ER': ER_new, 'C': C_new, 'O': O_new, 'Tm': Tm_new,
            'learning_success': learning_success
        }
        self.history.append(log)

        self.state = UEESState(
            E_G=s.E_G, E_M=s.E_M, E_R=ER_new,
            C=C_new, O=O_new, V=V,
            Tm=Tm_new, h=h, V_ema=V_ema,
            stage=stage, t=s.t + 1
        )

        return log


# ============================================================
# 6. COGNITIVE LATTICE — Full brain organ
# ============================================================

class CognitiveLattice:
    """
    The complete brain organ for the Ghost Shell.

    Integrates:
    - MZI mesh (optical cortex)
    - Cryo-control plane (phase stabilization)
    - Myridian interface (sensory input)
    - Quantum buffer (memory)
    - UEES coupling (energy dynamics)

    Sits in PRF cranial frame at 50-200K (inner) to 280K (outer).
    MZI core operates at cryo boundary (7.5-50K).
    Myridian interface at 280-310K, fiber-coupled across thermal gap.
    """

    def __init__(self, seed: int = 42):
        self.mesh = MZIMesh(n=4, seed=seed)
        self.cryo = CryoControlPlane(self.mesh, T_he4=4.2)
        self.myridian = MyridianInterface(n_channels=4)
        self.memory = QuantumBuffer(n_slots=16, T_he4=4.2)
        self.uees = UEESBrainCoupling()
        self.step_count = 0

    def process(self, raw_signal: np.ndarray, target: Optional[np.ndarray] = None,
                adversity: float = 0.3) -> Dict:
        """
        One cognitive cycle:
        1. Myridian encodes raw signal to optical
        2. MZI mesh transforms (inference)
        3. If target given, compute learning error and update phases
        4. Cryo plane applies drift + correction
        5. UEES updates energy state
        6. If tension high, search memory; if success, store memory

        Returns dict of results and diagnostics.
        """
        # 1. Sensory encoding
        optical_in = self.myridian.encode(raw_signal)

        # 2. Inference
        optical_out = self.mesh.forward(optical_in)
        output_power = np.abs(optical_out) ** 2

        # 3. Learning
        learning_success = 0.0
        if target is not None:
            target_c = np.asarray(target, dtype=np.complex128)
            error = np.sum(np.abs(target_c - optical_out) ** 2)
            max_error = np.sum(np.abs(target_c) ** 2) + np.sum(np.abs(optical_out) ** 2)
            learning_success = max(0, 1 - error / (max_error + 1e-15))

            # Gradient update on MZI phases (rate modulated by UEES coherence)
            lr = getattr(self.uees, 'current_lr', 0.02)
            eps = 1e-4

            def loss_fn():
                y = self.mesh.forward(optical_in)
                return float(np.sum(np.abs(target_c - y) ** 2))

            base_loss = loss_fn()
            for k in range(self.mesh.n_units):
                # theta
                self.mesh.theta[k] += eps
                lp = loss_fn()
                self.mesh.theta[k] -= 2 * eps
                lm = loss_fn()
                self.mesh.theta[k] += eps
                grad = (lp - lm) / (2 * eps)
                self.mesh.theta[k] -= lr * grad

                # phi
                self.mesh.phi[k] += eps
                lp = loss_fn()
                self.mesh.phi[k] -= 2 * eps
                lm = loss_fn()
                self.mesh.phi[k] += eps
                grad = (lp - lm) / (2 * eps)
                self.mesh.phi[k] -= lr * grad

        # 4. Cryo drift + correction
        self.cryo.thermal_drift_step(dt_seconds=1.0)
        self.cryo.trim_correct()
        self.cryo.update_reference()

        # 5. UEES step
        lambda_D = self.uees.compute_lambda_D(self.mesh, optical_in)
        uees_log = self.uees.step(adversity, lambda_D, learning_success)

        # 6. Memory management
        mem_action = "none"
        # High tension + low coherence -> search memory
        if self.uees.state.V > 0.3 and self.uees.state.C < 0.7:
            best_fid = 0
            best_slot = -1
            for i, slot in enumerate(self.memory.slots):
                if slot is not None:
                    # Check input similarity
                    sim = np.abs(np.vdot(slot.input_pattern, optical_in))
                    sim /= (np.linalg.norm(slot.input_pattern) *
                            np.linalg.norm(optical_in) + 1e-15)
                    if sim > best_fid:
                        best_fid = sim
                        best_slot = i
            if best_slot >= 0 and best_fid > 0.5:
                fid, _ = self.memory.recall(best_slot, self.mesh)
                mem_action = f"recall(slot={best_slot}, fid={fid:.3f})"

        # Good learning -> store for future recall
        elif learning_success > 0.8 and self.uees.state.C > 0.7:
            slot_idx = self.memory.store(
                self.mesh, optical_in, optical_out,
                label=f"step_{self.step_count}"
            )
            if slot_idx >= 0:
                mem_action = f"store(slot={slot_idx})"

        self.memory.advance_clock(1.0)
        self.step_count += 1

        return {
            'step': self.step_count,
            'output_power': output_power,
            'learning_success': learning_success,
            'lambda_D': lambda_D,
            'mem_action': mem_action,
            'uees': uees_log,
            'stage': self.uees.state.stage,
            'C': self.uees.state.C,
        }


# ============================================================
# 7. BENCH TESTS
# ============================================================

def run_bench_tests():
    """Run all 5 bench test phases from the blueprint."""
    results = {}
    np.random.seed(42)

    # ── Phase 0: MZI Mesh Fidelity ──
    print("=" * 60)
    print("PHASE 0: 4x4 MZI Mesh — Linear Algebra Fidelity")
    print("=" * 60)

    # Generate a random unitary target (Haar-distributed)
    from scipy.stats import unitary_group
    U_target = unitary_group.rvs(4)

    mesh = MZIMesh(n=4, seed=0)
    history = mesh.set_to_target(U_target, lr=0.1, steps=10000)
    final_fidelity = history[-1]

    # Also verify linearity: U(ax + by) = a*U(x) + b*U(y)
    x = np.random.randn(4) + 1j * np.random.randn(4)
    y = np.random.randn(4) + 1j * np.random.randn(4)
    a, b = 0.6 + 0.2j, 0.3 - 0.1j
    lhs = mesh.forward(a * x + b * y)
    rhs = a * mesh.forward(x) + b * mesh.forward(y)
    linearity = 1.0 - np.linalg.norm(lhs - rhs) / (np.linalg.norm(lhs) + 1e-15)

    passed_0 = final_fidelity >= 0.95
    results['phase_0'] = {
        'fidelity': final_fidelity,
        'linearity': linearity,
        'steps': len(history),
        'passed': passed_0
    }
    print(f"  Fidelity vs target unitary: {final_fidelity:.4f}")
    print(f"  Linearity check:            {linearity:.6f}")
    print(f"  Converged in:               {len(history)} steps")
    print(f"  PASS: {passed_0}  (threshold: >= 0.95)")
    print()

    # ── Phase 1: Optical Phase Stability ──
    print("=" * 60)
    print("PHASE 1: Optical Phase Stability Under Cryo")
    print("=" * 60)

    mesh1 = MZIMesh(n=4, seed=1)
    cryo = CryoControlPlane(mesh1, T_he4=4.2)
    drift_rate = cryo.measure_drift_rate(duration_steps=600, dt_per_step=1.0)

    passed_1 = drift_rate < 0.05
    results['phase_1'] = {
        'drift_rate_rad_per_min': drift_rate,
        'T_he4': 4.2,
        'passed': passed_1
    }
    print(f"  He-4 temperature:  {4.2} K")
    print(f"  Drift rate:        {drift_rate:.6f} rad/min")
    print(f"  PASS: {passed_1}  (threshold: < 0.05 rad/min)")
    print()

    # ── Phase 2: Adaptive Tuning ──
    print("=" * 60)
    print("PHASE 2: Adaptive Tuning — Gradient Convergence")
    print("=" * 60)

    # Task: learn a specific input->output mapping
    mesh2 = MZIMesh(n=4, seed=2)
    myridian = MyridianInterface(n_channels=4)

    # Training data: 8 input/output pairs from a target unitary
    # Train directly on complex optical inputs (Myridian tested separately in Phase 3)
    U_learn = unitary_group.rvs(4)
    train_inputs_raw = [np.random.randn(4) + 1j * np.random.randn(4) for _ in range(8)]
    # Normalize inputs
    train_inputs_c = [x / (np.linalg.norm(x) + 1e-15) for x in train_inputs_raw]
    train_targets = [U_learn @ x for x in train_inputs_c]

    losses = []
    for epoch in range(800):
        epoch_loss = 0
        for optical_in, y_target in zip(train_inputs_c, train_targets):
            optical_out = mesh2.forward(optical_in)
            loss = np.sum(np.abs(y_target - optical_out) ** 2)
            epoch_loss += loss

            # Gradient step on all parameters (theta, phi, diag_phase)
            lr = 0.08
            eps = 1e-4
            for k in range(mesh2.n_units):
                mesh2.theta[k] += eps
                lp = np.sum(np.abs(y_target - mesh2.forward(optical_in)) ** 2)
                mesh2.theta[k] -= 2 * eps
                lm = np.sum(np.abs(y_target - mesh2.forward(optical_in)) ** 2)
                mesh2.theta[k] += eps
                mesh2.theta[k] -= lr * (lp - lm) / (2 * eps)

                mesh2.phi[k] += eps
                lp = np.sum(np.abs(y_target - mesh2.forward(optical_in)) ** 2)
                mesh2.phi[k] -= 2 * eps
                lm = np.sum(np.abs(y_target - mesh2.forward(optical_in)) ** 2)
                mesh2.phi[k] += eps
                mesh2.phi[k] -= lr * (lp - lm) / (2 * eps)

            for k in range(mesh2.n):
                mesh2.diag_phase[k] += eps
                lp = np.sum(np.abs(y_target - mesh2.forward(optical_in)) ** 2)
                mesh2.diag_phase[k] -= 2 * eps
                lm = np.sum(np.abs(y_target - mesh2.forward(optical_in)) ** 2)
                mesh2.diag_phase[k] += eps
                mesh2.diag_phase[k] -= lr * (lp - lm) / (2 * eps)

        losses.append(epoch_loss / len(train_inputs_c))

    converged = losses[-1] < losses[0] * 0.1  # 90% reduction
    passed_2 = converged
    results['phase_2'] = {
        'initial_loss': losses[0],
        'final_loss': losses[-1],
        'reduction': 1 - losses[-1] / (losses[0] + 1e-15),
        'epochs': len(losses),
        'passed': passed_2
    }
    print(f"  Initial loss:  {losses[0]:.4f}")
    print(f"  Final loss:    {losses[-1]:.4f}")
    print(f"  Reduction:     {(1 - losses[-1] / (losses[0] + 1e-15)) * 100:.1f}%")
    print(f"  PASS: {passed_2}  (threshold: >= 90% reduction)")
    print()

    # ── Phase 3: Myridian Interface ──
    print("=" * 60)
    print("PHASE 3: Myridian Interface — Bioluminescent Pulse")
    print("=" * 60)

    mesh3 = MZIMesh(n=4, seed=3)
    myridian3 = MyridianInterface(n_channels=4)

    # Test: different raw signals should produce different optical outputs
    signals = [
        np.array([1.0, 0.0, 0.0, 0.0]),  # channel 1 only
        np.array([0.0, 1.0, 0.0, 0.0]),  # channel 2 only
        np.array([0.5, 0.5, 0.5, 0.5]),  # uniform
        np.array([1.0, 0.5, 0.2, 0.1]),  # gradient
    ]

    outputs = []
    for sig in signals:
        out = myridian3.pulse(sig, mesh3)
        outputs.append(out)

    # Check discriminability: outputs should be distinct
    min_dist = float('inf')
    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            d = np.linalg.norm(outputs[i] - outputs[j])
            min_dist = min(min_dist, d)

    # Check gain adaptation over repeated pulses
    initial_gain = myridian3.gain.copy()
    for _ in range(100):
        sig = np.array([1.0, 0.01, 0.01, 0.01])  # channel 1 dominant
        myridian3.pulse(sig, mesh3)
    gain_adapted = not np.allclose(myridian3.gain, initial_gain, atol=0.05)

    passed_3 = min_dist > 0.01 and gain_adapted
    results['phase_3'] = {
        'min_output_distance': min_dist,
        'gain_adapted': gain_adapted,
        'final_gain': myridian3.gain.tolist(),
        'passed': passed_3
    }
    print(f"  Min output distance:  {min_dist:.4f}  (need > 0.01)")
    print(f"  Gain adaptation:      {gain_adapted}")
    print(f"  Adapted gains:        {np.round(myridian3.gain, 3)}")
    print(f"  PASS: {passed_3}")
    print()

    # ── Phase 4: Memory Store/Retrieve ──
    print("=" * 60)
    print("PHASE 4: Memory Store/Retrieve — Cold Storage Recall")
    print("=" * 60)

    mesh4 = MZIMesh(n=4, seed=4)
    mem = QuantumBuffer(n_slots=16, T_he4=4.2)
    myridian4 = MyridianInterface(n_channels=4)

    # Store 4 patterns
    patterns_stored = []
    for i in range(4):
        raw = np.random.randn(4)
        optical_in = myridian4.encode(raw)
        optical_out = mesh4.forward(optical_in)
        slot = mem.store(mesh4, optical_in, optical_out, label=f"pattern_{i}")
        patterns_stored.append({
            'slot': slot, 'input': optical_in.copy(),
            'output': optical_out.copy()
        })

    # Advance clock (simulate 1 hour = 3600 time units)
    mem.advance_clock(3600.0)

    # Scramble mesh phases (simulate other computation happened)
    mesh4.theta = np.random.uniform(0, np.pi, mesh4.n_units)
    mesh4.phi = np.random.uniform(0, 2 * np.pi, mesh4.n_units)
    mesh4.diag_phase = np.random.uniform(0, 2 * np.pi, mesh4.n)

    # Recall each pattern
    recall_fidelities = []
    for p in patterns_stored:
        fid, recalled_out = mem.recall(p['slot'], mesh4)
        recall_fidelities.append(fid)

    avg_recall = np.mean(recall_fidelities)
    passed_4 = avg_recall >= 0.80
    results['phase_4'] = {
        'recall_fidelities': [float(f) for f in recall_fidelities],
        'average_recall': avg_recall,
        'elapsed_time': 3600.0,
        'T_he4': 4.2,
        'passed': passed_4
    }
    print(f"  Stored patterns:    {len(patterns_stored)}")
    print(f"  Cold storage time:  3600 time units (1 hour equivalent)")
    print(f"  Recall fidelities:  {[f'{f:.3f}' for f in recall_fidelities]}")
    print(f"  Average recall:     {avg_recall:.4f}")
    print(f"  PASS: {passed_4}  (threshold: >= 0.80)")
    print()

    # ── INTEGRATED RUN ──
    print("=" * 60)
    print("INTEGRATED RUN: Full Cognitive Lattice (200 steps)")
    print("=" * 60)

    lattice = CognitiveLattice(seed=42)
    U_task = unitary_group.rvs(4)

    for step in range(200):
        raw = np.random.randn(4) * 0.5
        target = U_task @ np.asarray(raw, dtype=np.complex128)
        adversity = 0.3 + 0.2 * np.sin(0.05 * step)
        if step in [80, 150]:
            adversity += 1.0  # shock

        result = lattice.process(raw, target=target, adversity=adversity)

        if step % 50 == 0 or step == 199:
            print(f"  Step {step:3d} | {result['stage']:11s} | "
                  f"C={result['C']:.3f} | "
                  f"learn={result['learning_success']:.3f} | "
                  f"lD={result['lambda_D']:.3f} | "
                  f"mem: {result['mem_action']}")

    # ── SUMMARY ──
    print()
    print("=" * 60)
    print("BENCH TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for phase, r in results.items():
        status = "PASS" if r['passed'] else "FAIL"
        if not r['passed']:
            all_passed = False
        print(f"  {phase}: {status}")
    print(f"\n  ALL PHASES: {'PASS' if all_passed else 'FAIL'}")
    print("=" * 60)

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    run_bench_tests()
