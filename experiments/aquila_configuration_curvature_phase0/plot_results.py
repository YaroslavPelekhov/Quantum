"""Plot the branch-free mechanism, controls, robustness, and scaling audits."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "results" / "aquila_configuration_curvature_phase0"


def read_rows(name: str) -> list[dict]:
    with (OUTPUT / name).open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    controls = read_rows("exact_controls.csv")
    mixed = read_rows("mixed_term_grid.csv")
    robustness = read_rows("robustness.csv")
    distance = read_rows("distance_scaling.csv")
    posthoc = read_rows("posthoc_asymptotic_distance.csv")

    figure, axes = plt.subplots(2, 2, figsize=(11.5, 7.5), constrained_layout=True)
    labels = ["forward", "reverse", "palindrome", "V=0", "equal mask", "LD off"]
    values = [float(row["chi"]) for row in controls]
    colors = ["#31688e", "#d1495b"] + ["#9e9e9e"] * 4
    axes[0, 0].bar(labels, values, color=colors)
    axes[0, 0].axhline(0.0, color="black", linewidth=0.8)
    axes[0, 0].axhline(0.15, color="black", linestyle="--", linewidth=1, label="frozen magnitude gate")
    axes[0, 0].axhline(-0.15, color="black", linestyle="--", linewidth=1)
    axes[0, 0].tick_params(axis="x", rotation=25)
    axes[0, 0].set_ylabel("branch-free counts witness chi")
    axes[0, 0].set_title("Exact causal controls")
    axes[0, 0].legend(fontsize=8)

    x = np.asarray([float(row["interaction_times_contrast"]) for row in mixed])
    y = np.asarray([float(row["chi"]) for row in mixed])
    beta = float(np.dot(x, y) / np.dot(x, x))
    axes[0, 1].scatter(x, y, s=26, alpha=0.8, color="#2a9d8f")
    grid = np.linspace(0.0, x.max(), 100)
    axes[0, 1].plot(grid, beta * grid, color="black", linestyle="--", label=f"chi={beta:.5f} V dh")
    axes[0, 1].set_xlabel("interaction V x mask contrast")
    axes[0, 1].set_ylabel("chi")
    axes[0, 1].set_title("Held-out mixed-term collapse")
    axes[0, 1].legend(fontsize=8)

    chis = np.asarray([float(row["chi"]) for row in robustness])
    axes[1, 0].hist(chis, bins=24, color="#457b9d", alpha=0.85)
    axes[1, 0].axvline(np.quantile(chis, 0.05), color="black", linestyle="--", label=f"p05={np.quantile(chis, 0.05):.3f}")
    axes[1, 0].axvline(0.1, color="#d1495b", linestyle=":", label="frozen gate")
    axes[1, 0].set_xlabel("chi")
    axes[1, 0].set_ylabel("perturbation draws")
    axes[1, 0].set_title("256-draw robustness")
    axes[1, 0].legend(fontsize=8)

    frozen_r = np.asarray([float(row["distance_um"]) for row in distance])
    frozen_phi = np.abs([float(row["numerical_flux_rad"]) for row in distance])
    post_r = np.asarray([float(row["distance_um"]) for row in posthoc])
    post_phi = np.abs([float(row["analytic_flux_rad"]) for row in posthoc])
    frozen_slope = np.polyfit(np.log(frozen_r), np.log(frozen_phi), 1)[0]
    post_slope = np.polyfit(np.log(post_r), np.log(post_phi), 1)[0]
    axes[1, 1].loglog(frozen_r, frozen_phi, "o-", label=f"frozen slope {frozen_slope:.3f}")
    axes[1, 1].loglog(post_r, post_phi, "s--", label=f"post-hoc asymptote {post_slope:.3f}")
    axes[1, 1].set_xlabel("distance (um)")
    axes[1, 1].set_ylabel("absolute weak-response flux")
    axes[1, 1].set_title("Finite-range gate vs asymptote")
    axes[1, 1].legend(fontsize=8)

    figure.suptitle("Aquila one-mask interaction response: mechanism survives, A-star novelty does not", fontsize=12)
    figure.savefig(OUTPUT / "phase0_diagnostics.png", dpi=180)
    plt.close(figure)

    compiler = read_rows("compiler_rank_audit.csv")
    profile = read_rows("compiler_polynomial_rank_profile.csv")
    compiler_figure, compiler_axes = plt.subplots(1, 2, figsize=(10.8, 4.2), constrained_layout=True)
    particle_counts = np.asarray([int(row["n"]) for row in compiler])
    full_ranks = np.asarray([int(row["coboundary_rank_mod_p"]) for row in compiler])
    tangent_ranks = np.asarray([int(row["first_interaction_order_rank"]) for row in compiler])
    compiler_axes[0].semilogy(
        particle_counts, full_ranks, "o-", linewidth=2, label="generic weak-drive flux rank"
    )
    compiler_axes[0].semilogy(
        particle_counts, tangent_ranks, "s--", linewidth=2, label="first-order interaction rank"
    )
    compiler_axes[0].set_xticks(particle_counts)
    compiler_axes[0].set_xlabel("atoms n")
    compiler_axes[0].set_ylabel("exact finite-field rank")
    compiler_axes[0].set_title("Low-rank tangent, full generic curvature")
    compiler_axes[0].legend(fontsize=8)

    for n in particle_counts:
        selected = [row for row in profile if int(row["n"]) == n]
        degree = np.asarray([int(row["polynomial_degree"]) for row in selected])
        rank = np.asarray([int(row["finite_field_rank"]) for row in selected])
        maximum = int(
            next(row["coboundary_rank_mod_p"] for row in compiler if int(row["n"]) == n)
        )
        compiler_axes[1].plot(degree / (maximum + 1), rank / maximum, label=f"n={n}")
    compiler_axes[1].axhline(1.0, color="black", linestyle="--", linewidth=0.8)
    compiler_axes[1].set_xlabel("polynomial degree / first full-rank degree")
    compiler_axes[1].set_ylabel("attained rank / full rank")
    compiler_axes[1].set_title("Exact polynomial spectral witnesses")
    compiler_axes[1].legend(fontsize=8)
    compiler_figure.suptitle(
        "One static mask does not impose a generic low-rank curvature tensor", fontsize=12
    )
    compiler_figure.savefig(OUTPUT / "compiler_rank_diagnostics.png", dpi=180)
    plt.close(compiler_figure)


if __name__ == "__main__":
    main()
