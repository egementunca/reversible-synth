# Reversible Circuit Synthesizer

A Python library for synthesizing reversible circuits using a custom universal gate.

## Gate Definition

The universal gate is: **Target XOR (Control1 OR NOT Control2)**

```
Gate(target, control1, control2):
    output[target] = input[target] XOR (input[control1] OR NOT input[control2])
```

This gate is **self-inverse**: applying it twice returns to the original state.

## Features

### Circuit Synthesis
- **BFS Synthesis**: Find optimal (shortest) circuits for any permutation
- **Bidirectional BFS**: Faster optimal synthesis using meet-in-the-middle
- **Heuristic Synthesis**: Fast approximate synthesis for larger circuits
- **Meet-in-the-Middle**: Memory-time tradeoff for medium-size problems

### Identity Template Generation
Generate non-trivial identity circuits for circuit obfuscation:

```python
from reversible_synth import NonTrivialIdentityGenerator

gen = NonTrivialIdentityGenerator(n_bits=3)
circuit = gen.generate_fast(target_length=6)
```

Features:
- No adjacent identical gates (trivial cancellation)
- No commuting cancellation patterns
- Structural dissimilarity between halves
- Hardness scoring

## Documentation

See [DOCUMENTATION.md](DOCUMENTATION.md) for a comprehensive status overview,
including what's implemented, what's tested, and current limitations.

## Installation

```bash
pip install -e .
```

## Usage

### Basic Circuit Operations

```python
from reversible_synth import CustomGate, Circuit, Permutation

# Create a gate: target=0, control1=1, control2=2
gate = CustomGate(0, 1, 2, n_bits=3)

# Apply to input
result = gate.apply(0b101)  # Apply to binary 101

# Create circuit
circuit = Circuit(n_bits=3, gates=[gate1, gate2])
perm = circuit.to_permutation()
```

### Synthesis

```python
from reversible_synth import ExactSynthesizer, Permutation

synth = ExactSynthesizer(n_bits=3)

# Synthesize circuit for a permutation
perm = Permutation(3, [0, 2, 1, 3, 4, 5, 6, 7])  # Swap positions 1 and 2
circuit = synth.synthesize_bfs(perm, max_depth=10)
```

### Identity Templates

```python
from reversible_synth import NonTrivialIdentityGenerator
from reversible_synth.identity_synthesis import draw_circuit, verify_identity

gen = NonTrivialIdentityGenerator(3)
circuit = gen.generate_fast(target_length=6)

# Verify it's an identity
assert verify_identity(circuit)

# Draw the circuit
print(draw_circuit(circuit))
```

## Cluster Usage

See [CLUSTER_GUIDE.md](CLUSTER_GUIDE.md) for running large-scale generation on HPC clusters.

## Project Structure

```
reversible_synth/
├── permutation.py       # Permutation class
├── gates.py             # CustomGate and Circuit classes
├── synthesis_exact.py   # BFS, bidirectional, MITM synthesis
├── synthesis_heuristic.py # Heuristic synthesis algorithms
├── identity_generator.py  # Basic identity generation
├── identity_synthesis.py  # Non-trivial identity generation
└── tests/               # Test suite

scripts/
├── generate_identities.py  # Cluster generation script
├── precompute_bfs.py       # BFS table caching
├── template_database.py    # SQLite storage
└── *.sh                    # Job submission scripts
```

## Recent Changes

### Synthesis Bug Fix
Fixed permutation composition order in all synthesis algorithms. When prepending a gate to a circuit, the composition should be `current * gate_perm` (gate applied first), not `gate_perm * current`.

### Non-Trivial Identity Generator
New generator that creates identity circuits resistant to simplification:
- Uses BFS synthesis to find structurally different inverse circuits
- Detects and rejects trivial patterns (adjacent pairs, commuting cancellations)
- Includes hardness scoring for quality assessment

## Performance

| Width | BFS Cache Time | Generation Rate |
|-------|----------------|-----------------|
| 3 | <1s | 2000+/s |
| 4 | ~1min | 50/s |
| 5 | ~30min | 10/s |
| 6+ | Hours | Use cluster |

## License

Research use.
