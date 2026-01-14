# Reversible Synth - Comprehensive Documentation and Status

This repo implements reversible circuit synthesis and identity-template generation
for a custom universal gate (ECA57-style gate). It is primarily a research
prototype to explore synthesis algorithms and obfuscation-friendly identity
circuits.

The core idea: circuits are built from a single reversible, self-inverse gate
defined as:

  Target XOR (Control1 OR NOT Control2)

This gate is treated as universal for reversible synthesis in this codebase.

---

## 1. Goals and Scope

Primary goals:
- Implement reversible circuit synthesis for a custom gate.
- Generate non-trivial identity circuits to use as obfuscation templates.
- Support exact (optimal) synthesis for small widths and heuristic methods for
  larger widths.
- Provide a cluster-friendly pipeline for large-scale template generation.

Out of scope (current code):
- Full integration with external SAT/SMT solvers.
- Formal optimality proofs beyond BFS search bounds.
- Canonical equivalence reduction beyond simple commutation checks.

---

## 2. Core Conventions and Representations

Bit and state conventions:
- Wires are zero-indexed.
- Circuit states are integers in [0, 2^n_bits).
- Circuit application is left-to-right (gate 0 first, then gate 1, etc).

Permutation composition:
- A circuit with gates [g1, g2] corresponds to permutation P = P_g2 * P_g1.
- In BFS, new permutations are built as `current * gate_perm` because gates are
  prepended (gate applies before existing circuit).

---

## 3. Core Data Structures

### CustomGate (reversible_synth/gates.py)
Definition:
- target, control1, control2, n_bits
- Activates when control1 == 1 OR control2 == 0.
- Self-inverse (applying twice cancels).

Key methods:
- apply(state): flips target bit if activation condition holds.
- to_permutation(): returns a Permutation object for the gate.
- conflicts_with(other): heuristic commutation check.
- all_gates/distinct_gates: enumerates allowed gate set.

Notes:
- If allow_same_line=True, target/control lines may overlap. This is useful for
  exploratory research but can include degenerate gates.

### Circuit (reversible_synth/gates.py)
Represents a list of CustomGate objects.

Key methods:
- apply(state): sequentially applies gates.
- to_permutation(): map all basis states to outputs.
- inverse(): reverse gate order (self-inverse gates).
- concatenate(other): concatenates two circuits.
- depth(): max number of gates touching any wire.
- has_adjacent_inverse_pair(): detects trivial g,g cancellation.
- has_commuting_cancellation(): detects identical gates that can commute.

### Permutation (reversible_synth/permutation.py)
Represents a mapping over 2^n states.

Key methods:
- __mul__: permutation composition (self(other(x))).
- inverse(), is_identity(), to_cycles().
- distance_to(other): number of mismatched outputs (used by heuristics).

Notes:
- Stored as a list; treat as immutable in practice for safe hashing.

---

## 4. Synthesis Algorithms

### ExactSynthesizer (reversible_synth/synthesis_exact.py)
Algorithms:
- BFS: optimal synthesis up to max_depth.
- Bidirectional BFS: meet-in-the-middle from identity and target.
- enumerate_all: enumerate all reachable permutations up to max_depth.

Tradeoffs:
- Exact and optimal, but memory and time blow up rapidly with width.
- Best for n_bits <= 4 and small depths.

### MeetInTheMiddleSynthesizer
Precomputes all permutations up to half_depth, then searches from target to meet
the forward table. Fast for moderate sizes, but does not guarantee minimality
beyond its search horizon (2 * half_depth).

### TransformationSynthesizer (heuristic)
Greedy distance-based synthesis:
- Uses permutation distance (mismatched outputs).
- Uses random moves to escape local minima.
- Multi-start mode tries several random restarts.

### OutputPermutationSynthesizer (heuristic)
Fixes outputs one index at a time without breaking already-correct positions.
Useful conceptually, but scales poorly since it iterates over all outputs
(2^n positions).

### GeneticSynthesizer (heuristic)
Randomized genetic search over gate sequences. Useful for exploration but
non-deterministic and not guaranteed to converge.

---

## 5. Identity Template Generation (Obfuscation)

The repo includes two generators:

### IdentityGenerator (reversible_synth/identity_generator.py)
Older generator with several strategies:
- generate_random_nontrivial: random half + heuristic inverse synthesis.
- generate_via_synthesis: random half + exact or heuristic inverse synthesis.
- generate_interleaved: interleaves gates, then synthesizes a closing sequence.
- generate_guaranteed: always returns identity using C || C^-1, with gate
  shuffling to hide triviality.

Limitations:
- Heuristic synthesis may fail for larger widths.
- Non-triviality checks are heuristic and rely on commutation checks.

### NonTrivialIdentityGenerator (reversible_synth/identity_synthesis.py)
Preferred generator for non-trivial templates:
- Builds random half C1.
- Synthesizes C2 for inverse permutation using randomized heuristic or BFS.
- Enforces structural dissimilarity vs C1^-1.
- Uses stronger non-triviality checks and hardness scoring.

