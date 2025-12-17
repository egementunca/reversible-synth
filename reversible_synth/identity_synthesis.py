"""
Non-trivial identity circuit generation using synthesis.

Generates identity circuits that resist simplification by:
1. Avoiding adjacent identical gates
2. Avoiding commuting cancellation patterns
3. Ensuring structural dissimilarity between circuit halves
"""

from typing import List, Optional, Tuple, Set
import random
from .permutation import Permutation
from .gates import CustomGate, Circuit
from .synthesis_exact import ExactSynthesizer


class NonTrivialIdentityGenerator:
    """
    Generate identity circuits that resist simplification.
    
    Strategy:
    1. Build random first half C1
    2. Synthesize C2 for C1.inverse().to_permutation() using BFS
    3. Verify C2 is structurally different from C1.inverse()
    4. Return C1 || C2
    """
    
    def __init__(self, n_bits: int, allow_same_line: bool = False):
        """
        Args:
            n_bits: Number of bits/wires
            allow_same_line: Allow gates with shared control/target lines
        """
        self.n_bits = n_bits
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
        self.synth = ExactSynthesizer(n_bits, allow_same_line=allow_same_line)
    
    def generate(self, half_length: int = 3, 
                 max_attempts: int = 100,
                 min_dissimilarity: float = 0.3) -> Optional[Circuit]:
        """
        Generate a non-trivial identity circuit.
        
        Args:
            half_length: Target length for each half of the circuit
            max_attempts: Maximum generation attempts
            min_dissimilarity: Minimum structural dissimilarity required (0-1)
        
        Returns:
            Circuit implementing identity, or None if generation fails
        """
        from .synthesis_heuristic import TransformationSynthesizer
        
        heuristic_synth = TransformationSynthesizer(self.n_bits)
        
        for attempt in range(max_attempts):
            # Step 1: Build random first half
            c1 = self._build_random_half(half_length)
            if c1 is None:
                continue
            
            # Step 2: Get inverse permutation
            perm = c1.to_permutation()
            inv_perm = perm.inverse()
            
            # Step 3: Try different synthesis approaches
            # Use heuristic synthesis with randomization for variety
            c2 = heuristic_synth._synthesize_randomized(inv_perm, max_steps=half_length * 3)
            
            if c2 is None:
                # Fall back to BFS
                c2 = self.synth.synthesize_bfs(inv_perm, max_depth=half_length + 3)
            
            if c2 is None:
                continue
            
            # Verify c2 actually implements the inverse permutation
            if c2.to_permutation() != inv_perm:
                continue
            
            # Step 4: Check for junction problems
            # The last gate of c1 and first gate of c2 should not be the same
            if len(c1) > 0 and len(c2) > 0:
                if c1.gates[-1] == c2.gates[0]:
                    continue  # Would create adjacent duplicate
            
            # Step 5: Check structural dissimilarity
            c1_inv = c1.inverse()
            similarity = self.structural_similarity(c2, c1_inv)
            
            if similarity < (1.0 - min_dissimilarity):
                # Combine
                full = c1.concatenate(c2)
                
                # Verify it's identity and non-trivial
                if full.to_permutation().is_identity() and not self.is_trivial(full):
                    return full
        
        return None
    
    def generate_interleaved(self, num_gates: int = 6, 
                              max_attempts: int = 100) -> Optional[Circuit]:
        """
        Generate identity by building from both ends and meeting in middle.
        
        Strategy:
        1. Pick random gates and track cumulative permutation
        2. At each step, avoid gates that would create trivial patterns
        3. Synthesize closing sequence when reaching target length
        """
        from .synthesis_heuristic import TransformationSynthesizer
        
        heuristic = TransformationSynthesizer(self.n_bits)
        
        for _ in range(max_attempts):
            circuit = Circuit.empty(self.n_bits)
            current_perm = Permutation.identity(self.n_bits)
            
            # Build most of the circuit randomly
            target_build = max(2, num_gates - 2)
            last_gate = None
            
            for _ in range(target_build):
                # Choose gate that doesn't create trivial pattern
                candidates = [
                    g for g in self.gates 
                    if g != last_gate  # No adjacent duplicates
                ]
                
                if not candidates:
                    break
                
                gate = random.choice(candidates)
                circuit.append(gate)
                current_perm = current_perm * gate.to_permutation()
                last_gate = gate
            
            if len(circuit) < target_build:
                continue
            
            # Now synthesize the closing sequence
            inv_perm = current_perm.inverse()
            closing = heuristic._synthesize_randomized(inv_perm, max_steps=num_gates)
            
            if closing is None or len(closing) == 0:
                continue
            
            # Check junction
            if circuit.gates[-1] == closing.gates[0]:
                continue
            
            full = circuit.concatenate(closing)
            
            if full.to_permutation().is_identity() and not self.is_trivial(full):
                return full
        
        return None

    def generate_best_of_n(self, n: int = 20, 
                           half_length: int = 3) -> Optional[Circuit]:
        """
        Generate n identity circuits and return the one with highest hardness.
        
        Args:
            n: Number of attempts
            half_length: Target length for each half
        
        Returns:
            Hardest identity circuit found, or None
        """
        best_circuit = None
        best_score = -1.0
        
        for _ in range(n):
            circuit = self.generate(half_length=half_length, max_attempts=10)
            if circuit is not None:
                score = self.hardness_score(circuit)
                if score > best_score:
                    best_score = score
                    best_circuit = circuit
        
        return best_circuit
    
    def _build_random_half(self, length: int) -> Optional[Circuit]:
        """
        Build random circuit avoiding adjacent duplicates.
        
        Args:
            length: Number of gates
        
        Returns:
            Random circuit with no adjacent identical gates
        """
        circuit = Circuit.empty(self.n_bits)
        last_gate = None
        
        for _ in range(length):
            # Pick gate different from last
            candidates = [g for g in self.gates if g != last_gate]
            if not candidates:
                return None
            
            gate = random.choice(candidates)
            circuit.append(gate)
            last_gate = gate
        
        return circuit
    
    def structural_similarity(self, c1: Circuit, c2: Circuit) -> float:
        """
        Measure structural similarity between two circuits.
        
        Returns:
            Float between 0 (completely different) and 1 (identical)
        """
        if len(c1) == 0 and len(c2) == 0:
            return 1.0
        if len(c1) == 0 or len(c2) == 0:
            return 0.0
        
        # Component 1: Gate sequence similarity (edit distance normalized)
        seq_sim = self._sequence_similarity(c1.gates, c2.gates)
        
        # Component 2: Gate multiset similarity
        set_sim = self._multiset_similarity(c1.gates, c2.gates)
        
        # Component 3: Control pattern similarity
        pattern_sim = self._control_pattern_similarity(c1, c2)
        
        # Weighted average
        return 0.4 * seq_sim + 0.3 * set_sim + 0.3 * pattern_sim
    
    def _sequence_similarity(self, gates1: List[CustomGate], 
                             gates2: List[CustomGate]) -> float:
        """Gate sequence similarity using longest common subsequence."""
        n, m = len(gates1), len(gates2)
        if n == 0 and m == 0:
            return 1.0
        
        # LCS length
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if gates1[i-1] == gates2[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        
        lcs_len = dp[n][m]
        return lcs_len / max(n, m)
    
    def _multiset_similarity(self, gates1: List[CustomGate], 
                             gates2: List[CustomGate]) -> float:
        """Multiset similarity using Jaccard-like metric."""
        from collections import Counter
        
        c1 = Counter(gates1)
        c2 = Counter(gates2)
        
        # Intersection and union of multisets
        intersection = sum((c1 & c2).values())
        union = sum((c1 | c2).values())
        
        if union == 0:
            return 1.0
        return intersection / union
    
    def _control_pattern_similarity(self, c1: Circuit, c2: Circuit) -> float:
        """Compare control/target line usage patterns."""
        def get_line_signature(circuit: Circuit) -> List[Tuple[int, int, int]]:
            return [(g.target, g.control1, g.control2) for g in circuit.gates]
        
        sig1 = get_line_signature(c1)
        sig2 = get_line_signature(c2)
        
        if not sig1 and not sig2:
            return 1.0
        
        # Count matching signatures
        matches = sum(1 for s in sig1 if s in sig2)
        return matches / max(len(sig1), len(sig2))
    
    def is_trivial(self, circuit: Circuit) -> bool:
        """
        Check if circuit has trivial simplification patterns.
        
        Checks:
        1. Adjacent identical gates
        2. Commuting cancellation (gates that can be pushed to cancel)
        """
        # Check 1: Adjacent identical gates
        for i in range(len(circuit.gates) - 1):
            if circuit.gates[i] == circuit.gates[i + 1]:
                return True
        
        # Check 2: Commuting cancellation
        has_commuting, _ = self._find_commuting_cancellation(circuit)
        return has_commuting
    
    def _find_commuting_cancellation(self, circuit: Circuit) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Find two identical gates that can be brought together via commutation.
        
        Returns:
            (found, (idx1, idx2)) if cancellation exists, else (False, None)
        """
        gates = circuit.gates
        n = len(gates)
        
        for i in range(n):
            for j in range(i + 2, n):
                if gates[i] == gates[j]:
                    # Check if all gates between i and j commute with gates[i]
                    can_commute = True
                    for k in range(i + 1, j):
                        if gates[i].conflicts_with(gates[k]):
                            can_commute = False
                            break
                    
                    if can_commute:
                        return True, (i, j)
        
        return False, None
    
    def hardness_score(self, circuit: Circuit) -> float:
        """
        Score how hard the identity circuit is to simplify.
        
        Higher score = harder to simplify.
        
        Factors:
        - Is it actually identity? (required)
        - No trivial patterns (required)
        - Gate diversity
        - Line entanglement between adjacent gates
        - Length
        - Structural complexity
        """
        # Basic requirements
        if not circuit.to_permutation().is_identity():
            return 0.0
        if self.is_trivial(circuit):
            return 0.0
        
        score = 0.0
        n = len(circuit.gates)
        
        if n == 0:
            return 0.0
        
        # 1. Length component (longer = harder, with diminishing returns)
        score += min(5.0, n * 0.4)
        
        # 2. Gate diversity (more unique gates = harder)
        unique_gates = len(set(circuit.gates))
        diversity = unique_gates / n
        score += diversity * 3.0
        
        # 3. Line entanglement (shared lines between adjacent gates)
        entanglement = 0
        for i in range(n - 1):
            g1, g2 = circuit.gates[i], circuit.gates[i + 1]
            lines1 = {g1.target, g1.control1, g1.control2}
            lines2 = {g2.target, g2.control1, g2.control2}
            entanglement += len(lines1 & lines2)
        
        if n > 1:
            avg_entanglement = entanglement / (n - 1)
            score += avg_entanglement * 1.5
        
        # 4. No long commuting runs (penalize if many adjacent gates commute)
        commuting_runs = 0
        for i in range(n - 1):
            if not circuit.gates[i].conflicts_with(circuit.gates[i + 1]):
                commuting_runs += 1
        
        # Lower is better for commuting runs
        if n > 1:
            commute_ratio = commuting_runs / (n - 1)
            score += (1.0 - commute_ratio) * 2.0
        
        # 5. Structural asymmetry between halves
        if n >= 4:
            mid = n // 2
            first_half = Circuit(self.n_bits, circuit.gates[:mid])
            second_half = Circuit(self.n_bits, circuit.gates[mid:])
            
            asymmetry = 1.0 - self.structural_similarity(first_half, second_half.inverse())
            score += asymmetry * 3.0
        
        return score
    
    def generate_fast(self, target_length: int = 6, 
                      max_attempts: int = 500) -> Optional[Circuit]:
        """
        Speed-optimized generation using BFS with cached permutation table.
        
        Much faster than generate() by:
        1. Pre-enumerating all reachable permutations up to half the target length
        2. Random walk + table lookup for closing
        
        Args:
            target_length: Approximate target circuit length
            max_attempts: Maximum generation attempts
        
        Returns:
            Non-trivial identity circuit, or None
        """
        half_depth = max(2, target_length // 2)
        
        # Pre-enumerate all short circuits (cached in synth object)
        perm_to_circuit = self.synth.enumerate_all(max_depth=half_depth + 1)
        
        for _ in range(max_attempts):
            # Build random first half avoiding adjacent duplicates
            c1 = self._build_random_half(half_depth)
            if c1 is None:
                continue
            
            # Get inverse permutation
            perm = c1.to_permutation()
            inv_perm = perm.inverse()
            
            # Fast lookup for closing circuit
            if inv_perm not in perm_to_circuit:
                continue
            
            c2 = perm_to_circuit[inv_perm]
            
            # Check junction - no adjacent duplicates
            if len(c1) > 0 and len(c2) > 0:
                if c1.gates[-1] == c2.gates[0]:
                    continue
            
            # Combine
            full = c1.concatenate(c2)
            
            # Verify and check non-trivial
            if full.to_permutation().is_identity() and not self.is_trivial(full):
                return full
        
        return None


def draw_circuit(circuit: Circuit, compact: bool = True) -> str:
    """
    Draw ASCII representation of a circuit.
    
    Args:
        circuit: The circuit to draw
        compact: If True, use compact format; otherwise full diagram
    
    Returns:
        String representation of the circuit
    """
    n_bits = circuit.n_bits
    gates = circuit.gates
    
    if not gates:
        return f"Empty circuit ({n_bits} wires)"
    
    if compact:
        # Compact format: one line per wire showing gate involvement
        lines = []
        lines.append(f"Circuit: {len(gates)} gates, {n_bits} wires")
        lines.append("")
        
        for g_idx, gate in enumerate(gates):
            lines.append(f"  [{g_idx}] target={gate.target}, ctrl1={gate.control1}, ctrl2={gate.control2}")
        
        lines.append("")
        lines.append("Wire diagram:")
        
        # Draw wire diagram
        for wire in range(n_bits):
            wire_str = f"  w{wire}: "
            for g_idx, gate in enumerate(gates):
                if gate.target == wire:
                    wire_str += "T"  # Target
                elif gate.control1 == wire:
                    wire_str += "+"  # Control 1 (positive)
                elif gate.control2 == wire:
                    wire_str += "-"  # Control 2 (negated)
                else:
                    wire_str += "─"  # Wire passes through
            
            lines.append(wire_str)
        
        return "\n".join(lines)
    else:
        # Full diagram with ASCII art
        lines = []
        lines.append(f"Circuit: {len(gates)} gates, {n_bits} wires")
        lines.append("=" * 40)
        
        # Each gate gets a column
        col_width = 5
        
        # Header
        header = "     "
        for i in range(len(gates)):
            header += f" G{i:<3}"
        lines.append(header)
        lines.append("")
        
        for wire in range(n_bits):
            wire_str = f"w{wire} ──"
            for gate in gates:
                if gate.target == wire:
                    wire_str += "─[X]─"
                elif gate.control1 == wire:
                    wire_str += "──●──"
                elif gate.control2 == wire:
                    wire_str += "──○──"
                else:
                    wire_str += "─────"
            
            lines.append(wire_str)
        
        return "\n".join(lines)


def verify_identity(circuit: Circuit, verbose: bool = False) -> bool:
    """
    Explicitly verify that a circuit implements the identity permutation.
    
    Args:
        circuit: The circuit to verify
        verbose: If True, print detailed information
    
    Returns:
        True if circuit is identity, False otherwise
    """
    perm = circuit.to_permutation()
    is_id = perm.is_identity()
    
    if verbose:
        print(f"Circuit: {len(circuit)} gates, {circuit.n_bits} wires")
        print(f"Permutation: {perm}")
        print(f"Is identity: {is_id}")
        
        if not is_id:
            # Show which positions differ
            identity = Permutation.identity(circuit.n_bits)
            diffs = []
            for i in range(1 << circuit.n_bits):
                if perm(i) != identity(i):
                    diffs.append(f"{i}->{perm(i)} (expected {identity(i)})")
            print(f"Differences: {diffs[:5]}{'...' if len(diffs) > 5 else ''}")
    
    return is_id


def enumerate_identity_templates(n_bits: int, 
                                  count: int = 10,
                                  half_length: int = 3) -> List[Circuit]:
    """
    Convenience function to generate multiple identity templates.
    
    Args:
        n_bits: Number of bits/wires
        count: Number of templates to generate
        half_length: Target length for each half
    
    Returns:
        List of non-trivial identity circuits
    """
    gen = NonTrivialIdentityGenerator(n_bits)
    templates = []
    
    for _ in range(count):
        circuit = gen.generate_best_of_n(n=10, half_length=half_length)
        if circuit is not None:
            templates.append(circuit)
    
    return templates


def generate_templates_fast(n_bits: int, count: int, 
                            target_length: int = 6) -> List[Circuit]:
    """
    Fast batch generation of identity templates.
    
    Optimized for speed using BFS table lookup.
    
    Args:
        n_bits: Number of bits/wires
        count: Number of templates to generate
        target_length: Approximate length of each template
    
    Returns:
        List of verified non-trivial identity circuits
    """
    gen = NonTrivialIdentityGenerator(n_bits)
    templates = []
    
    attempts_per_template = max(100, count * 10)
    
    for _ in range(count):
        circuit = gen.generate_fast(
            target_length=target_length, 
            max_attempts=attempts_per_template
        )
        if circuit is not None:
            # Double-check it's identity
            assert circuit.to_permutation().is_identity(), "BUG: Generated non-identity!"
            templates.append(circuit)
    
    return templates

