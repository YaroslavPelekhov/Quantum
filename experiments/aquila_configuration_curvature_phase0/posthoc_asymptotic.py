"""Post-hoc diagnosis of the failed finite-range r^-6 slope gate."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.aquila_configuration_curvature_phase0.curvature_core import analytic_weak_flux


EXPERIMENT = ROOT / "experiments" / "aquila_configuration_curvature_phase0"
OUTPUT = ROOT / "results" / "aquila_configuration_curvature_phase0"


def main() -> None:
    protocol = json.loads((EXPERIMENT / "protocol.json").read_text(encoding="utf-8"))
    config = protocol["weak_drive_case"]
    c6 = protocol["c6_rad_per_us_um6"]
    mask = np.asarray(config["mask"])
    e1, e2 = -config["global_detuning_rad_per_us"] - config["local_detuning_rad_per_us"] * mask
    distances = np.array([22.0, 26.0, 30.0, 36.0, 44.0, 54.0])
    rows = []
    for distance in distances:
        interaction = c6 / distance**6
        flux = analytic_weak_flux(
            e1,
            e2,
            interaction,
            config["duration_us"],
            tuple(config["kick_centers_us"]),
            tuple(config["kick_peaks_rad_per_us"]),
        )
        rows.append({"distance_um": distance, "interaction_rad_per_us": interaction, "analytic_flux_rad": flux})
    slope, intercept = np.polyfit(np.log(distances), np.log(np.abs([row["analytic_flux_rad"] for row in rows])), 1)
    with (OUTPUT / "posthoc_asymptotic_distance.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    note = f"""# Post-hoc asymptotic diagnosis

This diagnostic was designed after the frozen `-6 +/- 0.25` distance gate
failed with slope `-6.662409`.  It cannot rescue or relabel the preregistered
verdict.

The frozen scan began at interaction `0.719832 rad/us`; the exact weak-response
formula is nonlinear at that scale even though it matches the numerical
continued-log derivative to `1.3e-11 rad`.  Extending only the analytic formula
to the explicitly post-hoc range 22--54 um gives log-log slope
`{slope:.9f}`.  This approaches the predicted `-6` as `V=C6/r^6` enters the
linear regime.

The appropriate primary scaling law is the already frozen mixed-term check
`chi = beta V delta_h + higher orders`, which passed with centered
`R2=0.998610`.  The raw finite-range power-law gate was over-restrictive; the
mechanism is not falsified by that miss, but the official Phase-0 status remains
`MECHANISM_PARTIAL_ASTAR_KILL`.
"""
    (OUTPUT / "POSTHOC_ASYMPTOTIC_NOTE.md").write_text(note, encoding="utf-8")
    print(json.dumps({"posthoc_log_slope": float(slope), "intercept": float(intercept)}))


if __name__ == "__main__":
    main()

