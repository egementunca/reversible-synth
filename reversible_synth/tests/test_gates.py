"""
Tests for gates module.
"""

import pytest
from reversible_synth.gates import CustomGate, Circuit
from reversible_synth.permutation import Permutation


class TestCustomGate:
    """Tests for the custom universal gate."""
    
    def test_gate_creation(self):
        """Gate should be created with valid parameters."""
        gate = CustomGate(target=0, control1=1, control2=2, n_bits=3)
        assert gate.target == 0
        assert gate.control1 == 1
        assert gate.control2 == 2
        assert gate.n_bits == 3
    
    def test_gate_invalid_target(self):
        """Should reject invalid target."""
        with pytest.raises(ValueError):
            CustomGate(target=3, control1=1, control2=2, n_bits=3)
    
    def test_gate_activation_truth_table(self):
        """Test gate activation: c1 OR NOT c2."""
        gate = CustomGate(target=0, control1=1, control2=2, n_bits=3)
        
        # c1=0, c2=0 -> NOT c2 = 1 -> activates
        assert gate.applies(0b000) == True
        # c1=0, c2=1 -> c1=0, NOT c2=0 -> doesn't activate
        assert gate.applies(0b100) == False
        # c1=1, c2=0 -> c1=1 -> activates
        assert gate.applies(0b010) == True
        # c1=1, c2=1 -> c1=1 -> activates
        assert gate.applies(0b110) == True
    
    def test_gate_apply(self):
        """Test gate application to states."""
        gate = CustomGate(target=0, control1=1, control2=2, n_bits=3)
        
        # When activates, target bit flips
        assert gate.apply(0b000) == 0b001  # Flips bit 0
        assert gate.apply(0b001) == 0b000  # Flips bit 0 back
        
        # When doesn't activate (c1=0, c2=1), no change
        assert gate.apply(0b100) == 0b100
    
    def test_gate_self_inverse(self):
        """Gate should be self-inverse."""
        gate = CustomGate(target=0, control1=1, control2=2, n_bits=3)
        
        for state in range(8):
            after_once = gate.apply(state)
            after_twice = gate.apply(after_once)
            assert after_twice == state, f"Failed for state {state}"
    
    def test_gate_to_permutation(self):
        """Gate should produce valid permutation."""
        gate = CustomGate(target=0, control1=1, control2=2, n_bits=3)
        perm = gate.to_permutation()
        
        assert perm.n_bits == 3
        assert set(perm._map) == set(range(8))
        
        # Permutation should match direct application
        for i in range(8):
            assert perm(i) == gate.apply(i)
    
    def test_gate_permutation_self_inverse(self):
        """Gate permutation squared should be identity."""
        gate = CustomGate(target=1, control1=0, control2=2, n_bits=3)
        perm = gate.to_permutation()
        
        squared = perm * perm
        assert squared.is_identity()
    
    def test_all_gates_count(self):
        """Count of all possible gates."""
        # With distinct lines: n * (n-1) * (n-2) choices
        gates_3bit = CustomGate.distinct_gates(3)
        assert len(gates_3bit) == 3 * 2 * 1  # 6
        
        gates_4bit = CustomGate.distinct_gates(4)
        assert len(gates_4bit) == 4 * 3 * 2  # 24
    
    def test_gate_conflicts(self):
        """Test gate conflict detection."""
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)  # Target of g2 is control of g1
        g3 = CustomGate(2, 1, 0, 3)  # Different target, shares controls
        
        assert g1.conflicts_with(g2)  # g2.target in g1.controls
        assert g2.conflicts_with(g1)
        
    def test_gate_hashable(self):
        """Gates should be hashable for use in sets."""
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(0, 1, 2, 3)
        g3 = CustomGate(1, 0, 2, 3)
        
        s = {g1, g2, g3}
        assert len(s) == 2


class TestCircuit:
    """Tests for Circuit class."""
    
    def test_empty_circuit(self):
        """Empty circuit should be identity."""
        circuit = Circuit.empty(3)
        assert len(circuit) == 0
        assert circuit.to_permutation().is_identity()
    
    def test_single_gate_circuit(self):
        """Single gate circuit."""
        gate = CustomGate(0, 1, 2, 3)
        circuit = Circuit(3, [gate])
        
        assert len(circuit) == 1
        assert circuit.to_permutation() == gate.to_permutation()
    
    def test_circuit_append(self):
        """Appending gates to circuit."""
        circuit = Circuit.empty(3)
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        
        circuit.append(g1).append(g2)
        
        assert len(circuit) == 2
        assert circuit.gates == [g1, g2]
    
    def test_circuit_prepend(self):
        """Prepending gates to circuit."""
        circuit = Circuit.empty(3)
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        
        circuit.prepend(g1).prepend(g2)
        
        assert len(circuit) == 2
        assert circuit.gates == [g2, g1]
    
    def test_circuit_apply(self):
        """Circuit application to states."""
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        circuit = Circuit(3, [g1, g2])
        
        for state in range(8):
            expected = g2.apply(g1.apply(state))
            assert circuit.apply(state) == expected
    
    def test_circuit_inverse(self):
        """Circuit inverse."""
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        circuit = Circuit(3, [g1, g2])
        
        inv = circuit.inverse()
        
        # Inverse should have reversed gates
        assert inv.gates == [g2, g1]
        
        # Circuit * inverse = identity
        composed = circuit.concatenate(inv)
        assert composed.to_permutation().is_identity()
    
    def test_circuit_concatenate(self):
        """Circuit concatenation."""
        c1 = Circuit(3, [CustomGate(0, 1, 2, 3)])
        c2 = Circuit(3, [CustomGate(1, 0, 2, 3)])
        
        combined = c1.concatenate(c2)
        
        assert len(combined) == 2
        assert combined.gates == c1.gates + c2.gates
    
    def test_adjacent_inverse_pair_detection(self):
        """Detect adjacent identical gates (which cancel)."""
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        
        # No adjacent pair
        c1 = Circuit(3, [g1, g2, g1])
        assert not c1.has_adjacent_inverse_pair()
        
        # Has adjacent pair
        c2 = Circuit(3, [g1, g1, g2])
        assert c2.has_adjacent_inverse_pair()
    
    def test_circuit_depth(self):
        """Circuit depth calculation."""
        g1 = CustomGate(0, 1, 2, 3)
        g2 = CustomGate(1, 0, 2, 3)
        
        circuit = Circuit(3, [g1, g2])
        depth = circuit.depth()
        
        assert depth >= 1
    
    def test_circuit_copy(self):
        """Circuit copy should be independent."""
        c1 = Circuit(3, [CustomGate(0, 1, 2, 3)])
        c2 = c1.copy()
        
        c2.append(CustomGate(1, 0, 2, 3))
        
        assert len(c1) == 1
        assert len(c2) == 2
