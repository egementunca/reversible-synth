"""
Exact synthesis algorithms: BFS, Bidirectional BFS, Meet-in-the-Middle.
"""

from typing import List, Dict, Optional, Tuple, Set
from collections import deque
from .permutation import Permutation
from .gates import CustomGate, Circuit


class ExactSynthesizer:
    """
    Exact synthesis using BFS and bidirectional BFS.
    Guarantees optimal (shortest) circuits.
    """
    
    def __init__(self, n_bits: int, allow_same_line: bool = False):
        """
        Args:
            n_bits: Number of bits
            allow_same_line: Allow gates with shared control/target lines
        """
        self.n_bits = n_bits
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
        self.gate_perms = [(g, g.to_permutation()) for g in self.gates]
    
    def synthesize_bfs(self, target: Permutation, max_depth: int = 10) -> Optional[Circuit]:
        """
        BFS synthesis: find shortest circuit implementing target permutation.
        
        Returns None if no circuit found within max_depth.
        """
        if target.n_bits != self.n_bits:
            raise ValueError("Target permutation has wrong number of bits")
        
        identity = Permutation.identity(self.n_bits)
        
        if target == identity:
            return Circuit.empty(self.n_bits)
        
        # BFS: state = (current_perm, circuit)
        visited: Set[Permutation] = {identity}
        queue = deque([(identity, Circuit.empty(self.n_bits))])
        
        while queue:
            current_perm, current_circuit = queue.popleft()
            
            if len(current_circuit) >= max_depth:
                continue
            
            for gate, gate_perm in self.gate_perms:
                new_perm = current_perm * gate_perm
                
                if new_perm == target:
                    result = current_circuit.copy()
                    result.prepend(gate)
                    return result
                
                if new_perm not in visited:
                    visited.add(new_perm)
                    new_circuit = current_circuit.copy()
                    new_circuit.prepend(gate)
                    queue.append((new_perm, new_circuit))
        
        return None
    
    def synthesize_bidirectional(self, target: Permutation, max_depth: int = 10) -> Optional[Circuit]:
        """
        Bidirectional BFS: search from both identity and target.
        
        Forward: builds circuits from identity, forward[perm] = circuit C where C.to_perm() == perm
        Backward: builds circuits from target, backward[perm] = circuit C where C.to_perm() == perm
                  (starting from target, applying C gives perm)
        
        When meeting at P:
          - forward[P].to_perm() == P (identity -> P)
          - backward[P].to_perm() == P (target -> P)
          - backward[P].inverse() takes P -> target
          - So: forward[P] + backward[P].inverse() = identity -> P -> target
        """
        if target.n_bits != self.n_bits:
            raise ValueError("Target permutation has wrong number of bits")
        
        identity = Permutation.identity(self.n_bits)
        
        if target == identity:
            return Circuit.empty(self.n_bits)
        
        # forward[perm] = circuit C such that C.to_permutation() == perm
        forward: Dict[Permutation, Circuit] = {identity: Circuit.empty(self.n_bits)}
        # backward[perm] = circuit C such that starting from target and applying C gives perm
        backward: Dict[Permutation, Circuit] = {target: Circuit.empty(self.n_bits)}
        
        forward_queue = deque([identity])
        backward_queue = deque([target])
        
        for depth in range(max_depth // 2 + 1):
            # Expand forward (same as BFS: prepend gate, new_perm = current * gate_perm)
            next_forward = deque()
            while forward_queue:
                current = forward_queue.popleft()
                current_circuit = forward[current]
                
                if len(current_circuit) > depth:
                    next_forward.append(current)
                    continue
                
                for gate, gate_perm in self.gate_perms:
                    new_perm = current * gate_perm
                    
                    if new_perm in backward:
                        # forward reaches new_perm, backward reaches new_perm from target
                        # Combined: forward + backward.inverse() = identity -> target
                        fwd_circuit = current_circuit.copy()
                        fwd_circuit.prepend(gate)
                        bwd_circuit = backward[new_perm]
                        return fwd_circuit.concatenate(bwd_circuit.inverse())
                    
                    if new_perm not in forward:
                        new_circuit = current_circuit.copy()
                        new_circuit.prepend(gate)
                        forward[new_perm] = new_circuit
                        next_forward.append(new_perm)
            
            forward_queue = next_forward
            
            # Expand backward (same pattern: prepend gate, new_perm = current * gate_perm)
            next_backward = deque()
            while backward_queue:
                current = backward_queue.popleft()
                current_circuit = backward[current]
                
                if len(current_circuit) > depth:
                    next_backward.append(current)
                    continue
                
                for gate, gate_perm in self.gate_perms:
                    new_perm = current * gate_perm
                    
                    if new_perm in forward:
                        fwd_circuit = forward[new_perm]
                        bwd_circuit = current_circuit.copy()
                        bwd_circuit.prepend(gate)
                        return fwd_circuit.concatenate(bwd_circuit.inverse())
                    
                    if new_perm not in backward:
                        new_circuit = current_circuit.copy()
                        new_circuit.prepend(gate)
                        backward[new_perm] = new_circuit
                        next_backward.append(new_perm)
            
            backward_queue = next_backward
        
        return None
    
    def enumerate_all(self, max_depth: int) -> Dict[Permutation, Circuit]:
        """
        Enumerate all reachable permutations up to max_depth.
        Returns dict mapping permutation -> shortest circuit.
        """
        identity = Permutation.identity(self.n_bits)
        results: Dict[Permutation, Circuit] = {identity: Circuit.empty(self.n_bits)}
        
        queue = deque([identity])
        
        while queue:
            current = queue.popleft()
            current_circuit = results[current]
            
            if len(current_circuit) >= max_depth:
                continue
            
            for gate, gate_perm in self.gate_perms:
                new_perm = current * gate_perm
                
                if new_perm not in results:
                    new_circuit = current_circuit.copy()
                    new_circuit.prepend(gate)
                    results[new_perm] = new_circuit
                    queue.append(new_perm)
        
        return results


class MeetInTheMiddleSynthesizer:
    """
    Meet-in-the-middle synthesis.
    Precomputes forward table for efficient reuse.
    """
    
    def __init__(self, n_bits: int, half_depth: int = 4, allow_same_line: bool = False):
        """
        Args:
            n_bits: Number of bits
            half_depth: Depth to precompute (total search depth = 2 * half_depth)
            allow_same_line: Allow gates with shared control/target lines
        """
        self.n_bits = n_bits
        self.half_depth = half_depth
        
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
        self.gate_perms = [(g, g.to_permutation()) for g in self.gates]
        
        # Precompute forward table
        self._forward_table: Optional[Dict[Permutation, Circuit]] = None
    
    def _build_forward_table(self) -> Dict[Permutation, Circuit]:
        """Build table of all permutations reachable in half_depth steps."""
        if self._forward_table is not None:
            return self._forward_table
        
        identity = Permutation.identity(self.n_bits)
        table: Dict[Permutation, Circuit] = {identity: Circuit.empty(self.n_bits)}
        
        queue = deque([identity])
        
        while queue:
            current = queue.popleft()
            current_circuit = table[current]
            
            if len(current_circuit) >= self.half_depth:
                continue
            
            for gate, gate_perm in self.gate_perms:
                new_perm = current * gate_perm
                
                if new_perm not in table:
                    new_circuit = current_circuit.copy()
                    new_circuit.prepend(gate)
                    table[new_perm] = new_circuit
                    queue.append(new_perm)
        
        self._forward_table = table
        return table
    
    def synthesize(self, target: Permutation) -> Optional[Circuit]:
        """
        Synthesize using meet-in-the-middle.
        Searches up to 2 * half_depth.
        """
        if target.n_bits != self.n_bits:
            raise ValueError("Target permutation has wrong number of bits")
        
        forward_table = self._build_forward_table()
        
        # Check if target is directly in forward table
        if target in forward_table:
            return forward_table[target]
        
        # Search backward from target
        backward: Dict[Permutation, Circuit] = {target: Circuit.empty(self.n_bits)}
        queue = deque([target])
        
        while queue:
            current = queue.popleft()
            current_circuit = backward[current]
            
            if len(current_circuit) >= self.half_depth:
                continue
            
            for gate, gate_perm in self.gate_perms:
                new_perm = current * gate_perm
                
                # Check for meeting point
                if new_perm in forward_table:
                    fwd_circuit = forward_table[new_perm]
                    bwd_circuit = current_circuit.copy()
                    bwd_circuit.prepend(gate)
                    return fwd_circuit.concatenate(bwd_circuit.inverse())
                
                if new_perm not in backward:
                    new_circuit = current_circuit.copy()
                    new_circuit.prepend(gate)
                    backward[new_perm] = new_circuit
                    queue.append(new_perm)
        
        return None
    
    @property
    def table_size(self) -> int:
        """Number of permutations in forward table."""
        if self._forward_table is None:
            self._build_forward_table()
        return len(self._forward_table)
