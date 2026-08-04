"""
Evaluator: synthetic TSP, exact-baseline speed scoring.

- Генерирует K синтетических инстансов размера N∈[GEN_MIN_N, GEN_MAX_N].
- Бейзлайн: точная длина тура через Held–Karp DP (O(n^2*2^n)).
- Вызывает solve_tsp(coords). Если длина совпала с оптимумом (с допуском EPS),
  score_i = t_exact / t_candidate, иначе 0.
- Итоговый combined_score = среднее score_i.

Пер-инстанс таймаут защищает от зависаний кандидатов.

ENV (необязательно):
  GEN_K=24, GEN_MIN_N=7, GEN_MAX_N=9, GEN_SCALE=100.0, RNG_SEED=42
  EPS=1e-8
  PER_INSTANCE_TIMEOUT=10   (секунд)
  SAVE_JSONL=/path/to/per_file_metrics.jsonl
  SAVE_DIR=/path/to/dir
"""

from __future__ import annotations
from typing import Dict, Any, List, Tuple, Sequence
import math, os, time, json, random, multiprocessing as mp
import numpy as np
from openevolve.evaluation_result import EvaluationResult
import importlib.util

Coord = Tuple[float, float]

# ---------------- env ----------------
GEN_K       = int(os.getenv("GEN_K", "24"))
GEN_MIN_N   = int(os.getenv("GEN_MIN_N", "7"))
GEN_MAX_N   = int(os.getenv("GEN_MAX_N", "9"))
GEN_SCALE   = float(os.getenv("GEN_SCALE", "100.0"))
RNG_SEED    = int(os.getenv("RNG_SEED", "42"))
EPS         = float(os.getenv("EPS", "1e-8"))
PER_INSTANCE_TIMEOUT = float(os.getenv("PER_INSTANCE_TIMEOUT", "10"))

SAVE_JSONL  = os.getenv("SAVE_JSONL", "").strip()
SAVE_DIR    = os.getenv("SAVE_DIR", "").strip()

# -------------- utils ----------------
def _dist(a: Coord, b: Coord) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])

def _tour_len(coords: Sequence[Coord], tour: Sequence[int]) -> float:
    s = 0.0
    n = len(tour)
    for i in range(n):
        a = tour[i]; b = tour[(i+1) % n]
        s += _dist(coords[a], coords[b])
    return s

def _validate_tour(tour, n: int):
    if not isinstance(tour, list): return False, "tour_not_list"
    if len(tour) != n: return False, "tour_wrong_length"
    if any((not isinstance(v, int)) for v in tour): return False, "tour_non_int"
    if any((v < 0 or v >= n) for v in tour): return False, "tour_oob"
    if len(set(tour)) != n: return False, "tour_dups"
    return True, ""

# -------- exact Held–Karp (length only) --------
def _hk_exact_length(coords: Sequence[Coord]) -> float:
    n = len(coords)
    if n <= 1: return 0.0
    # precompute
    D = [[0.0]*n for _ in range(n)]
    for i in range(n):
        xi, yi = coords[i]
        for j in range(i+1, n):
            d = math.hypot(xi - coords[j][0], yi - coords[j][1])
            D[i][j] = D[j][i] = d

    FULL = (1 << n) - 1
    INF = float("inf")
    dp = [[INF]*n for _ in range(1 << n)]
    dp[1][0] = 0.0  # start at 0

    for mask in range(1 << n):
        if (mask & 1) == 0:  # must include 0
            continue
        for j in range(n):
            if (mask >> j) & 1 == 0: continue
            cj = dp[mask][j]
            if cj == INF: continue
            rem = (~mask) & FULL
            m = rem
            while m:
                k = (m & -m).bit_length() - 1
                m ^= (1 << k)
                nm = mask | (1 << k)
                val = cj + D[j][k]
                if val < dp[nm][k]:
                    dp[nm][k] = val

    best = INF
    for j in range(1, n):
        best = min(best, dp[FULL][j] + D[j][0])
    return best

# ---------- instance generation ----------
def _gen_instances(K: int, n_min: int, n_max: int, scale: float, seed: int):
    rng = np.random.default_rng(seed)
    Ns = rng.integers(low=n_min, high=n_max+1, size=K).tolist()
    items = []
    for i, n in enumerate(Ns):
        pts = (rng.random((n, 2)) * scale).tolist()
        coords = [(float(x), float(y)) for x, y in pts]
        items.append({"name": f"synthetic_{i}_n{n}", "coords": coords})
    return items

