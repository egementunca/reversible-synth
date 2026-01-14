# Research Progress: Reversible Circuit Synthesis & Identity Templates

## Overview

This document summarizes the synthesis framework and identity template generator developed for circuit obfuscation research.

---

## 1. Synthesis Algorithm Fixes

### Problem Identified
The original synthesis algorithms had a **permutation composition bug**. When prepending a gate `g` to a circuit `C`:

```
Circuit [g, c1, c2, ...] applies gates left-to-right: g first, then c1, etc.
Permutation: p_c2 * p_c1 * p_g  (rightmost applied first)
```

The code was computing `gate_perm * current_perm` instead of `current_perm * gate_perm`.

### Fix Applied
Changed composition order in:
- `synthesis_exact.py`: BFS, bidirectional BFS, enumerate_all, MITM
- `synthesis_heuristic.py`: TransformationSynthesizer, OutputPermutationSynthesizer

**Result**: All 48 tests now pass.

---

## 2. Non-Trivial Identity Generator

### Motivation
For circuit obfuscation, we need identity circuits that are **hard to simplify**:
- Not just `C || C⁻¹` (circuit + its reverse)
- No adjacent cancellations (`g·g = I`)
- No "pushable" cancellations (gate commutes to meet its copy)

### Algorithm

```
1. Generate random circuit C₁ of length k
2. Compute inverse permutation: P⁻¹ = C₁.to_permutation().inverse()
3. Synthesize C₂ implementing P⁻¹ using BFS (finds DIFFERENT structure)
4. Verify C₂ ≠ C₁.inverse() structurally
5. Check C₁ || C₂ has no trivial patterns
6. Return if non-trivial, else retry
```

### Hardness Metrics

| Metric | Description | Weight |
|--------|-------------|--------|
| Length | More gates = harder | 0.4 per gate |
| Diversity | Unique gates / total | ×3.0 |
| Entanglement | Shared lines between adjacent gates | ×1.5 |
| Non-commuting | Adjacent gates that conflict | ×2.0 |
| Asymmetry | Halves structurally different | ×3.0 |

### Trivial Pattern Detection

1. **Adjacent pairs**: Scan for `gates[i] == gates[i+1]`
2. **Commuting cancellation**: For each pair `gates[i] == gates[j]`, check if all gates between them commute with `gates[i]`

---

## 3. Performance Results

### Local Benchmarks

| Width | BFS Cache | Cache Size | Gen Rate | Notes |
|-------|-----------|------------|----------|-------|
| 3 | 0.03s | 0.8 MB | 2000/s | 10K permutations |
| 4 | 13.5s | 240 MB | 2029/s | 2.8M permutations |
| 5 | ~30min | ~2 GB | ~50/s | Estimated |
| 6+ | Hours | 10+ GB | Use cluster | |

### Sample Generation Run (Width 4)

```
Width:     4
Count:     50
Length:    8

Generated:  50/50 (100%)
Duplicates: 0
Rate:       2029 circuits/s
```

---

## 4. Infrastructure

### Database
- SQLite with WAL mode (concurrent access safe)
- Hash-based deduplication (SHA256 of canonical gate sequence)
- Indexed by width and depth

### Cluster Scripts
- `precompute_bfs.py`: Cache BFS tables
- `generate_identities.py`: Main generator
- `submit_all_jobs.py`: Job orchestration
- `template_database.py`: DB operations

---

## 5. Next Steps

1. **Cluster deployment**: Run width 5-8 generation
2. **Quality analysis**: Evaluate hardness distribution
3. **Obfuscation integration**: Use templates in circuit obfuscator
4. **Canonical forms**: Investigate permutation-equivalence classes

---

## 6. Code Examples

### Generate Templates
```python
from reversible_synth import NonTrivialIdentityGenerator

gen = NonTrivialIdentityGenerator(n_bits=4)
circuit = gen.generate_fast(target_length=8)
print(f"Length: {len(circuit)}, Score: {gen.hardness_score(circuit):.1f}")
```

### Draw Circuit
```python
from reversible_synth.identity_synthesis import draw_circuit

print(draw_circuit(circuit, compact=False))
# Output:
# w0 ────○────●────○────●──
# w1 ───[X]──[X]──[X]──[X]─
# w2 ────●────○────●────○──
```

### Verify Identity
```python
from reversible_synth.identity_synthesis import verify_identity

verify_identity(circuit, verbose=True)
# Circuit: 8 gates, 4 wires
# Permutation: [0, 1, 2, 3, ...]
# Is identity: True
```
