"""Read-only smoke audit for the two archived ``ibm_boston`` QAOA jobs.

This module is intentionally narrow.  It loads one counts payload from the
working tree and one older payload directly from the local submodule's Git
object database.  The historical blob is streamed through ``git show`` and is
never materialized in the submodule.

The returned feasibility rate is the *raw reduced-graph* rate: a measured
bitstring is feasible exactly when it does not select both endpoints of any
edge in the archived reduced graph.  No unfolding, repair, mitigation, pair
selection, confidence interval, conformal calibration, or generalization
claim is performed here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Mapping, Sequence


SUBMODULE_RELATIVE_PATH = Path("baselines/qoblib-solutions")
EXPERIMENT_RELATIVE_PATH = Path(
    "experiments/quantum/ibm_qpu/07-independentset/es60fst02/"
    "20251127_qdc2025_qaoa_mis_reduction"
)
COUNTS_RELATIVE_PATH = EXPERIMENT_RELATIVE_PATH / (
    "outputs/samples/es60fst02_ibm_boston_p15_grid_20251127_samples.json.gz"
)
QPU_CASE_RELATIVE_PATH = EXPERIMENT_RELATIVE_PATH / (
    "outputs/qpu_cases/es60fst02_ibm_boston_p15_grid_20251127.json"
)
RESULT_RELATIVE_PATH = EXPERIMENT_RELATIVE_PATH / (
    "outputs/results/es60fst02_ibm_boston_p15_grid_20251127_result.json"
)

EXPECTED_INSTANCE = "es60fst02"
EXPECTED_BACKEND = "ibm_boston"
EXPECTED_DEPTH = 15
EXPECTED_ARMS = 20
EXPECTED_SHOTS_PER_ARM = 1_000
EXPECTED_TOTAL_SHOTS = 20_000


class LegacyArchiveValidationError(ValueError):
    """Raised when a local legacy artifact violates its frozen schema."""


@dataclass(frozen=True)
class LegacyBlockSpec:
    """Frozen provenance expected for one archived hardware job."""

    block_id: str
    job_id: str
    lambda_penalty: float
    source_kind: str
    revision: str | None


@dataclass(frozen=True)
class ArmRawFeasibility:
    """Raw reduced-graph feasibility for one parameter-schedule arm."""

    delta_index: int
    delta_beta: float
    delta_gamma: float
    total_shots: int
    unique_bitstrings: int
    raw_feasible_shots: int
    raw_feasible_fraction: float


@dataclass(frozen=True)
class LegacyJobBlock:
    """Validated summary of one archived IBM job."""

    block_id: str
    job_id: str
    instance: str
    backend_name: str
    lambda_penalty: float
    depth: int
    source_kind: str
    source_revision: str | None
    counts_locator: str
    counts_sha256: str
    job_created_at: str | None
    job_finished_at: str | None
    qpu_runtime_seconds: float
    reduced_node_count: int
    reduced_edge_count: int
    graph_sha256: str
    total_shots: int
    total_raw_feasible_shots: int
    arms: tuple[ArmRawFeasibility, ...]


@dataclass(frozen=True)
class LegacyAuditMetadata:
    """Scope restrictions that must travel with every legacy audit result."""

    audit_kind: str
    job_blocks: int
    independent_instances: int
    independent_backends: int
    arms_per_job: int
    pairwise_comparisons_per_job: int
    not_independent_for_conformal: bool
    missing_transpiled_circuit_lineage: bool
    missing_calibration_lineage: bool
    allows_claim_or_generalization: bool
    warning: str


@dataclass(frozen=True)
class LegacyIBMSmokeAudit:
    """Complete read-only audit result for the two known archive blocks."""

    metadata: LegacyAuditMetadata
    blocks: tuple[LegacyJobBlock, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation without raw bitstrings."""

        return asdict(self)


