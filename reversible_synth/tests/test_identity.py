"""
Tests for identity circuit generation.
"""

import pytest
from reversible_synth.permutation import Permutation
from reversible_synth.gates import CustomGate, Circuit
from reversible_synth.identity_generator import IdentityGenerator


class TestIdentityGenerator:
    """Tests for non-trivial identity generation."""
    
    def test_generator_creation(self):
        """Generator should initialize correctly."""
        gen = IdentityGenerator(3)
        assert gen.n_bits == 3
        assert len(gen.gates) > 0
    
    def test_guaranteed_generates_identity(self):
        """Guaranteed method should always produce identity circuit."""
        gen = IdentityGenerator(3)
        
        for _ in range(10):
            circuit = gen.generate_guaranteed(min_length=4)
            
            assert circuit is not None
            assert circuit.to_permutation().is_identity()
    
    def test_random_nontrivial_is_identity(self):
        """Random non-trivial should produce identity when successful."""
        gen = IdentityGenerator(3)
        
        circuit = gen.generate_random_nontrivial(target_length=8, max_attempts=200)
        
        if circuit is not None:
            assert circuit.to_permutation().is_identity()
    
    def test_hardness_score_zero_for_non_identity(self):
        """Non-identity circuits should have zero hardness score."""
        gen = IdentityGenerator(3)
        
        gate = CustomGate(0, 1, 2, 3)
        circuit = Circuit(3, [gate])
        
        score = gen.hardness_score(circuit)
        assert score == 0
    
    def test_double_gate_is_identity(self):
        """Any gate applied twice is identity."""
        for t in range(3):
            for c1 in range(3):
                for c2 in range(3):
                    if t != c1 and t != c2 and c1 != c2:
                        gate = CustomGate(t, c1, c2, 3)
                        circuit = Circuit(3, [gate, gate])
                        assert circuit.to_permutation().is_identity()
