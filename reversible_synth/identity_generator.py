"""
Non-trivial identity circuit generation for obfuscation.
"""

from typing import List, Optional, Tuple, Set
import random
from .permutation import Permutation
from .gates import CustomGate, Circuit
from .synthesis_exact import ExactSynthesizer
from .synthesis_heuristic import TransformationSynthesizer


class IdentityGenerator:
    """
    Generate non-trivial identity circuits for obfuscation.
    
    A non-trivial identity circuit:
    - Computes the identity permutation
    - Has no adjacent inverse pairs (same gate twice)
    - Has no obvious commuting cancellations
    - Is not a simple C || C^(-1) concatenation
    """
    
    def __init__(self, n_bits: int, allow_same_line: bool = False):
        self.n_bits = n_bits
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
        self.gate_perms = [(g, g.to_permutation()) for g in self.gates]
    
    def _is_trivial(self, circuit: Circuit) -> bool:
        """Check if circuit has trivial reductions."""
        if circuit.has_adjacent_inverse_pair():
            return True
        has_commuting, _ = circuit.has_commuting_cancellation()
        return has_commuting
    
    def generate_random_nontrivial(self, target_length: int, 
                                    max_attempts: int = 1000) -> Optional[Circuit]:
        """
        Generate random identity circuit without trivial patterns.
        
        Strategy: Build circuit avoiding adjacent duplicates and 
        track permutation to close with inverse.
        """
        for _ in range(max_attempts):
            circuit = self._build_random_half(target_length // 2)
            if circuit is None:
                continue
            
            # Get inverse permutation
            perm = circuit.to_permutation()
            inv_perm = perm.inverse()
            
            # Synthesize inverse with different structure
            synth = TransformationSynthesizer(self.n_bits)
            inv_circuit = synth.synthesize(inv_perm, max_steps=target_length)
            
            if inv_circuit is None:
                continue
            
            # Combine
            full = circuit.concatenate(inv_circuit)
            
            # Check non-triviality
            if not self._is_trivial(full) and len(full) >= target_length // 2:
                return full
        
        return None
    
    def _build_random_half(self, length: int) -> Optional[Circuit]:
        """Build random circuit avoiding adjacent duplicates."""
        circuit = Circuit.empty(self.n_bits)
        last_gate = None
        
        for _ in range(length):
            # Pick random gate different from last
            candidates = [g for g in self.gates if g != last_gate]
            if not candidates:
                return None
            
            gate = random.choice(candidates)
            circuit.append(gate)
            last_gate = gate
        
        return circuit
    
    def generate_via_synthesis(self, min_length: int = 6) -> Optional[Circuit]:
        """
        Generate identity by:
        1. Create random circuit C1
        2. Synthesize C2 for inverse of C1's permutation
        3. Result: C1 || C2 = identity (if C2 found)
        
        The synthesis ensures C2 is structurally different from C1^(-1).
        """
        # Generate random first half
        half_len = max(3, min_length // 2)
        c1 = self._build_random_half(half_len)
        
        if c1 is None:
            return None
        
        # Get permutation and its inverse
        perm = c1.to_permutation()
        inv_perm = perm.inverse()
        
        # Try exact synthesis first for small cases
        if self.n_bits <= 3:
            exact = ExactSynthesizer(self.n_bits)
            c2 = exact.synthesize_bidirectional(inv_perm, max_depth=half_len + 2)
        else:
            # Use heuristic for larger
            heuristic = TransformationSynthesizer(self.n_bits)
            c2 = heuristic.synthesize_multistart(inv_perm, restarts=5, max_steps=half_len * 2)
        
        if c2 is None:
            return None
        
        # Combine and verify
        full = c1.concatenate(c2)
        
        # Verify it's identity
        if not full.to_permutation().is_identity():
            return None
        
        # Check non-triviality
        if self._is_trivial(full):
            return None
        
        return full
    
    def generate_interleaved(self, num_pairs: int = 4) -> Optional[Circuit]:
        """
        Generate interleaved complementary sequences.
        
        Strategy: Create pairs of gates that will eventually cancel,
        but interleave them to hide the cancellation.
        """
        # This is tricky with our gate (self-inverse)
        # We need gates g1, g2 such that g1*g2*g1*g2 = identity
        # or more complex patterns
        
        circuit = Circuit.empty(self.n_bits)
        used_gates: List[CustomGate] = []
        
        for _ in range(num_pairs):
            # Pick a gate we haven't used recently
            candidates = [g for g in self.gates if g not in used_gates[-2:]] if used_gates else self.gates
            if not candidates:
                candidates = self.gates
            
            g1 = random.choice(candidates)
            
            # Pick a second gate that doesn't trivially cancel
            candidates2 = [g for g in self.gates if g != g1]
            if not candidates2:
                continue
            g2 = random.choice(candidates2)
            
            # Add pattern: g1, g2
            circuit.append(g1)
            circuit.append(g2)
            used_gates.extend([g1, g2])
        
        # Now we need to close back to identity
        perm = circuit.to_permutation()
        if perm.is_identity():
            if not self._is_trivial(circuit):
                return circuit
        
        # Try to synthesize closing sequence
        inv_perm = perm.inverse()
        synth = TransformationSynthesizer(self.n_bits)
        closing = synth.synthesize(inv_perm, max_steps=num_pairs * 2)
        
        if closing is None:
            return None
        
        full = circuit.concatenate(closing)
        
        if full.to_permutation().is_identity() and not self._is_trivial(full):
            return full
        
        return None
    
    def hardness_score(self, circuit: Circuit) -> float:
        """
        Score how "hard" an identity circuit is to recognize.
        
        Higher score = harder to simplify.
        
        Factors:
        - Length: longer is harder
        - Gate diversity: more unique gates is harder
        - Entanglement: gates sharing lines is harder
        - No obvious patterns
        """
        if not circuit.to_permutation().is_identity():
            return 0.0
        
        if self._is_trivial(circuit):
            return 0.0
        
        score = 0.0
        
        # Length component (log scale)
        score += min(10, len(circuit) * 0.5)
        
        # Diversity: unique gates / total gates
        unique_gates = len(set(circuit.gates))
        if len(circuit) > 0:
            diversity = unique_gates / len(circuit)
            score += diversity * 5
        
        # Entanglement: average number of shared lines between adjacent gates
        entanglement = 0
        for i in range(len(circuit.gates) - 1):
            g1 = circuit.gates[i]
            g2 = circuit.gates[i + 1]
            lines1 = {g1.target, g1.control1, g1.control2}
            lines2 = {g2.target, g2.control1, g2.control2}
            entanglement += len(lines1 & lines2)
        
        if len(circuit) > 1:
            avg_entanglement = entanglement / (len(circuit) - 1)
            score += avg_entanglement * 2
        
        # Depth penalty for very shallow circuits
        depth = circuit.depth()
        if depth > 0:
            score += min(5, depth * 0.3)
        
        return score
    
    def generate_best_of_n(self, n: int = 10, target_length: int = 10) -> Optional[Circuit]:
        """
        Generate n identity circuits and return the one with highest hardness.
        """
        best_circuit = None
        best_score = -1
        
        for _ in range(n):
            # Try different generation methods
            method = random.choice(['random', 'synthesis', 'interleaved'])
            
            if method == 'random':
                circuit = self.generate_random_nontrivial(target_length)
            elif method == 'synthesis':
                circuit = self.generate_via_synthesis(target_length)
            else:
                circuit = self.generate_interleaved(target_length // 2)
            
            if circuit is not None:
                score = self.hardness_score(circuit)
                if score > best_score:
                    best_score = score
                    best_circuit = circuit
        
        return best_circuit
    
    def generate_guaranteed(self, min_length: int = 4) -> Circuit:
        """
        Generate an identity circuit guaranteed to succeed.
        
        Fallback: C || C^(-1) with different gate orderings.
        """
        # Build first half
        half = self._build_random_half(max(2, min_length // 2))
        
        if half is None:
            # Ultimate fallback: single gate twice
            gate = random.choice(self.gates)
            return Circuit(self.n_bits, [gate, gate])
        
        # Inverse is just reversed (gates are self-inverse)
        inv = half.inverse()
        
        # Try to shuffle the inverse to make it less obvious
        # while maintaining the same permutation
        shuffled_inv = self._shuffle_commuting(inv)
        
        return half.concatenate(shuffled_inv)
    
    def _shuffle_commuting(self, circuit: Circuit) -> Circuit:
        """
        Shuffle gates that commute to obscure structure.
        """
        gates = circuit.gates.copy()
        
        # Multiple passes of adjacent swaps for commuting gates
        for _ in range(len(gates) * 2):
            if len(gates) < 2:
                break
            
            i = random.randint(0, len(gates) - 2)
            g1, g2 = gates[i], gates[i + 1]
            
            # Swap if they commute
            if not g1.conflicts_with(g2):
                gates[i], gates[i + 1] = g2, g1
        
        return Circuit(self.n_bits, gates)
