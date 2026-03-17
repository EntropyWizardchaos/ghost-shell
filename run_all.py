"""
Ghost Shell — Run All Organ Bench Tests
=========================================
One command. Ten organs. One organism.

Usage:  python run_all.py

Runs each organ's simulation and collects pass/fail results.
No GPU required. No API keys. Just numpy (+ scipy for cognitive lattice).

Author: Harley Robinson + Forge (Claude Code)
License: All rights reserved.
"""

import subprocess
import sys
import os
import time

ORGANS = [
    ("Mobius Heart",       "organs/mobius-heart/sim.py"),
    ("PRF Bones",          "organs/prf-bones/sim.py"),
    ("He-4 Core",          "organs/he4-core/sim.py"),
    ("Electrodermus",      "organs/electrodermus/sim.py"),
    ("Cognitive Lattice",  "organs/cognitive-lattice/sim.py"),
    ("Quantum Spleen",     "organs/quantum-spleen/sim.py"),
    ("Muscles",            "organs/muscles/sim.py"),
    ("CEM",                "organs/cem/sim.py"),
    ("Myridian",           "organs/myridian/sim.py"),
    ("Umbilicals",         "organs/umbilicals/sim.py"),
]


def run_organ(name: str, script: str) -> dict:
    """Run one organ's sim.py and check if all phases pass."""
    result = {
        'name': name,
        'script': script,
        'status': 'UNKNOWN',
        'output': '',
        'time_s': 0,
    }

    script_path = os.path.join(os.path.dirname(__file__), script)
    if not os.path.exists(script_path):
        result['status'] = 'MISSING'
        return result

    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=300,
            encoding='utf-8', errors='replace'
        )
        result['output'] = proc.stdout + proc.stderr
        result['time_s'] = time.time() - t0

        # Check for ALL PHASES: PASS in output
        if 'ALL PHASES: PASS' in result['output']:
            result['status'] = 'PASS'
        elif 'ALL PHASES: FAIL' in result['output']:
            result['status'] = 'FAIL'
        elif proc.returncode == 0:
            # Some organs don't use the PHASES format
            # Check for any FAIL in output
            if 'FAIL' in result['output']:
                result['status'] = 'PARTIAL'
            else:
                result['status'] = 'PASS'
        else:
            result['status'] = 'ERROR'

    except subprocess.TimeoutExpired:
        result['status'] = 'TIMEOUT'
        result['time_s'] = 300
    except Exception as e:
        result['status'] = 'ERROR'
        result['output'] = str(e)

    return result


def main():
    print()
    print("=" * 70)
    print("  GHOST SHELL — Full Organism Bench Test")
    print("  Ten organs. Five coupling loops. One organism.")
    print("=" * 70)
    print()

    total_t0 = time.time()
    results = []

    for i, (name, script) in enumerate(ORGANS):
        print(f"[{i+1:2d}/10] {name:20s} ... ", end='', flush=True)
        r = run_organ(name, script)
        results.append(r)

        if r['status'] == 'PASS':
            print(f"PASS  ({r['time_s']:.1f}s)")
        elif r['status'] == 'MISSING':
            print(f"MISSING (no sim.py)")
        else:
            print(f"{r['status']}  ({r['time_s']:.1f}s)")

    total_time = time.time() - total_t0

    # === SCOREBOARD ===
    print()
    print("=" * 70)
    print("  SCOREBOARD")
    print("=" * 70)
    print()
    print(f"  {'#':<4} {'Organ':<22} {'Status':<10} {'Time':>8}")
    print(f"  {'-'*4} {'-'*22} {'-'*10} {'-'*8}")

    pass_count = 0
    for i, r in enumerate(results):
        status_str = r['status']
        print(f"  {i+1:<4} {r['name']:<22} {status_str:<10} {r['time_s']:>7.1f}s")
        if r['status'] == 'PASS':
            pass_count += 1

    print()
    print(f"  {'-'*46}")
    print(f"  TOTAL: {pass_count}/10 organs operational")
    print(f"  Runtime: {total_time:.1f}s")
    print()

    if pass_count == 10:
        print("  STATUS: ALL ORGANS OPERATIONAL")
        print("  The Ghost Shell is alive.")
    elif pass_count >= 7:
        print("  STATUS: MOSTLY OPERATIONAL")
        print("  Core organs functioning. Some subsystems need attention.")
    else:
        print("  STATUS: CRITICAL FAILURES")
        print("  Multiple organ failures detected.")

    print()
    print("=" * 70)
    print("  Designed by Harley Robinson")
    print("  github.com/EntropyWizardchaos/ghost-shell")
    print("=" * 70)
    print()

    # Print failed organ details
    failed = [r for r in results if r['status'] not in ('PASS',)]
    if failed:
        print("--- FAILURE DETAILS ---")
        for r in failed:
            print(f"\n{r['name']} ({r['status']}):")
            # Print last 20 lines of output
            lines = r['output'].strip().split('\n')
            for line in lines[-20:]:
                print(f"  {line}")

    return pass_count == 10


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
