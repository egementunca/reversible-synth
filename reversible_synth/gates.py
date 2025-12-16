"""
Custom universal gate: Target XOR (Control1 OR NOT Control2)
And circuit representation.
"""

from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from .permutation import Permutation


@dataclass(frozen=True)
class CustomGate:
    """
    The universal gate: Target XOR (Control1 OR NOT Control2)
    
    When c1=1 OR c2=0, the target bit is flipped.
    
    Attributes:
        target: Index of target bit (0-indexed)
        control1: Index of positive control bit
        control2: Index of negative control bit
        n_bits: Total number of bits in the circuit
    """
    target: int
    control1: int
    control2: int
    n_bits: int
    
    def __post_init__(self):
        if not (0 <= self.target < self.n_bits):
            raise ValueError(f"Target {self.target} out of range for {self.n_bits} bits")
        if not (0 <= self.control1 < self.n_bits):
            raise ValueError(f"Control1 {self.control1} out of range")
        if not (0 <= self.control2 < self.n_bits):
            raise ValueError(f"Control2 {self.control2} out of range")
    
    def __repr__(self) -> str:
        return f"G(t={self.target}, c1={self.control1}, c2={self.control2})"
    
    def applies(self, state: int) -> bool:
        """
        Check if gate activates (target flips) for given state.
        Condition: c1 OR NOT c2
        """
        c1_bit = (state >> self.control1) & 1
        c2_bit = (state >> self.control2) & 1
        return c1_bit == 1 or c2_bit == 0
    
    def apply(self, state: int) -> int:
        """Apply gate to a single basis state."""
        if self.applies(state):
            return state ^ (1 << self.target)
        return state
    
    def to_permutation(self) -> Permutation:
        """Convert gate to its permutation representation."""
        size = 1 << self.n_bits
        mapping = [self.apply(i) for i in range(size)]
        return Permutation(self.n_bits, mapping)
    
    def is_trivial_identity(self) -> bool:
        """
        Check if this gate is trivially the identity.
        This gate is never identity - it always activates for some inputs.
        """
        return False
    
    def inverse(self) -> 'CustomGate':
        """
        This gate is self-inverse!
        Applying it twice returns to original state.
        """
        return CustomGate(self.target, self.control1, self.control2, self.n_bits)
    
    def conflicts_with(self, other: 'CustomGate') -> bool:
        """
        Check if two gates potentially conflict (don't commute trivially).
        Gates commute if they don't share target/control dependencies.
        """
        if self.target in {other.control1, other.control2}:
            return True
        if other.target in {self.control1, self.control2}:
            return True
        if self.target == other.target:
            return True
        return False
    
    @classmethod
    def all_gates(cls, n_bits: int, allow_same_line: bool = True) -> List['CustomGate']:
        """
        Generate all possible gates for n_bits.
        
        Args:
            n_bits: Number of bits
            allow_same_line: If True, allow control and target on same line
        """
        gates = []
        for t in range(n_bits):
            for c1 in range(n_bits):
                for c2 in range(n_bits):
                    if not allow_same_line:
                        if t == c1 or t == c2 or c1 == c2:
                            continue
                    gates.append(cls(t, c1, c2, n_bits))
        return gates
    
    @classmethod
    def distinct_gates(cls, n_bits: int) -> List['CustomGate']:
        """
        Generate all gates with distinct lines (t, c1, c2 all different).
        These are the 'standard' gates.
        """
        return cls.all_gates(n_bits, allow_same_line=False)


class Circuit:
    """
    A reversible circuit as a sequence of CustomGates.
    """
    
    def __init__(self, n_bits: int, gates: Optional[List[CustomGate]] = None):
        self.n_bits = n_bits
        self.gates: List[CustomGate] = list(gates) if gates else []
    
    def __len__(self) -> int:
        return len(self.gates)
    
    def __repr__(self) -> str:
        return f"Circuit({self.n_bits}, {self.gates})"
    
    def append(self, gate: CustomGate) -> 'Circuit':
        """Append gate and return self for chaining."""
        if gate.n_bits != self.n_bits:
            raise ValueError("Gate bit count mismatch")
        self.gates.append(gate)
        return self
    
    def prepend(self, gate: CustomGate) -> 'Circuit':
        """Prepend gate and return self for chaining."""
        if gate.n_bits != self.n_bits:
            raise ValueError("Gate bit count mismatch")
        self.gates.insert(0, gate)
        return self
    
    def copy(self) -> 'Circuit':
        """Create a copy of this circuit."""
        return Circuit(self.n_bits, self.gates.copy())
    
    def apply(self, state: int) -> int:
        """Apply circuit to a single basis state."""
        for gate in self.gates:
            state = gate.apply(state)
        return state
    
    def to_permutation(self) -> Permutation:
        """Convert circuit to its permutation representation."""
        size = 1 << self.n_bits
        mapping = [self.apply(i) for i in range(size)]
        return Permutation(self.n_bits, mapping)
    
    def inverse(self) -> 'Circuit':
        """
        Return the inverse circuit.
        Since each gate is self-inverse, just reverse the order.
        """
        return Circuit(self.n_bits, list(reversed(self.gates)))
    
    def concatenate(self, other: 'Circuit') -> 'Circuit':
        """Concatenate two circuits."""
        if self.n_bits != other.n_bits:
            raise ValueError("Circuits must have same bit count")
        return Circuit(self.n_bits, self.gates + other.gates)
    
    def has_adjacent_inverse_pair(self) -> bool:
        """
        Check for trivial cancellation: adjacent identical gates.
        Since our gate is self-inverse, identical adjacent gates cancel.
        """
        for i in range(len(self.gates) - 1):
            if self.gates[i] == self.gates[i + 1]:
                return True
        return False
    
    def has_commuting_cancellation(self) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        Check if there are two identical gates that can be brought together
        by commutation (i.e., all gates between them commute with both).
        
        Returns (found, (idx1, idx2)) or (False, None)
        """
        for i in range(len(self.gates)):
            for j in range(i + 2, len(self.gates)):
                if self.gates[i] == self.gates[j]:
                    can_commute = True
                    for k in range(i + 1, j):
                        if self.gates[i].conflicts_with(self.gates[k]):
                            can_commute = False
                            break
                    if can_commute:
                        return True, (i, j)
        return False, None
    
    def gate_cost(self) -> int:
        """Simple cost metric: number of gates."""
        return len(self.gates)
    
    def depth(self) -> int:
        """
        Circuit depth: maximum number of gates on any single wire.
        """
        wire_depths = [0] * self.n_bits
        for gate in self.gates:
            lines = {gate.target, gate.control1, gate.control2}
            max_depth = max(wire_depths[l] for l in lines)
            new_depth = max_depth + 1
            for l in lines:
                wire_depths[l] = new_depth
        return max(wire_depths) if wire_depths else 0
    
    @classmethod
    def empty(cls, n_bits: int) -> 'Circuit':
        """Create empty circuit."""
        return cls(n_bits)
    
    @classmethod
    def from_gates(cls, gates: List[CustomGate]) -> 'Circuit':
        """Create circuit from list of gates."""
        if not gates:
            raise ValueError("Need at least one gate to infer n_bits")
        return cls(gates[0].n_bits, gates)
