"""
Permutation representation and operations for reversible circuits.
"""

from typing import List, Tuple, Dict, Optional, Set
from functools import reduce
import itertools


class Permutation:
    """
    Represents a permutation on n bits (2^n elements).
    Internally stored as a mapping: input -> output
    """
    
    def __init__(self, n_bits: int, mapping: Optional[List[int]] = None):
        """
        Initialize a permutation.
        
        Args:
            n_bits: Number of bits (defines domain size as 2^n_bits)
            mapping: List where mapping[i] = j means input i maps to output j
                    If None, creates identity permutation
        """
        self.n_bits = n_bits
        self.size = 1 << n_bits  # 2^n_bits
        
        if mapping is None:
            self._map = list(range(self.size))
        else:
            if len(mapping) != self.size:
                raise ValueError(f"Mapping must have {self.size} elements")
            if set(mapping) != set(range(self.size)):
                raise ValueError("Mapping must be a valid permutation")
            self._map = list(mapping)
    
    def __call__(self, x: int) -> int:
        """Apply permutation to input x."""
        return self._map[x]
    
    def __eq__(self, other: 'Permutation') -> bool:
        return self.n_bits == other.n_bits and self._map == other._map
    
    def __hash__(self) -> int:
        return hash(tuple(self._map))
    
    def __repr__(self) -> str:
        return f"Permutation({self.n_bits}, {self._map})"
    
    def __mul__(self, other: 'Permutation') -> 'Permutation':
        """
        Compose permutations: (self * other)(x) = self(other(x))
        """
        if self.n_bits != other.n_bits:
            raise ValueError("Permutations must have same number of bits")
        new_map = [self._map[other._map[i]] for i in range(self.size)]
        return Permutation(self.n_bits, new_map)
    
    def inverse(self) -> 'Permutation':
        """Return the inverse permutation."""
        inv_map = [0] * self.size
        for i, j in enumerate(self._map):
            inv_map[j] = i
        return Permutation(self.n_bits, inv_map)
    
    def is_identity(self) -> bool:
        """Check if this is the identity permutation."""
        return self._map == list(range(self.size))
    
    def to_cycles(self) -> List[Tuple[int, ...]]:
        """
        Return cycle notation of the permutation.
        Excludes fixed points (1-cycles).
        """
        visited = [False] * self.size
        cycles = []
        
        for start in range(self.size):
            if visited[start]:
                continue
            
            cycle = []
            current = start
            while not visited[current]:
                visited[current] = True
                cycle.append(current)
                current = self._map[current]
            
            if len(cycle) > 1:
                cycles.append(tuple(cycle))
        
        return cycles
    
    def cycle_structure(self) -> Dict[int, int]:
        """
        Return cycle structure: {cycle_length: count}
        """
        cycles = self.to_cycles()
        fixed = sum(1 for i in range(self.size) if self._map[i] == i)
        
        structure = {}
        if fixed > 0:
            structure[1] = fixed
        
        for cycle in cycles:
            length = len(cycle)
            structure[length] = structure.get(length, 0) + 1
        
        return structure
    
    def hamming_distance_sum(self) -> int:
        """
        Sum of Hamming distances between each input and its output.
        Useful as a complexity metric.
        """
        total = 0
        for i in range(self.size):
            total += bin(i ^ self._map[i]).count('1')
        return total
    
    def to_truth_table(self) -> List[List[int]]:
        """
        Convert to truth table format.
        Returns list of output bit vectors for each input.
        """
        table = []
        for i in range(self.size):
            out = self._map[i]
            bits = [(out >> b) & 1 for b in range(self.n_bits)]
            table.append(bits)
        return table
    
    @classmethod
    def from_truth_table(cls, table: List[List[int]]) -> 'Permutation':
        """Create permutation from truth table."""
        size = len(table)
        n_bits = size.bit_length() - 1
        
        mapping = []
        for bits in table:
            val = sum(b << i for i, b in enumerate(bits))
            mapping.append(val)
        
        return cls(n_bits, mapping)
    
    @classmethod
    def identity(cls, n_bits: int) -> 'Permutation':
        """Create identity permutation."""
        return cls(n_bits)
    
    @classmethod
    def random(cls, n_bits: int) -> 'Permutation':
        """Create random permutation."""
        import random
        mapping = list(range(1 << n_bits))
        random.shuffle(mapping)
        return cls(n_bits, mapping)
    
    def distance_to(self, other: 'Permutation') -> int:
        """
        Number of positions where permutations differ.
        """
        if self.n_bits != other.n_bits:
            raise ValueError("Permutations must have same size")
        return sum(1 for i in range(self.size) if self._map[i] != other._map[i])
