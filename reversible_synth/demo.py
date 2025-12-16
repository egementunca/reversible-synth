"""
Demo script showing the reversible circuit synthesizer in action.
"""

from .permutation import Permutation
from .gates import CustomGate, Circuit
from .synthesis_exact import ExactSynthesizer, MeetInTheMiddleSynthesizer
from .synthesis_heuristic import TransformationSynthesizer, GeneticSynthesizer
from .identity_generator import IdentityGenerator


def demo_gate_basics():
    """Demonstrate the custom gate."""
    print("=" * 60)
    print("CUSTOM GATE DEMO: Target XOR (Control1 OR NOT Control2)")
    print("=" * 60)
    
    gate = CustomGate(target=0, control1=1, control2=2, n_bits=3)
    print(f"\nGate: {gate}")
    print("\nTruth table for activation (c1 OR NOT c2):")
    print("c1 | c2 | activates | target flips")
    print("-" * 40)
    
    for c1 in [0, 1]:
        for c2 in [0, 1]:
            activates = (c1 == 1) or (c2 == 0)
            print(f" {c1} |  {c2} |     {1 if activates else 0}     |      {'Yes' if activates else 'No'}")
    
    perm = gate.to_permutation()
    print(f"\nPermutation: {perm._map}")
    print(f"Cycles: {perm.to_cycles()}")
    
    print("\n--- Self-Inverse Property ---")
    test_state = 0b101
    after_once = gate.apply(test_state)
    after_twice = gate.apply(after_once)
    print(f"State {test_state:03b} -> {after_once:03b} -> {after_twice:03b}")
    print(f"Applying gate twice returns to original: {test_state == after_twice}")


def demo_synthesis():
    """Demonstrate synthesis algorithms."""
    print("\n" + "=" * 60)
    print("SYNTHESIS DEMO")
    print("=" * 60)
    
    n_bits = 3
    target_gate = CustomGate(target=1, control1=0, control2=2, n_bits=n_bits)
    target_perm = target_gate.to_permutation()
    
    print(f"\nTarget: {target_gate}")
    print(f"Target permutation: {target_perm._map}")
    
    print("\n--- Exact Synthesis (BFS) ---")
    exact = ExactSynthesizer(n_bits)
    circuit = exact.synthesize_bfs(target_perm, max_depth=5)
    
    if circuit:
        print(f"Found circuit with {len(circuit)} gate(s): {circuit.gates}")
        print(f"Verification: {circuit.to_permutation() == target_perm}")
    else:
        print("No circuit found")
    
    print("\n--- Bidirectional BFS ---")
    circuit_bi = exact.synthesize_bidirectional(target_perm, max_depth=5)
    if circuit_bi:
        print(f"Found circuit with {len(circuit_bi)} gate(s): {circuit_bi.gates}")
    
    print("\n--- Complex Permutation ---")
    complex_perm = Permutation.random(n_bits)
    print(f"Random permutation: {complex_perm._map}")
    
    circuit_complex = exact.synthesize_bidirectional(complex_perm, max_depth=8)
    if circuit_complex:
        print(f"Found circuit with {len(circuit_complex)} gates")
        print(f"Verification: {circuit_complex.to_permutation() == complex_perm}")
    else:
        print("Trying heuristic synthesis...")
        heuristic = TransformationSynthesizer(n_bits)
        circuit_complex = heuristic.synthesize_multistart(complex_perm, restarts=10)
        if circuit_complex:
            print(f"Heuristic found circuit with {len(circuit_complex)} gates")


def demo_identity_generation():
    """Demonstrate identity circuit generation."""
    print("\n" + "=" * 60)
    print("IDENTITY CIRCUIT GENERATION DEMO")
    print("=" * 60)
    
    n_bits = 3
    gen = IdentityGenerator(n_bits)
    
    print("\nGenerating non-trivial identity circuits...")
    
    print("\n--- Method 1: Random Non-Trivial ---")
    circuit1 = gen.generate_random_nontrivial(target_length=8, max_attempts=100)
    if circuit1:
        print(f"Generated circuit with {len(circuit1)} gates")
        print(f"Is identity: {circuit1.to_permutation().is_identity()}")
        print(f"Has adjacent inverse pair: {circuit1.has_adjacent_inverse_pair()}")
        print(f"Hardness score: {gen.hardness_score(circuit1):.2f}")
    else:
        print("Failed to generate (try again)")
    
    print("\n--- Method 2: Via Synthesis ---")
    circuit2 = gen.generate_via_synthesis(min_length=6)
    if circuit2:
        print(f"Generated circuit with {len(circuit2)} gates")
        print(f"Is identity: {circuit2.to_permutation().is_identity()}")
        print(f"Hardness score: {gen.hardness_score(circuit2):.2f}")
    
    print("\n--- Method 3: Best of 10 ---")
    best = gen.generate_best_of_n(n=10, target_length=10)
    if best:
        print(f"Best circuit has {len(best)} gates")
        print(f"Hardness score: {gen.hardness_score(best):.2f}")
        print(f"Depth: {best.depth()}")
    
    print("\n--- Guaranteed Generation ---")
    guaranteed = gen.generate_guaranteed(min_length=6)
    print(f"Guaranteed circuit with {len(guaranteed)} gates")
    print(f"Is identity: {guaranteed.to_permutation().is_identity()}")


def demo_circuit_analysis():
    """Demonstrate circuit analysis features."""
    print("\n" + "=" * 60)
    print("CIRCUIT ANALYSIS DEMO")
    print("=" * 60)
    
    n_bits = 3
    g1 = CustomGate(0, 1, 2, n_bits)
    g2 = CustomGate(1, 0, 2, n_bits)
    g3 = CustomGate(2, 0, 1, n_bits)
    
    circuit = Circuit(n_bits, [g1, g2, g3, g2, g1])
    
    print(f"\nCircuit: {circuit.gates}")
    print(f"Length: {len(circuit)}")
    print(f"Depth: {circuit.depth()}")
    
    perm = circuit.to_permutation()
    print(f"Permutation: {perm._map}")
    print(f"Is identity: {perm.is_identity()}")
    
    print(f"\nHas adjacent inverse pair: {circuit.has_adjacent_inverse_pair()}")
    has_commuting, pair = circuit.has_commuting_cancellation()
    print(f"Has commuting cancellation: {has_commuting}")
    
    inv = circuit.inverse()
    print(f"\nInverse circuit: {inv.gates}")
    composed = circuit.concatenate(inv)
    print(f"Circuit || Inverse = identity: {composed.to_permutation().is_identity()}")


def main():
    """Run all demos."""
    print("\n" + "#" * 60)
    print("# REVERSIBLE CIRCUIT SYNTHESIZER DEMO")
    print("# Gate: Target XOR (Control1 OR NOT Control2)")
    print("#" * 60)
    
    demo_gate_basics()
    demo_synthesis()
    demo_identity_generation()
    demo_circuit_analysis()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
