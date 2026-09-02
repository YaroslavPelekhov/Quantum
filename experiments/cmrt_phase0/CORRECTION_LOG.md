# CMRT Phase-0 correction log

The first full offline execution completed before the independent code-review
message arrived.  Its terminal decision was already
`KILL_CMRT_AS_ASTAR_SOURCE` (4/10 gates), but review found several checks that
could have been too permissive in a hypothetical positive run.

Before using or committing the result, the evaluator was corrected and the
complete frozen cohort was rerun without changing any graph, schedule, noise,
threshold, seed, simulator output, or promotion criterion:

1. G4 now includes `nominal_noise` and `exact_noiseless`, in addition to the
   three approximate baselines, in matched-count error comparisons.
2. G6 now requires a matched-count advantage over every baseline separately
   inside each primary snapshot, as well as the registered absolute accuracy
   and coverage.
3. G8 now computes fallback fraction on held-out rows, consistent with the
   statement that binding gates apply to the primary held-out split.
4. Exact zero gaps now raise an error rather than being silently assigned the
   negative sign.
5. The nonbinding shot audit explicitly labels Newcombe-Wilson intervals as
   descriptive rather than exact familywise guarantees.

These corrections can only make promotion harder.  They are disclosed because
the code should remain safe against false promotion even though they do not
rescue, tune, or reinterpret the observed negative result.

The frozen global hash split is also retained unchanged.  It happens to place
all `n=9` and `n=13` graphs in calibration, leaving no held-out examples in
those two size strata.  This weakens external validity and is counted against
escalation; changing to a favorable stratified split after seeing results would
be post-hoc redesign.

## Final independent-audit disclosures

An independent read-only audit approved the terminal negative decision and
recomputed the conformal quantile, gate outcomes, tables, hashes, and archive
counts.  It also identified the following provenance and presentation limits:

1. The pre-correction evaluator and first negative output were not separately
   archived or hashed.  The current corrected run is internally reproducible,
   but the statement that its cohort and simulator values were unchanged from
   that first run cannot be reconstructed from this package alone.
2. The preregistration described one local IBM job/snapshot.  Read-only object
   discovery subsequently recovered two distinct historical jobs.  Both use the
   same graph and backend, change the penalty between jobs, and lack complete
   transpilation/calibration provenance.  Neither enters a promotion gate; both
   are retained only to audit ingestion.
3. The original generated prose reported the upper central ideal-gap observation
   for 108 rows (`5.987e-05`).  The final report now uses the conventional
   average-of-two-middle median (`5.835e-05`).  This does not affect any gate.
4. The held-out Spearman value repeats simulator spread across noise snapshots
   and clusters rows inside 12 graphs.  It is therefore descriptive and has no
   block-aware uncertainty claim.
5. G10 records the manual prior-art audit as a Boolean rather than deriving it
   mechanically.  That limitation cannot affect the present kill decision; any
   future positive screen would require signed/manual review provenance rather
   than an unconditional evaluator flag.
