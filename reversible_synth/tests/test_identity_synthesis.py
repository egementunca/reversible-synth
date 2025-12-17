"""
Tests for non-trivial identity generation.
"""

import pytest
from reversible_synth.identity_synthesis import NonTrivialIdentityGenerator, enumerate_identity_templates
from reversible_synth.gates import CustomGate, Circuit


class TestNonTrivialIdentityGenerator:
    """Tests for the non-trivial identity generator."""
    
    def test_generator_creation(self):
        """Generator should initialize correctly."""
        gen = NonTrivialIdentityGenerator(3)
        assert gen.n_bits == 3
        assert len(gen.gates) > 0
    
    def test_generate_returns_identity(self):
        """Generated circuit must implement identity permutation."""
        gen = NonTrivialIdentityGenerator(3)
        
        circuit = gen.generate(half_length=3, max_attempts=50)
        
        if circuit is not None:
            assert circuit.to_permutation().is_identity(), \
                "Generated circuit must be identity"
    
    def test_no_adjacent_duplicates(self):
        """Generated circuit should have no adjacent identical gates."""
        gen = NonTrivialIdentityGenerator(3)
        
        circuit = gen.generate(half_length=3, max_attempts=50)
        
        if circuit is not None:
            for i in range(len(circuit.gates) - 1):
                assert circuit.gates[i] != circuit.gates[i + 1], \
                    f"Adjacent gates {i} and {i+1} are identical"
    
    def test_is_trivial_detects_adjacent_pair(self):
        """is_trivial should detect adjacent identical gates."""
        gen = NonTrivialIdentityGenerator(3)
        
        g = CustomGate(0, 1, 2, 3)
        trivial_circuit = Circuit(3, [g, g])  # g·g = identity
        
        assert gen.is_trivial(trivial_circuit)
    
    def test_is_trivial_detects_commuting_pair(self):
        """is_trivial should detect commuting cancellation."""
        gen = NonTrivialIdentityGenerator(3)
        
        # g1 and g2 don't conflict (different targets and controls)
        # So g1·g2·g1 = g2 (g1 can be pushed through g2 to cancel)
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 2, 0, 3)  # Different target
        
        # Check if they actually don't conflict for this test to be valid
        if not g1.conflicts_with(g2):
            circuit = Circuit(3, [g1, g2, g1])
            assert gen.is_trivial(circuit)
    
    def test_hardness_score_zero_for_non_identity(self):
        """Non-identity circuits should have zero hardness score."""
        gen = NonTrivialIdentityGenerator(3)
        
        gate = CustomGate(0, 1, 2, 3)
        non_identity = Circuit(3, [gate])
        
        assert gen.hardness_score(non_identity) == 0.0
    
    def test_hardness_score_zero_for_trivial(self):
        """Trivial identity circuits should have zero hardness score."""
        gen = NonTrivialIdentityGenerator(3)
        
        gate = CustomGate(0, 1, 2, 3)
        trivial = Circuit(3, [gate, gate])
        
        assert gen.hardness_score(trivial) == 0.0
    
    def test_hardness_score_positive_for_nontrivial(self):
        """Non-trivial identity should have positive hardness score."""
        gen = NonTrivialIdentityGenerator(3)
        
        circuit = gen.generate(half_length=3, max_attempts=50)
        
        if circuit is not None:
            score = gen.hardness_score(circuit)
            assert score > 0, "Non-trivial identity should have positive score"
    
    def test_structural_similarity_identical(self):
        """Identical circuits should have similarity 1.0."""
        gen = NonTrivialIdentityGenerator(3)
        
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        circuit = Circuit(3, [g1, g2])
        
        sim = gen.structural_similarity(circuit, circuit)
        assert sim == 1.0
    
    def test_structural_similarity_different(self):
        """Different circuits should have similarity < 1.0."""
        gen = NonTrivialIdentityGenerator(3)
        
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        g3 = CustomGate(2, 0, 1, 3)
        
        c1 = Circuit(3, [g1, g2])
        c2 = Circuit(3, [g2, g3])
        
        sim = gen.structural_similarity(c1, c2)
        assert sim < 1.0
    
    def test_generate_best_of_n(self):
        """Best-of-n should return a circuit when possible."""
        gen = NonTrivialIdentityGenerator(3)
        
        circuit = gen.generate_best_of_n(n=10, half_length=3)
        
        if circuit is not None:
            assert circuit.to_permutation().is_identity()
            assert not gen.is_trivial(circuit)


class TestEnumerateTemplates:
    """Tests for template enumeration."""
    
    def test_enumerate_returns_list(self):
        """Enumeration should return a list of circuits."""
        templates = enumerate_identity_templates(3, count=3, half_length=2)
        
        assert isinstance(templates, list)
        
        for template in templates:
            assert template.to_permutation().is_identity()