LEGACY_BLOCK_SPECS = (
    LegacyBlockSpec(
        block_id="ibm_boston_20260609_lambda1",
        job_id="d8k7s4r2d42s73c9smo0",
        lambda_penalty=1.0,
        source_kind="git_blob",
        revision="c8b29bd",
    ),
    LegacyBlockSpec(
        block_id="ibm_boston_20260611_lambda2",
        job_id="d8l8g8rqv2lc73865vhg",
        lambda_penalty=2.0,
        source_kind="working_tree",
        revision=None,
    ),
)


def default_repository_root() -> Path:
    """Return the project root inferred from this module's location."""

    return Path(__file__).resolve().parents[2]


def _fail(context: str, message: str) -> None:
    raise LegacyArchiveValidationError(f"{context}: {message}")


def _mapping(value: object, *, context: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        _fail(context, "expected a JSON object")
    return value


def _sequence(value: object, *, context: str) -> Sequence[object]:
    if not isinstance(value, list):
        _fail(context, "expected a JSON array")
    return value


def _required(mapping: Mapping[str, object], key: str, *, context: str) -> object:
    if key not in mapping:
        _fail(context, f"missing required key {key!r}")
    return mapping[key]


def _integer(value: object, *, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(context, "expected an integer")
    return value


def _number(value: object, *, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(context, "expected a finite number")
    result = float(value)
    if not math.isfinite(result):
        _fail(context, "expected a finite number")
    return result


def _expect_equal(actual: object, expected: object, *, context: str) -> None:
    if actual != expected:
        _fail(context, f"expected {expected!r}, got {actual!r}")


def _expect_float(actual: object, expected: float, *, context: str) -> float:
    value = _number(actual, context=context)
    if not math.isclose(value, expected, rel_tol=0.0, abs_tol=1e-12):
        _fail(context, f"expected {expected!r}, got {value!r}")
    return value


def _decode_json(raw: bytes, *, context: str) -> Mapping[str, object]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LegacyArchiveValidationError(f"{context}: invalid UTF-8 JSON") from error
    return _mapping(value, context=context)


def _read_git_blob(submodule_root: Path, revision: str, relative_path: Path) -> bytes:
    locator = f"{revision}:{relative_path.as_posix()}"
    try:
        process = subprocess.run(
            ["git", "-C", str(submodule_root), "show", locator],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise LegacyArchiveValidationError("git executable is unavailable") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        raise LegacyArchiveValidationError(
            f"cannot read local Git object {locator!r}: {detail}"
        ) from error
    return process.stdout


def _read_artifact(
    submodule_root: Path,
    spec: LegacyBlockSpec,
    relative_path: Path,
) -> tuple[bytes, str]:
    if spec.source_kind == "git_blob":
        if spec.revision is None:
            _fail(spec.block_id, "git_blob source requires a revision")
        raw = _read_git_blob(submodule_root, spec.revision, relative_path)
        locator = f"{submodule_root}@{spec.revision}:{relative_path.as_posix()}"
        return raw, locator
    if spec.source_kind == "working_tree":
        path = (submodule_root / relative_path).resolve()
        try:
            return path.read_bytes(), str(path)
        except OSError as error:
            raise LegacyArchiveValidationError(f"cannot read {path}") from error
    _fail(spec.block_id, f"unknown source kind {spec.source_kind!r}")


def _normalise_deltas(value: object, *, context: str) -> tuple[tuple[float, float], ...]:
    rows = _sequence(value, context=context)
    result: list[tuple[float, float]] = []
    for index, row in enumerate(rows):
        row_context = f"{context}[{index}]"
        if isinstance(row, dict):
            beta = _number(_required(row, "delta_beta", context=row_context), context=row_context)
            gamma = _number(_required(row, "delta_gamma", context=row_context), context=row_context)
        else:
            pair = _sequence(row, context=row_context)
            if len(pair) != 2:
                _fail(row_context, "expected a beta/gamma pair")
            beta = _number(pair[0], context=f"{row_context}.beta")
            gamma = _number(pair[1], context=f"{row_context}.gamma")
        result.append((beta, gamma))
    return tuple(result)


def _validate_graph(result: Mapping[str, object], *, context: str) -> tuple[tuple[int, ...], tuple[tuple[int, int], ...]]:
    graph_section = _mapping(_required(result, "graph", context=context), context=f"{context}.graph")
    reduced = _mapping(
        _required(graph_section, "reduced_graph", context=f"{context}.graph"),
        context=f"{context}.graph.reduced_graph",
    )
    node_values = _sequence(
        _required(reduced, "nodes", context=f"{context}.graph.reduced_graph"),
        context=f"{context}.graph.reduced_graph.nodes",
    )
    nodes = tuple(_integer(node, context=f"{context}.graph.nodes") for node in node_values)
    if len(nodes) != len(set(nodes)):
        _fail(context, "reduced graph contains duplicate nodes")
    _expect_equal(
        _integer(_required(reduced, "num_nodes", context=context), context=context),
        len(nodes),
        context=f"{context}.graph.num_nodes",
    )
    if len(nodes) != 55:
        _fail(context, f"expected 55 reduced nodes, got {len(nodes)}")

    node_set = set(nodes)
    edge_values = _sequence(
        _required(reduced, "edges", context=f"{context}.graph.reduced_graph"),
        context=f"{context}.graph.reduced_graph.edges",
    )
    edges: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for index, edge_value in enumerate(edge_values):
        pair = _sequence(edge_value, context=f"{context}.graph.edges[{index}]")
        if len(pair) != 2:
            _fail(context, f"edge {index} does not have two endpoints")
        u = _integer(pair[0], context=f"{context}.graph.edges[{index}][0]")
        v = _integer(pair[1], context=f"{context}.graph.edges[{index}][1]")
        if u == v or u not in node_set or v not in node_set:
            _fail(context, f"invalid reduced edge {(u, v)!r}")
        canonical = (min(u, v), max(u, v))
        if canonical in seen:
            _fail(context, f"duplicate reduced edge {canonical!r}")
        seen.add(canonical)
        edges.append(canonical)
    _expect_equal(
        _integer(_required(reduced, "num_edges", context=context), context=context),
        len(edges),
        context=f"{context}.graph.num_edges",
    )
    if len(edges) != 91:
        _fail(context, f"expected 91 reduced edges, got {len(edges)}")
    return tuple(sorted(nodes)), tuple(sorted(edges))


def raw_reduced_graph_feasible_shots(
    counts: Mapping[str, int],
    reduced_nodes: Sequence[int],
    reduced_edges: Sequence[Sequence[int]],
) -> int:
    """Count shots with no selected reduced-graph edge.

    Archive bit position ``i`` corresponds to the ``i``-th sorted reduced
    node.  This is specific to the notebook's reversed classical-register
    measurement contract and must not be assumed for unrelated jobs.
    """

    nodes = tuple(sorted(reduced_nodes))
    if not nodes or len(nodes) != len(set(nodes)):
        raise ValueError("reduced_nodes must be non-empty and unique")
    position = {node: index for index, node in enumerate(nodes)}
    edge_positions: list[tuple[int, int]] = []
    for edge in reduced_edges:
        if len(edge) != 2:
            raise ValueError("each reduced edge must have two endpoints")
        u, v = edge
        if u == v or u not in position or v not in position:
            raise ValueError(f"invalid reduced edge {(u, v)!r}")
        edge_positions.append((position[u], position[v]))

    feasible_shots = 0
    for bitstring, raw_count in counts.items():
        if not isinstance(bitstring, str) or len(bitstring) != len(nodes):
            raise ValueError("each bitstring must match the reduced-node count")
        if set(bitstring) - {"0", "1"}:
            raise ValueError("bitstrings may contain only '0' and '1'")
        if isinstance(raw_count, bool) or not isinstance(raw_count, int) or raw_count <= 0:
            raise ValueError("shot counts must be positive integers")
        if all(not (bitstring[u] == "1" and bitstring[v] == "1") for u, v in edge_positions):
            feasible_shots += raw_count
    return feasible_shots


def _validate_companions(
    spec: LegacyBlockSpec,
    counts: Mapping[str, object],
    qpu_case: Mapping[str, object],
    result: Mapping[str, object],
) -> tuple[tuple[float, float], ...]:
    context = spec.block_id
    _expect_equal(_required(counts, "schema_version", context=context), 1, context="counts.schema_version")
    _expect_equal(_required(counts, "job_id", context=context), spec.job_id, context="counts.job_id")
    _expect_equal(_required(counts, "backend_name", context=context), EXPECTED_BACKEND, context="counts.backend_name")
    _expect_equal(_required(counts, "shots", context=context), EXPECTED_SHOTS_PER_ARM, context="counts.shots")
    _expect_equal(_required(counts, "ps", context=context), [EXPECTED_DEPTH], context="counts.ps")
    _expect_equal(_required(counts, "selected_p", context=context), EXPECTED_DEPTH, context="counts.selected_p")
    _expect_equal(
        _required(counts, "total_sample_count", context=context),
        EXPECTED_TOTAL_SHOTS,
        context="counts.total_sample_count",
    )
    deltas = _normalise_deltas(_required(counts, "deltas", context=context), context="counts.deltas")
    _expect_equal(len(deltas), EXPECTED_ARMS, context="counts.delta_count")

    _expect_equal(_required(qpu_case, "schema_version", context=context), 1, context="qpu_case.schema_version")
    _expect_equal(_required(qpu_case, "instance", context=context), EXPECTED_INSTANCE, context="qpu_case.instance")
    execution = _mapping(_required(qpu_case, "execution", context=context), context="qpu_case.execution")
    _expect_equal(_required(execution, "backend_name", context=context), EXPECTED_BACKEND, context="qpu_case.backend")
    _expect_equal(_required(execution, "shots", context=context), EXPECTED_SHOTS_PER_ARM, context="qpu_case.shots")
    job = _mapping(_required(qpu_case, "job", context=context), context="qpu_case.job")
    _expect_equal(_required(job, "job_id", context=context), spec.job_id, context="qpu_case.job_id")
    qaoa = _mapping(_required(qpu_case, "qaoa", context=context), context="qpu_case.qaoa")
    _expect_equal(_required(qaoa, "ps", context=context), [EXPECTED_DEPTH], context="qpu_case.ps")
    _expect_equal(_required(qaoa, "selected_p", context=context), EXPECTED_DEPTH, context="qpu_case.selected_p")
    _expect_float(_required(qaoa, "lambda_penalty", context=context), spec.lambda_penalty, context="qpu_case.lambda")
    qpu_deltas = _normalise_deltas(_required(qaoa, "deltas", context=context), context="qpu_case.deltas")
    _expect_equal(qpu_deltas, deltas, context="qpu_case/counts deltas")

    metadata = _mapping(_required(result, "metadata", context=context), context="result.metadata")
    _expect_equal(_required(metadata, "instance", context=context), EXPECTED_INSTANCE, context="result.instance")
    _expect_equal(_required(metadata, "backend", context=context), EXPECTED_BACKEND, context="result.backend")
    parameters = _mapping(_required(result, "parameters", context=context), context="result.parameters")
    _expect_equal(_required(parameters, "depth", context=context), EXPECTED_DEPTH, context="result.depth")
    _expect_equal(_required(parameters, "shots", context=context), EXPECTED_SHOTS_PER_ARM, context="result.shots")
    _expect_equal(_required(parameters, "circuit_count", context=context), EXPECTED_ARMS, context="result.circuit_count")
    _expect_float(_required(parameters, "lambda_penalty", context=context), spec.lambda_penalty, context="result.lambda")
    result_deltas = _normalise_deltas(_required(parameters, "deltas", context=context), context="result.deltas")
    _expect_equal(result_deltas, deltas, context="result/counts deltas")
    result_execution = _mapping(_required(result, "execution", context=context), context="result.execution")
    _expect_equal(_required(result_execution, "backend_name", context=context), EXPECTED_BACKEND, context="result.execution.backend")
    result_job = _mapping(_required(result_execution, "job", context=context), context="result.execution.job")
    _expect_equal(_required(result_job, "job_id", context=context), spec.job_id, context="result.execution.job_id")
    return deltas


def _load_block(submodule_root: Path, spec: LegacyBlockSpec) -> LegacyJobBlock:
    counts_gzip, counts_locator = _read_artifact(submodule_root, spec, COUNTS_RELATIVE_PATH)
    qpu_case_raw, _ = _read_artifact(submodule_root, spec, QPU_CASE_RELATIVE_PATH)
    result_raw, _ = _read_artifact(submodule_root, spec, RESULT_RELATIVE_PATH)
    try:
        counts_raw = gzip.decompress(counts_gzip)
    except (OSError, EOFError) as error:
        raise LegacyArchiveValidationError(f"{spec.block_id}: invalid gzip counts payload") from error
    counts = _decode_json(counts_raw, context=f"{spec.block_id}.counts")
    qpu_case = _decode_json(qpu_case_raw, context=f"{spec.block_id}.qpu_case")
    result = _decode_json(result_raw, context=f"{spec.block_id}.result")
    deltas = _validate_companions(spec, counts, qpu_case, result)
    nodes, edges = _validate_graph(result, context=f"{spec.block_id}.result")

    entries = _sequence(_required(counts, "entries", context=spec.block_id), context="counts.entries")
    _expect_equal(len(entries), EXPECTED_ARMS, context="counts.entry_count")
    arms: list[ArmRawFeasibility] = []
    seen_indices: set[int] = set()
    total_shots = 0
    for position, raw_entry in enumerate(entries):
        entry = _mapping(raw_entry, context=f"counts.entries[{position}]")
        delta_index = _integer(
            _required(entry, "delta_index", context=spec.block_id),
            context=f"counts.entries[{position}].delta_index",
        )
        if delta_index in seen_indices or not 0 <= delta_index < EXPECTED_ARMS:
            _fail(spec.block_id, f"invalid or duplicate delta_index {delta_index}")
        seen_indices.add(delta_index)
        beta = _number(_required(entry, "delta_beta", context=spec.block_id), context="entry.delta_beta")
        gamma = _number(_required(entry, "delta_gamma", context=spec.block_id), context="entry.delta_gamma")
        expected_beta, expected_gamma = deltas[delta_index]
        if not (
            math.isclose(beta, expected_beta, rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(gamma, expected_gamma, rel_tol=0.0, abs_tol=1e-12)
        ):
            _fail(spec.block_id, f"entry {delta_index} disagrees with the frozen delta grid")
        samples_by_p = _mapping(
            _required(entry, "samples_by_p", context=spec.block_id),
            context=f"counts.entries[{position}].samples_by_p",
        )
        _expect_equal(set(samples_by_p), {str(EXPECTED_DEPTH)}, context="entry.samples_by_p keys")
        raw_counts = _mapping(
            _required(samples_by_p, str(EXPECTED_DEPTH), context=spec.block_id),
            context=f"counts.entries[{position}].samples_by_p[{EXPECTED_DEPTH}]",
        )
        arm_counts: dict[str, int] = {}
        for bitstring, raw_count in raw_counts.items():
            count = _integer(raw_count, context=f"entry {delta_index} count")
            if count <= 0:
                _fail(spec.block_id, "shot counts must be positive")
            arm_counts[bitstring] = count
        arm_shots = sum(arm_counts.values())
        _expect_equal(arm_shots, EXPECTED_SHOTS_PER_ARM, context=f"entry {delta_index} shots")
        feasible_shots = raw_reduced_graph_feasible_shots(arm_counts, nodes, edges)
        total_shots += arm_shots
        arms.append(
            ArmRawFeasibility(
                delta_index=delta_index,
                delta_beta=beta,
                delta_gamma=gamma,
                total_shots=arm_shots,
                unique_bitstrings=len(arm_counts),
                raw_feasible_shots=feasible_shots,
                raw_feasible_fraction=feasible_shots / arm_shots,
            )
        )
    _expect_equal(seen_indices, set(range(EXPECTED_ARMS)), context="counts.delta_indices")
    _expect_equal(total_shots, EXPECTED_TOTAL_SHOTS, context="counts summed shots")
    arms.sort(key=lambda arm: arm.delta_index)

    job = _mapping(_required(qpu_case, "job", context=spec.block_id), context="qpu_case.job")
    dates_value = job.get("backend_dates")
    dates = dates_value if isinstance(dates_value, dict) else {}
    created_at = dates.get("metrics.timestamps.created")
    finished_at = dates.get("metrics.timestamps.finished")
    qpu_runtime_seconds = _number(
        _required(job, "qpu_runtime_seconds", context=spec.block_id),
        context="qpu_case.qpu_runtime_seconds",
    )
    canonical_graph = json.dumps(
        {"nodes": nodes, "edges": edges}, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return LegacyJobBlock(
        block_id=spec.block_id,
        job_id=spec.job_id,
        instance=EXPECTED_INSTANCE,
        backend_name=EXPECTED_BACKEND,
        lambda_penalty=spec.lambda_penalty,
        depth=EXPECTED_DEPTH,
        source_kind=spec.source_kind,
        source_revision=spec.revision,
        counts_locator=counts_locator,
        counts_sha256=hashlib.sha256(counts_gzip).hexdigest(),
        job_created_at=created_at if isinstance(created_at, str) else None,
        job_finished_at=finished_at if isinstance(finished_at, str) else None,
        qpu_runtime_seconds=qpu_runtime_seconds,
        reduced_node_count=len(nodes),
        reduced_edge_count=len(edges),
        graph_sha256=hashlib.sha256(canonical_graph).hexdigest(),
        total_shots=total_shots,
        total_raw_feasible_shots=sum(arm.raw_feasible_shots for arm in arms),
        arms=tuple(arms),
    )


def load_legacy_ibm_smoke_audit(
    repository_root: str | Path | None = None,
) -> LegacyIBMSmokeAudit:
    """Load and validate the two local archive blocks without writing files.

    The result is descriptive evidence only.  The 20 arms and 190 within-job
    pairings share a job, graph instance, and hardware window; they are not
    independent calibration examples for conformal inference.
    """

    root = default_repository_root() if repository_root is None else Path(repository_root).resolve()
    submodule_root = (root / SUBMODULE_RELATIVE_PATH).resolve()
    if not submodule_root.is_dir():
        raise LegacyArchiveValidationError(f"submodule directory is missing: {submodule_root}")
    blocks = tuple(_load_block(submodule_root, spec) for spec in LEGACY_BLOCK_SPECS)
    if len({block.job_id for block in blocks}) != 2:
        _fail("archive", "expected two distinct hardware jobs")
    if len({block.instance for block in blocks}) != 1:
        _fail("archive", "expected one shared problem instance")
    if len({block.backend_name for block in blocks}) != 1:
        _fail("archive", "expected one shared backend")
    if len({block.graph_sha256 for block in blocks}) != 1:
        _fail("archive", "the two blocks must share the same reduced graph")

    metadata = LegacyAuditMetadata(
        audit_kind="legacy_smoke_audit_only",
        job_blocks=2,
        independent_instances=1,
        independent_backends=1,
        arms_per_job=EXPECTED_ARMS,
        pairwise_comparisons_per_job=EXPECTED_ARMS * (EXPECTED_ARMS - 1) // 2,
        not_independent_for_conformal=True,
        missing_transpiled_circuit_lineage=True,
        missing_calibration_lineage=True,
        allows_claim_or_generalization=False,
        warning=(
            "Two jobs on one instance/backend, with different lambda penalties; "
            "arms and pairwise contrasts are nested and must not be treated as "
            "independent conformal or generalization examples."
        ),
    )
    return LegacyIBMSmokeAudit(metadata=metadata, blocks=blocks)


def main() -> None:
    """Print the descriptive audit as JSON; perform no filesystem writes."""

    audit = load_legacy_ibm_smoke_audit()
    print(json.dumps(audit.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
