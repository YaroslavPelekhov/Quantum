"""Create compact diagnostic figures for the completed Phase 0."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "aquila_one_mask_phase0"


def main() -> None:
    reference = json.loads((OUTPUT / "reference_audit.json").read_text(encoding="utf-8"))
    with (OUTPUT / "reference_convergence.csv").open(encoding="utf-8") as handle:
        convergence = list(csv.DictReader(handle))
    with (OUTPUT / "robustness.csv").open(encoding="utf-8") as handle:
        robustness = list(csv.DictReader(handle))

    figure, axes = plt.subplots(1, 3, figsize=(13.2, 3.8), constrained_layout=True)
    substeps = np.array([2, 4, 8, 16, 32, 64])
    colors = {5: "#31688e", 10: "#d1495b"}
    for target in (5, 10):
        selected = reference["best_hardware_facing_candidates"][str(target)]
        row = next(
            item
            for item in convergence
            if item["model"] == "full_c6"
            and item["mode"] == "gradient_mask"
            and int(item["target_mask"]) == target
            and int(item["seed"]) == selected["seed"]
        )
        values = np.array([float(row[f"midpoint_substeps_{count}"]) for count in substeps])
        axes[0].plot(substeps, values, "o-", color=colors[target], label=f"target {target:04b}")
        axes[0].axhline(selected["adaptive_ode_reference_fidelity"], color=colors[target], linestyle=":")
    axes[0].axhline(0.95, color="black", linestyle="--", linewidth=1, label="frozen gate")
    axes[0].set_xscale("log", base=2)
    axes[0].set_xlabel("midpoint substeps / knot interval")
    axes[0].set_ylabel("state fidelity")
    axes[0].set_title("Mesh false positive")
    axes[0].set_ylim(0.35, 1.02)
    axes[0].legend(fontsize=8)

    target_labels = ["0101", "1010"]
    reference_values = [
        reference["best_hardware_facing_candidates"][str(target)]["adaptive_ode_reference_fidelity"]
        for target in (5, 10)
    ]
    axes[1].bar(target_labels, reference_values, color=[colors[5], colors[10]], width=0.62)
    axes[1].axhline(0.5, color="#777777", linestyle=":", label="global-only ceiling")
    axes[1].axhline(0.95, color="black", linestyle="--", label="frozen gate")
    axes[1].set_ylim(0.0, 1.02)
    axes[1].set_ylabel("adaptive-ODE fidelity")
    axes[1].set_title("Hardware-facing truth")
    axes[1].legend(fontsize=8)

    groups = [
        np.array([float(row["fidelity"]) for row in robustness if int(row["target_mask"]) == target])
        for target in (5, 10)
    ]
    box = axes[2].boxplot(groups, tick_labels=target_labels, patch_artist=True, showfliers=False)
    for patch, target in zip(box["boxes"], (5, 10)):
        patch.set_facecolor(colors[target])
        patch.set_alpha(0.75)
    axes[2].axhline(0.8, color="black", linestyle="--", linewidth=1, label="robustness gate")
    axes[2].set_ylim(0.0, 1.02)
    axes[2].set_ylabel("perturbed fidelity")
    axes[2].set_title("128-draw robustness")
    axes[2].legend(fontsize=8)

    figure.suptitle("Aquila one-static-mask Phase 0: structural promise, physical kill", fontsize=12)
    figure.savefig(OUTPUT / "phase0_diagnostics.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()

