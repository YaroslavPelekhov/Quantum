# TherapyBench: A Constraint-Grounded Benchmark for Rule-Governed Therapeutic Dialogue

This repository contains the dataset, human evaluation results, and evaluation scripts for the paper:

> **RAVR-S: State-Sensitive Verification and Repair for Trustworthy Rule-Governed LLM Dialogue**
> Accepted at the ICML 2026 Workshop on Trustworthy AI for Good

---

## Dataset Overview

### `benchmark/`

| File | Description |
|---|---|
| `state_sensitive_mini_dialogue_pairs_v3_random_balanced.csv` | 16 three-turn mini-dialogue pairs across 4 clinical domains (PTSD, panic disorder, schizophrenia, personality disorders), comparing RAVR-S vs RAVR and Self-Refine |
| `state_sensitive_mini_dialogue_pairs_v3_random_balanced_key.csv` | Ground-truth key: maps each pair ID to methods A and B |
| `automated_eval_1500turns.json` | Full automated evaluation outputs for 1,500 dialogue turns across 3 LLM providers (GPT-4o, DeepSeek-Chat, Qwen-2.5), 4 methods, with proof objects, adherence scores, and repair deltas |

### `human_eval/`

| File | Description |
|---|---|
| `state_sensitive_v3_N20_metrics.json` | Stage 2 human evaluation results (N=20, 1,600 judgments): win/loss/tie counts per dimension and method |
| `human_eval_stage1_combined.json` | Stage 1 screening results (N=10, 1,440 judgments): pairwise win rates across 4 methods, Krippendorff's α, Wilson CIs |
| `human_eval_stage1_combined.md` | Markdown summary of Stage 1 results |

### `predicates/`

| File | Description |
|---|---|
| `virtual_patient_cases.json` | 10 therapeutic case definitions with full predicate inventories (58 unique typed predicates across CBT, DBT, EMDR, ABA, Psychodynamic, Rogerian, MI, Schema Therapy, Narrative Therapy, Psychopharmacology) |

### `scripts/`

| File | Description |
|---|---|
| `analyze_state_sensitive_form.py` | Fetch and analyze Stage 2 human evaluation responses from Google Forms |
| `analyze_pairwise_combined.py` | Fetch and combine Stage 1 responses from multiple form sources, compute Krippendorff's α |
| `stats_report.py` | Statistical testing: bootstrap CIs, permutation tests, effect sizes |

---

## Predicate Schema

Each predicate in `virtual_patient_cases.json` has the following structure:

```json
{
  "id": "cbt_thought_focus",
  "family": "method_focus",
  "type": "mandatory",
  "description": "Response must address the patient's automatic thoughts or cognitive distortions",
  "methodology": "CBT"
}
```

**Predicate families:**
- `method_focus` — methodology-specific technique constraints (mandatory)
- `directivity` — limits on question count, directive language, unsolicited advice (mandatory)
- `safety` — crisis detection, boundary maintenance, scope (mandatory)
- `collaborative_stance` — warmth, validation, autonomy support (recommended)
- `citation_grounding` — evidence references must map to retrieved sources (mandatory)

---

## Mini-Dialogue Format

Each row in `state_sensitive_mini_dialogue_pairs_v3_random_balanced.csv`:

```
pair_id, domain, case_id, turn_count, dialogue_a, dialogue_b, method_a, method_b, target_comparison
```

Dialogues are 3-turn exchanges (patient → therapist × 3), representing a realistic therapy micro-session with a defined initial patient state (trust, distress, fatigue).

---

## Reproducing Human Evaluation Analysis

```bash
pip install -r requirements.txt

# Stage 2 (RAVR-S vs RAVR vs Self-Refine, N=20)
export GOOGLE_CLIENT_ID=...
export GOOGLE_CLIENT_SECRET=...
export GOOGLE_REFRESH_TOKEN=...

python scripts/analyze_state_sensitive_form.py \
  --create-json <form_create_response.json> \
  --key-csv benchmark/state_sensitive_mini_dialogue_pairs_v3_random_balanced_key.csv \
  --out-json results/stage2_metrics.json \
  --out-md results/stage2_metrics.md

# Stage 1 (4-method screening, N=10)
python scripts/analyze_pairwise_combined.py \
  --form-jsons <v7_create.json> <v8_create.json> \
  --key-csv <stage1_key.csv> \
  --out-json results/stage1_combined.json \
  --out-md results/stage1_combined.md
```

---

## Statistics

```bash
python scripts/stats_report.py \
  --input benchmark/automated_eval_1500turns.json \
  --out-json results/stats.json \
  --out-md results/stats.md
```

---

## License

Data: CC BY 4.0
Code: MIT

All dialogue scenarios are **synthetic** — no real patient data is included.
