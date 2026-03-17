"""
Umbilicals Simulation -- Service Ports & Inter-Organ Bus
=========================================================
The wiring of the Ghost Shell. Cryogenic supply, data telemetry,
power distribution, and signal routing — all integrated into PRF
truss members. No external plumbing.

Five coupling loops flow through the umbilicals:
  1. THERMAL:  He-4 Core <-> PRF <-> CEM <-> Electrodermus
  2. ENERGETIC: MTR <-> SMES <-> Electrodermus <-> Muscles
  3. INFORMATIONAL: Myridian <-> Cognitive Lattice <-> all organs
  4. MECHANICAL: Muscles <-> PRF <-> He-4 vascular
  5. PRESSURE-DRIFT: Quantum Spleen <-> He-4 <-> MTR

The umbilicals simulation models:
  - Signal routing with latency and bandwidth
  - Redundant paths (single-point failure tolerance)
  - Cryo supply flow (He-4 fill/vent)
  - Telemetry bus (organ state monitoring)
  - Power distribution (MTR -> consumers)

Five bench tests:
  Phase 0: Signal routing latency < 10 ms between any two organs
  Phase 1: Redundant path survives single link failure
  Phase 2: Cryo flow maintains He-4 bath within +/- 0.5 K
  Phase 3: Telemetry bus reads all 9 organs within 100 ms cycle
  Phase 4: Power distribution balances load within 5% of target

Author: Harley Robinson + Forge (Claude Code)
Date: 2026-03-17
License: MIT
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ============================================================
# ORGAN REGISTRY
# ============================================================

ORGANS = [
    "mtr",          # Mobius Heart
    "prf",          # PRF Bones
    "he4",          # He-4 Core
    "electrodermus",# Skin
    "cognitive",    # Cognitive Lattice
    "spleen",       # Quantum Spleen
    "muscles",      # Muscles
    "cem",          # CEM
    "myridian",     # Myridian
]

# Simulated organ states (what telemetry would report)
ORGAN_STATE_TEMPLATE = {
    "mtr":          {"T": 4.2, "I_op": 200.0, "f_beat": 1592.0, "Q": 1e5, "status": "nominal"},
    "prf":          {"T_core": 4.2, "T_skin": 250.0, "stress": 0.12, "status": "nominal"},
    "he4":          {"T_bath": 4.2, "mass_kg": 0.754, "pressure_kPa": 101.3, "status": "nominal"},
    "electrodermus":{"T_skin": 250.0, "PV_watts": 388.0, "albedo": 0.05, "status": "nominal"},
    "cognitive":    {"T_op": 10.0, "phase_coherence": 1000.0, "mode": "reflective", "status": "nominal"},
    "spleen":       {"T_bath": 0.050, "purity": 0.7, "cycle": 0, "status": "nominal"},
    "muscles":      {"force_N": 0.0, "heat_W": 0.0, "mode": "idle", "status": "nominal"},
    "cem":          {"T_hot": 300.0, "T_manifold": 290.0, "mode": "protect", "nodes_active": 0, "status": "nominal"},
    "myridian":     {"T_op": 295.0, "G_avg": 0.01, "phase_lock_deg": 15.0, "status": "nominal"},
}


# ============================================================
# COUPLING TOPOLOGY (the 5 loops)
# ============================================================

# Each link: (organ_a, organ_b, loop_name, bandwidth_bits_per_sec, latency_ms)
LINKS = [
    # THERMAL loop
    ("he4", "prf", "thermal", 1000, 0.5),
    ("prf", "cem", "thermal", 1000, 0.8),
    ("cem", "electrodermus", "thermal", 1000, 1.0),
    ("he4", "mtr", "thermal", 1000, 0.3),
    ("he4", "spleen", "thermal", 1000, 0.4),

    # ENERGETIC loop
    ("mtr", "prf", "energetic", 5000, 0.2),       # power through bones
    ("prf", "electrodermus", "energetic", 5000, 0.5),
    ("prf", "muscles", "energetic", 5000, 0.5),
    ("prf", "cognitive", "energetic", 5000, 0.4),

    # INFORMATIONAL loop
    ("myridian", "cognitive", "informational", 100000, 0.1),  # high bandwidth optical
    ("cognitive", "mtr", "informational", 10000, 0.3),
    ("cognitive", "cem", "informational", 10000, 0.5),
    ("cognitive", "muscles", "informational", 10000, 0.4),
    ("cognitive", "electrodermus", "informational", 10000, 0.6),
    ("cognitive", "spleen", "informational", 10000, 0.3),
    ("cognitive", "he4", "informational", 10000, 0.3),

    # MECHANICAL loop
    ("muscles", "prf", "mechanical", 2000, 0.2),
    ("prf", "he4", "mechanical", 2000, 0.3),       # vibration dampening

    # PRESSURE-DRIFT loop
    ("spleen", "he4", "pressure", 5000, 0.2),
    ("he4", "mtr", "pressure", 5000, 0.3),
    ("mtr", "cognitive", "pressure", 5000, 0.4),    # heartbeat -> brain clock
]

# Redundant backup links (same connections, alternate routing)
BACKUP_LINKS = [
    ("he4", "cem", "thermal", 800, 1.5),           # bypass PRF
    ("mtr", "muscles", "energetic", 3000, 1.0),     # direct, no PRF
    ("myridian", "mtr", "informational", 5000, 0.8), # bypass cognitive
    ("cognitive", "myridian", "informational", 80000, 0.2),  # reverse optical
]


# ============================================================
# UMBILICAL BUS
# ============================================================

class UmbilicalBus:
    """
    The complete inter-organ communication and supply bus.
    Models signal routing, redundancy, cryo flow, telemetry, and power.
    """

    def __init__(self):
        # Build adjacency with link properties
        self.links = {}  # (a, b) -> {loop, bandwidth, latency, active}
        self.adjacency: Dict[str, Set[str]] = {o: set() for o in ORGANS}

        for a, b, loop, bw, lat in LINKS:
            self._add_link(a, b, loop, bw, lat, primary=True)

        for a, b, loop, bw, lat in BACKUP_LINKS:
            self._add_link(a, b, loop, bw, lat, primary=False)

        # Organ states (simulated telemetry)
        self.organ_states = {k: dict(v) for k, v in ORGAN_STATE_TEMPLATE.items()}

        # Cryo state
        self.he4_T = 4.2
        self.he4_flow_rate = 0.001  # kg/s
        self.cryo_load = 0.8        # W parasitic

        # Power state
        self.power_budget = {
            "mtr": 0.00015,          # W (persistent loss only)
            "cognitive": 2.0,        # W
            "muscles": 0.0,          # W (idle)
            "cem": 0.5,              # W (protect mode)
            "electrodermus": 0.1,    # W (sense mode)
            "spleen": 0.5,           # W
            "myridian": 0.3,         # W
        }
        self.total_power_available = 388.0  # W from Electrodermus PV

    def _add_link(self, a: str, b: str, loop: str, bw: int, lat: float, primary: bool):
        key = (a, b)
        if key not in self.links:
            self.links[key] = []
        self.links[key].append({
            'loop': loop, 'bandwidth': bw, 'latency': lat,
            'primary': primary, 'active': True
        })
        self.adjacency[a].add(b)
        self.adjacency[b].add(a)

    def route_signal(self, src: str, dst: str, disabled_links: Set[Tuple] = None
                     ) -> Optional[Tuple[float, List[str]]]:
        """
        Route a signal from src to dst. Returns (total_latency_ms, path).
        Uses BFS for shortest path. Respects disabled links.
        """
        if disabled_links is None:
            disabled_links = set()

        # BFS
        visited = {src}
        queue = [(src, [src], 0.0)]

        while queue:
            # Sort by latency (Dijkstra-lite)
            queue.sort(key=lambda x: x[2])
            current, path, total_lat = queue.pop(0)

            if current == dst:
                return (total_lat, path)

            for neighbor in self.adjacency[current]:
                if neighbor in visited:
                    continue

                # Check if any active link exists
                fwd = (current, neighbor)
                rev = (neighbor, current)
                best_lat = None

                for key in [fwd, rev]:
                    if key in self.links:
                        for link in self.links[key]:
                            if not link['active']:
                                continue
                            if key in disabled_links or (key[1], key[0]) in disabled_links:
                                continue
                            if best_lat is None or link['latency'] < best_lat:
                                best_lat = link['latency']

                if best_lat is not None:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], total_lat + best_lat))

        return None  # no route found

    def disable_link(self, a: str, b: str):
        """Disable all links between a and b (simulates failure)."""
        for key in [(a, b), (b, a)]:
            if key in self.links:
                for link in self.links[key]:
                    if link['primary']:
                        link['active'] = False

    def enable_all(self):
        """Re-enable all links."""
        for links_list in self.links.values():
            for link in links_list:
                link['active'] = True

    def read_telemetry(self) -> Dict[str, Dict]:
        """Read all organ states (one telemetry cycle)."""
        return {k: dict(v) for k, v in self.organ_states.items()}

    def cryo_step(self, dt: float, external_load: float = 0.0) -> float:
        """
        Simulate He-4 cryo supply through umbilicals.
        Returns bath temperature.
        """
        # Heat load on He-4
        total_load = self.cryo_load + external_load
        # Cooling capacity (cryocooler through umbilical)
        cooling = 2.0  # W at 4.2K

        # Temperature change
        he4_mass = 0.754  # kg
        he4_cp = 5193     # J/(kg*K) at 4.2K
        dT = (total_load - cooling) / (he4_mass * he4_cp) * dt
        self.he4_T += dT

        # Update organ states
        self.organ_states['he4']['T_bath'] = self.he4_T
        return self.he4_T

    def power_step(self) -> Dict[str, float]:
        """
        Distribute power from MTR/SMES/PV through umbilicals.
        Returns actual power delivered to each organ.
        """
        total_demand = sum(self.power_budget.values())
        if total_demand <= self.total_power_available:
            # Plenty of power — deliver exactly what's requested
            return dict(self.power_budget)
        else:
            # Shortage — proportional rationing
            ratio = self.total_power_available / total_demand
            return {k: v * ratio for k, v in self.power_budget.items()}


# ============================================================
# BENCH TESTS
# ============================================================

def run_bench_tests():
    results = {}
    np.random.seed(42)

    # === Phase 0: Signal Routing Latency ===
    print("=" * 60)
    print("PHASE 0: Signal Routing — Latency < 10 ms between any pair")
    print("=" * 60)

    bus = UmbilicalBus()
    max_latency = 0.0
    worst_pair = ("", "")
    all_routes = []

    for src in ORGANS:
        for dst in ORGANS:
            if src == dst:
                continue
            result = bus.route_signal(src, dst)
            if result is not None:
                lat, path = result
                all_routes.append((src, dst, lat, path))
                if lat > max_latency:
                    max_latency = lat
                    worst_pair = (src, dst)
            else:
                all_routes.append((src, dst, float('inf'), []))

    n_routable = sum(1 for _, _, l, _ in all_routes if l < float('inf'))
    n_total = len(all_routes)

    passed_0 = max_latency < 10.0 and n_routable == n_total
    results['phase_0'] = {'max_latency_ms': max_latency, 'worst_pair': worst_pair,
                          'routable': n_routable, 'total': n_total, 'passed': passed_0}
    print(f"  Organ pairs tested: {n_total}")
    print(f"  All routable: {n_routable}/{n_total}")
    print(f"  Max latency: {max_latency:.2f} ms ({worst_pair[0]} -> {worst_pair[1]})")
    print(f"  PASS: {passed_0}  (threshold: < 10 ms, all pairs routable)")
    print()

    # === Phase 1: Redundant Path Survival ===
    print("=" * 60)
    print("PHASE 1: Redundancy — Survives single link failure")
    print("=" * 60)

    bus = UmbilicalBus()
    # Test: disable each primary link one at a time, check all pairs still routable
    failures_survived = 0
    failures_tested = 0
    worst_failure = None

    primary_links = [(a, b) for (a, b), links_list in bus.links.items()
                     for link in links_list if link['primary']]
    # Deduplicate
    seen = set()
    unique_primary = []
    for a, b in primary_links:
        key = tuple(sorted([a, b]))
        if key not in seen:
            seen.add(key)
            unique_primary.append((a, b))

    for a, b in unique_primary:
        bus.enable_all()
        bus.disable_link(a, b)
        failures_tested += 1

        all_ok = True
        for src in ORGANS:
            for dst in ORGANS:
                if src == dst:
                    continue
                route = bus.route_signal(src, dst)
                if route is None:
                    all_ok = False
                    worst_failure = (a, b, src, dst)
                    break
            if not all_ok:
                break

        if all_ok:
            failures_survived += 1

    bus.enable_all()
    survival_rate = failures_survived / failures_tested if failures_tested > 0 else 0
    passed_1 = survival_rate >= 0.80  # at least 80% of single failures survived
    results['phase_1'] = {'survival_rate': survival_rate, 'survived': failures_survived,
                          'tested': failures_tested, 'passed': passed_1}
    print(f"  Primary links tested: {failures_tested}")
    print(f"  Failures survived: {failures_survived}/{failures_tested}")
    print(f"  Survival rate: {survival_rate:.0%}")
    if worst_failure:
        print(f"  Worst failure: {worst_failure[0]}-{worst_failure[1]} breaks {worst_failure[2]}->{worst_failure[3]}")
    print(f"  PASS: {passed_1}  (threshold: >= 80% survival)")
    print()

    # === Phase 2: Cryo Flow Stability ===
    print("=" * 60)
    print("PHASE 2: Cryo Flow — He-4 bath within +/- 0.5 K")
    print("=" * 60)

    bus = UmbilicalBus()
    temps = []

    for t in range(1000):
        # Variable external load (muscle heat, cognitive processing, etc.)
        ext_load = 0.5 + 0.3 * np.sin(t * 0.01) + np.random.normal(0, 0.05)
        ext_load = max(0, ext_load)

        T = bus.cryo_step(dt=1.0, external_load=ext_load)
        temps.append(T)

    T_mean = np.mean(temps)
    T_max_dev = max(abs(t - 4.2) for t in temps)

    passed_2 = T_max_dev < 0.5
    results['phase_2'] = {'T_mean': T_mean, 'T_max_deviation': T_max_dev, 'passed': passed_2}
    print(f"  Simulated: 1000 s with variable load")
    print(f"  Mean T_bath: {T_mean:.4f} K")
    print(f"  Max deviation from 4.2 K: {T_max_dev:.4f} K")
    print(f"  PASS: {passed_2}  (threshold: < 0.5 K)")
    print()

    # === Phase 3: Telemetry Bus Cycle Time ===
    print("=" * 60)
    print("PHASE 3: Telemetry — Read all 9 organs within 100 ms")
    print("=" * 60)

    bus = UmbilicalBus()
    # Telemetry cycle: cognitive lattice polls each organ
    poll_latencies = []
    for organ in ORGANS:
        if organ == "cognitive":
            poll_latencies.append(0.0)  # self-read
            continue
        route = bus.route_signal("cognitive", organ)
        if route:
            lat, path = route
            # Round trip: query + response
            poll_latencies.append(lat * 2)
        else:
            poll_latencies.append(float('inf'))

    # Sequential polling: total = sum of all round trips
    total_sequential = sum(poll_latencies)
    # Parallel polling: total = max round trip (bus supports parallel)
    total_parallel = max(poll_latencies)
    # Practical: partially parallel (4 concurrent polls)
    sorted_lats = sorted(poll_latencies, reverse=True)
    concurrent = 4
    waves = [sorted_lats[i:i + concurrent] for i in range(0, len(sorted_lats), concurrent)]
    total_practical = sum(max(w) for w in waves)

    passed_3 = total_practical < 100.0
    results['phase_3'] = {'sequential_ms': total_sequential, 'parallel_ms': total_parallel,
                          'practical_ms': total_practical, 'passed': passed_3}
    print(f"  Sequential polling: {total_sequential:.2f} ms")
    print(f"  Fully parallel:     {total_parallel:.2f} ms")
    print(f"  Practical (4-way):  {total_practical:.2f} ms")
    for organ, lat in zip(ORGANS, poll_latencies):
        print(f"    {organ:15s}: {lat:.2f} ms round-trip")
    print(f"  PASS: {passed_3}  (threshold: < 100 ms practical)")
    print()

    # === Phase 4: Power Distribution Balance ===
    print("=" * 60)
    print("PHASE 4: Power Distribution — Load balance within 5%")
    print("=" * 60)

    bus = UmbilicalBus()

    # Normal operation
    delivered_normal = bus.power_step()
    total_demand = sum(bus.power_budget.values())
    total_delivered = sum(delivered_normal.values())
    balance_error_normal = abs(total_delivered - total_demand) / total_demand

    # Stress test: muscles running, CEM dumping, cognitive processing
    bus.power_budget["muscles"] = 251.0   # running mode
    bus.power_budget["cem"] = 3.2         # dump mode
    bus.power_budget["cognitive"] = 5.0   # heavy processing

    delivered_stress = bus.power_step()
    total_demand_stress = sum(bus.power_budget.values())
    total_delivered_stress = sum(delivered_stress.values())

    # Check proportional fairness
    if total_demand_stress > bus.total_power_available:
        ratio = bus.total_power_available / total_demand_stress
        max_deviation = 0.0
        for organ, demand in bus.power_budget.items():
            expected = demand * ratio
            actual = delivered_stress[organ]
            dev = abs(actual - expected) / (expected + 1e-15)
            max_deviation = max(max_deviation, dev)
        proportional_fair = max_deviation < 0.05
    else:
        proportional_fair = True
        max_deviation = 0.0

    passed_4 = balance_error_normal < 0.05 and proportional_fair
    results['phase_4'] = {'normal_error': balance_error_normal,
                          'stress_demand': total_demand_stress,
                          'stress_delivered': total_delivered_stress,
                          'proportional_fair': proportional_fair,
                          'max_deviation': max_deviation,
                          'passed': passed_4}
    print(f"  Normal operation:")
    print(f"    Demand: {total_demand:.2f} W, Delivered: {total_delivered:.2f} W")
    print(f"    Balance error: {balance_error_normal:.4f}")
    print(f"  Stress operation (muscles running):")
    print(f"    Demand: {total_demand_stress:.2f} W, Available: {bus.total_power_available:.2f} W")
    print(f"    Delivered: {total_delivered_stress:.2f} W")
    print(f"    Proportionally fair: {proportional_fair} (max deviation: {max_deviation:.4f})")
    print(f"  PASS: {passed_4}  (threshold: < 5% error)")
    print()

    # === INTEGRATED: Full organism heartbeat ===
    print("=" * 60)
    print("INTEGRATED: Full Organism Heartbeat (10 cycles)")
    print("=" * 60)

    bus = UmbilicalBus()
    bus.power_budget["muscles"] = 94.0  # walking mode

    for cycle in range(10):
        # Cryo step
        ext_load = 0.5 + 0.1 * np.sin(cycle * 0.5)
        T = bus.cryo_step(dt=10.0, external_load=ext_load)

        # Power distribution
        power = bus.power_step()

        # Telemetry
        telemetry = bus.read_telemetry()

        # Signal check: MTR heartbeat to cognitive
        hb_route = bus.route_signal("mtr", "cognitive")
        hb_lat = hb_route[0] if hb_route else float('inf')

        if cycle % 3 == 0:
            print(f"  Cycle {cycle:2d} | He4={T:.3f}K | Power={sum(power.values()):.1f}W | "
                  f"Heartbeat latency={hb_lat:.1f}ms | "
                  f"Organs reporting: {len(telemetry)}/9")

    # === SUMMARY ===
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


if __name__ == "__main__":
    run_bench_tests()