Key utilities:
- generate(): main generator with dissimilarity threshold.
- generate_fast(): uses BFS table enumeration for fast lookup.
- generate_best_of_n(): picks highest hardness score.
- draw_circuit(): ASCII diagram for human inspection.
- verify_identity(): explicit permutation check.

Hardness scoring factors:
- Length, gate diversity, entanglement, non-commuting adjacency, asymmetry.
These are heuristics, not formal obfuscation metrics.

---

## 6. Scripts and Cluster Pipeline

### scripts/precompute_bfs.py
Enumerates all permutations up to a depth and writes a pickle cache. Used to
speed up identity template generation, especially at width >= 5.

### scripts/generate_identities.py
Generates templates in bulk with optional:
- JSON output.
- SQLite database output.
- BFS cache usage.
- Verification of identities.

Exit code is non-zero if success rate is under 50%.

### scripts/template_database.py
SQLite storage with WAL mode and hash-based deduplication.
- Hash is based on the exact gate sequence (not commutation-canonical).
- Useful for large batch runs on clusters.

### scripts/submit_all_jobs.py
Orchestrates BFS precompute and batch template generation via qsub.

### scripts/run_identity.sh, scripts/precompute_bfs_job.sh, scripts/setup_env.sh
Cluster wrappers for SGE/qsub environments.

---

## 7. Data Artifacts

Generated directories (created at runtime):
- cache/: pickled BFS tables.
- data/templates.db: SQLite database for templates.
- results/: JSON outputs if not using DB.
- logs/: job logs for cluster runs.

These are not committed by default.

---

## 8. Test Coverage

Test files:
- reversible_synth/tests/test_gates.py
  - Gate truth table, self-inverse, conflict detection, Circuit basics.
- reversible_synth/tests/test_synthesis.py
  - BFS synthesis, MITM, heuristic identity case.
  - Bidirectional BFS test only checks non-None result.
- reversible_synth/tests/test_identity.py
  - IdentityGenerator behavior and hardness scoring basics.
- reversible_synth/tests/test_identity_synthesis.py
  - NonTrivialIdentityGenerator behavior, triviality checks, similarity score.

Not covered by tests:
- scripts/ (cluster, caching, DB).
- verify_identity and draw_circuit helpers.
- OutputPermutationSynthesizer and GeneticSynthesizer on non-trivial targets.
- Permutation metrics like to_cycles(), hamming_distance_sum().

Note: Tests are present but not run in this documentation pass.

---

## 9. Current Status (What Is Implemented)

Implemented and usable:
- Gate, circuit, permutation core types.
- Exact synthesis (BFS, bidirectional, enumerate_all).
- Meet-in-the-middle synthesis.
- Several heuristic syntheses.
- Non-trivial identity template generation with hardness scoring.
- Cluster-compatible pipeline for large-scale generation.

Recent fix already integrated:
- Permutation composition order when prepending gates has been corrected in
  synthesis algorithms (see RESEARCH_PROGRESS.md).

Not integrated (yet):
- External SAT/SMT solving (a SWORD solver bundle is included but unused).
- Canonical simplification beyond heuristic commutation checks.
- Formal correctness proofs for heuristic generators.

Scaling status:
- Width 3-4 runs locally with BFS.
- Width 5+ needs caching and typically a cluster setup.

---

## 10. Known Limitations and Caveats

- Commutation logic (conflicts_with) is heuristic. Some commuting or
  non-commuting cases may be misclassified.
- Non-triviality checks only detect obvious cancellation patterns.
- Identity generation uses randomness with no global seeding control.
- BFS and MITM explode in memory with width and depth.
- TemplateDatabase deduplication uses exact gate order, not equivalence under
  commutation or inversion.
- Bidirectional BFS tests currently only assert non-None, so optimality is not
  fully validated.

---

## 11. Quick Start

Install (editable):
```bash
pip install -e .
```

Run demo:
```bash
python -m reversible_synth.demo
```

Generate a single template:
```python
from reversible_synth import NonTrivialIdentityGenerator

gen = NonTrivialIdentityGenerator(n_bits=3)
circuit = gen.generate_fast(target_length=6)
```

Run tests:
```bash
pytest
```

---

## 12. Suggested Next Steps

If you want to extend the repo:
- Add tests for scripts, caching, and DB behavior.
- Benchmark bidirectional BFS correctness and optimality.
- Add canonicalization beyond commutation heuristics.
- Integrate external solvers (SWORD or SAT) for exact synthesis at larger widths.
- Add reproducible seeding controls for identity generation.

---

## 13. Repo Map (Quick Reference)

Core library:
- reversible_synth/gates.py
- reversible_synth/permutation.py
- reversible_synth/synthesis_exact.py
- reversible_synth/synthesis_heuristic.py
- reversible_synth/identity_generator.py
- reversible_synth/identity_synthesis.py

Utilities and scripts:
- reversible_synth/demo.py
- scripts/precompute_bfs.py
- scripts/generate_identities.py
- scripts/template_database.py
- scripts/submit_all_jobs.py
- scripts/run_identity.sh
- scripts/precompute_bfs_job.sh
- scripts/setup_env.sh

Docs:
- README.md
- RESEARCH_PROGRESS.md
- CLUSTER_GUIDE.md
*** End Patch}"""