# -------- safe import + timeout wrapper --------
def _safe_import(program_path: str):
    spec = importlib.util.spec_from_file_location("candidate", program_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

def _call_with_timeout(func, args=(), kwargs=None, timeout=10.0):
    kwargs = kwargs or {}
    q = mp.Queue()

    def _runner(q):
        try:
            r = func(*args, **kwargs)
            q.put(("ok", r))
        except Exception as e:
            q.put(("err", f"{type(e).__name__}: {e}"))

    p = mp.Process(target=_runner, args=(q,))
    p.daemon = True
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate(); p.join()
        return ("timeout", None)
    if q.empty():
        return ("err", "no_result")
    return q.get()

# ---------------- saves ----------------
def _ensure_parent(path: str):
    if not path: return
    d = os.path.dirname(path)
    if d: os.makedirs(d, exist_ok=True)

def _save_jsonl(rows: List[Dict[str, Any]]):
    if not SAVE_JSONL: return
    _ensure_parent(SAVE_JSONL)
    with open(SAVE_JSONL, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def _save_dir(rows: List[Dict[str, Any]]):
    if not SAVE_DIR: return
    os.makedirs(SAVE_DIR, exist_ok=True)
    for r in rows:
        base = str(r.get("file", "instance"))
        safe = "".join(ch if ch.isalnum() or ch in ("-","_",".") else "_" for ch in base)
        with open(os.path.join(SAVE_DIR, safe + ".json"), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)

# --------------- main evaluate ---------------
def evaluate(program_path: str) -> EvaluationResult:
    per_file: List[Dict[str, Any]] = []

    try:
        mod = _safe_import(program_path)
    except Exception as e:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "error_code": "import_error", "error_message": str(e)},
            artifacts={"per_file_metrics": []}
        )
    if not hasattr(mod, "solve_tsp"):
        return EvaluationResult(
            metrics={"combined_score": 0.0, "error_code": "missing_solve_tsp", "error_message": "solve_tsp not found"},
            artifacts={"per_file_metrics": []}
        )

    items = _gen_instances(GEN_K, GEN_MIN_N, GEN_MAX_N, GEN_SCALE, RNG_SEED)

    scores: List[float] = []
    match_flags: List[int] = []
    t_eval0 = time.time()

    for it in items:
        name = it["name"]; coords = it["coords"]; n = len(coords)

        # exact baseline
        t0 = time.time()
        try:
            exact_len = _hk_exact_length(coords)
            t_exact = time.time() - t0
        except Exception as e:
            per_file.append({"file": name, "N": n, "status": "error", "error_code": "exact_failed",
                             "error_message": f"{type(e).__name__}: {e}"})
            continue

        # candidate call with timeout
        tc0 = time.time()
        status, payload = _call_with_timeout(mod.solve_tsp, args=(coords,),
                                             timeout=PER_INSTANCE_TIMEOUT)
        t_cand = time.time() - tc0

        if status == "timeout":
            per_file.append({"file": name, "N": n, "status": "timeout",
                             "Exact Length": float(exact_len),
                             "Baseline Exact Time (s)": float(t_exact),
                             "Candidate Time (s)": float(t_cand)})
            match_flags.append(0)
            scores.append(0.0)
            continue
        elif status == "err":
            per_file.append({"file": name, "N": n, "status": "error",
                             "error_code": "solve_exception", "error_message": str(payload),
                             "Baseline Exact Time (s)": float(t_exact)})
            match_flags.append(0)
            scores.append(0.0)
            continue
        else:
            cand_tour = payload

        ok, ec = _validate_tour(cand_tour, n)
        if not ok:
            per_file.append({"file": name, "N": n, "status": "invalid_tour",
                             "error_code": ec, "Baseline Exact Time (s)": float(t_exact),
                             "Candidate Time (s)": float(t_cand)})
            match_flags.append(0)
            scores.append(0.0)
            continue

        cand_len = _tour_len(coords, cand_tour)
        match = (abs(cand_len - exact_len) <= EPS)
        score = (t_exact / t_cand) if (match and t_cand > 0) else 0.0
        per_file.append({
            "file": name, "N": n, "Exact Length": float(exact_len),
            "Length": float(cand_len), "Exact Match": bool(match),
            "Baseline Exact Time (s)": float(t_exact),
            "Candidate Time (s)": float(t_cand),
            "Score": float(score),
            "status": "ok" if match else "mismatch"
        })
        match_flags.append(1 if match else 0)
        scores.append(float(score))

    t_eval = time.time() - t_eval0
    _save_jsonl(per_file)
    _save_dir(per_file)

    if not scores:
        return EvaluationResult(
            metrics={"combined_score": 0.0, "error_code": "no_instances",
                     "error_message": "No instances evaluated"},
            artifacts={"per_file_metrics": per_file}
        )

    combined = float(np.mean(scores))
    exact_match_rate = float(np.mean(match_flags)) if match_flags else 0.0

    return EvaluationResult(
        metrics={
            "combined_score": combined,
            "exact_match_rate": exact_match_rate,
            "eval_time": float(t_eval),
            "instances_total": int(len(items)),
            "generator": "synthetic",
            "n_range": f"[{GEN_MIN_N},{GEN_MAX_N}]",
        },
        artifacts={"per_file_metrics": per_file}
    )

def evaluate_stage1(program_path: str): return evaluate(program_path)
def evaluate_stage2(program_path: str): return evaluate(program_path)
def evaluate_stage3(program_path: str): return evaluate(program_path)
