"""
Heuristic synthesis algorithms: Transformation-based, Output Permutation, Genetic.
"""

from typing import List, Optional, Tuple, Callable
import random
from .permutation import Permutation
from .gates import CustomGate, Circuit


class TransformationSynthesizer:
    """
    Greedy transformation-based synthesis.
    Tries to reduce distance to target at each step.
    """
    
    def __init__(self, n_bits: int, allow_same_line: bool = False):
        self.n_bits = n_bits
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
        self.gate_perms = [(g, g.to_permutation()) for g in self.gates]
    
    def _distance(self, perm: Permutation, target: Permutation) -> int:
        """Count positions where permutations differ."""
        return perm.distance_to(target)
    
    def synthesize(self, target: Permutation, max_steps: int = 1000) -> Optional[Circuit]:
        """
        Greedy synthesis: at each step, pick gate that most reduces distance.
        """
        if target.n_bits != self.n_bits:
            raise ValueError("Target permutation has wrong number of bits")
        
        identity = Permutation.identity(self.n_bits)
        
        if target == identity:
            return Circuit.empty(self.n_bits)
        
        current = identity
        circuit = Circuit.empty(self.n_bits)
        
        for _ in range(max_steps):
            current_dist = self._distance(current, target)
            
            if current_dist == 0:
                return circuit
            
            best_gate = None
            best_perm = None
            best_dist = current_dist
            
            for gate, gate_perm in self.gate_perms:
                new_perm = gate_perm * current
                new_dist = self._distance(new_perm, target)
                
                if new_dist < best_dist:
                    best_dist = new_dist
                    best_gate = gate
                    best_perm = new_perm
            
            if best_gate is None:
                # Stuck - try random gate to escape
                gate, gate_perm = random.choice(self.gate_perms)
                circuit.prepend(gate)
                current = gate_perm * current
            else:
                circuit.prepend(best_gate)
                current = best_perm
        
        return circuit if current == target else None
    
    def synthesize_multistart(self, target: Permutation, restarts: int = 10, 
                               max_steps: int = 500) -> Optional[Circuit]:
        """
        Multi-start greedy with randomization.
        Returns shortest circuit found.
        """
        best_circuit = None
        
        for _ in range(restarts):
            circuit = self._synthesize_randomized(target, max_steps)
            if circuit is not None:
                if best_circuit is None or len(circuit) < len(best_circuit):
                    best_circuit = circuit
        
        return best_circuit
    
    def _synthesize_randomized(self, target: Permutation, max_steps: int) -> Optional[Circuit]:
        """Greedy with random tie-breaking and occasional random moves."""
        identity = Permutation.identity(self.n_bits)
        
        if target == identity:
            return Circuit.empty(self.n_bits)
        
        current = identity
        circuit = Circuit.empty(self.n_bits)
        
        for _ in range(max_steps):
            if current == target:
                return circuit
            
            current_dist = self._distance(current, target)
            
            # Find all improving moves
            improving = []
            for gate, gate_perm in self.gate_perms:
                new_perm = gate_perm * current
                new_dist = self._distance(new_perm, target)
                if new_dist < current_dist:
                    improving.append((gate, gate_perm, new_dist))
            
            if improving:
                # Pick randomly among best improvements
                min_dist = min(x[2] for x in improving)
                best = [x for x in improving if x[2] == min_dist]
                gate, gate_perm, _ = random.choice(best)
            else:
                # Random move to escape local minimum
                gate, gate_perm = random.choice(self.gate_perms)
            
            circuit.prepend(gate)
            current = gate_perm * current
        
        return circuit if current == target else None


class OutputPermutationSynthesizer:
    """
    Fix outputs one at a time.
    Tries to make output i correct without disturbing already-fixed outputs.
    """
    
    def __init__(self, n_bits: int, allow_same_line: bool = False):
        self.n_bits = n_bits
        self.size = 1 << n_bits
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
        self.gate_perms = [(g, g.to_permutation()) for g in self.gates]
    
    def synthesize(self, target: Permutation, max_steps_per_output: int = 100) -> Optional[Circuit]:
        """
        Fix each output position in order.
        """
        if target.n_bits != self.n_bits:
            raise ValueError("Target permutation has wrong number of bits")
        
        current = Permutation.identity(self.n_bits)
        circuit = Circuit.empty(self.n_bits)
        
        for pos in range(self.size):
            # Try to make current(pos) == target(pos) without changing 0..pos-1
            steps = 0
            while current(pos) != target(pos) and steps < max_steps_per_output:
                best_gate = None
                best_perm = None
                best_score = -1
                
                for gate, gate_perm in self.gate_perms:
                    new_perm = gate_perm * current
                    
                    # Check we don't break already-fixed positions
                    breaks_fixed = False
                    for i in range(pos):
                        if new_perm(i) != target(i):
                            breaks_fixed = True
                            break
                    
                    if breaks_fixed:
                        continue
                    
                    # Score: does it fix position pos?
                    score = 1 if new_perm(pos) == target(pos) else 0
                    
                    if score > best_score:
                        best_score = score
                        best_gate = gate
                        best_perm = new_perm
                
                if best_gate is None:
                    # No gate found that doesn't break things
                    return None
                
                circuit.prepend(best_gate)
                current = best_perm
                steps += 1
        
        return circuit if current == target else None


class GeneticSynthesizer:
    """
    Genetic algorithm for circuit synthesis.
    """
    
    def __init__(self, n_bits: int, allow_same_line: bool = False):
        self.n_bits = n_bits
        if allow_same_line:
            self.gates = CustomGate.all_gates(n_bits, allow_same_line=True)
        else:
            self.gates = CustomGate.distinct_gates(n_bits)
    
    def _random_circuit(self, length: int) -> Circuit:
        """Generate random circuit of given length."""
        circuit = Circuit.empty(self.n_bits)
        for _ in range(length):
            gate = random.choice(self.gates)
            circuit.append(gate)
        return circuit
    
    def _fitness(self, circuit: Circuit, target: Permutation) -> float:
        """
        Fitness function: higher is better.
        Based on distance to target and circuit length.
        """
        perm = circuit.to_permutation()
        distance = perm.distance_to(target)
        
        if distance == 0:
            # Found solution! Reward shorter circuits
            return 10000 - len(circuit)
        
        # Penalize distance, slightly penalize length
        return -distance - 0.01 * len(circuit)
    
    def _crossover(self, parent1: Circuit, parent2: Circuit) -> Circuit:
        """Single-point crossover."""
        if len(parent1) == 0:
            return parent2.copy()
        if len(parent2) == 0:
            return parent1.copy()
        
        point1 = random.randint(0, len(parent1))
        point2 = random.randint(0, len(parent2))
        
        new_gates = parent1.gates[:point1] + parent2.gates[point2:]
        return Circuit(self.n_bits, new_gates)
    
    def _mutate(self, circuit: Circuit, mutation_rate: float = 0.1) -> Circuit:
        """Mutate circuit: insert, delete, or change gates."""
        gates = circuit.gates.copy()
        
        for i in range(len(gates)):
            if random.random() < mutation_rate:
                gates[i] = random.choice(self.gates)
        
        # Possibly insert
        if random.random() < mutation_rate:
            pos = random.randint(0, len(gates))
            gates.insert(pos, random.choice(self.gates))
        
        # Possibly delete
        if len(gates) > 1 and random.random() < mutation_rate:
            pos = random.randint(0, len(gates) - 1)
            gates.pop(pos)
        
        return Circuit(self.n_bits, gates)
    
    def _tournament_select(self, population: List[Tuple[Circuit, float]], 
                           tournament_size: int = 3) -> Circuit:
        """Tournament selection."""
        contestants = random.sample(population, min(tournament_size, len(population)))
        winner = max(contestants, key=lambda x: x[1])
        return winner[0]
    
    def synthesize(self, target: Permutation, 
                   population_size: int = 100,
                   generations: int = 500,
                   initial_length: int = 10,
                   mutation_rate: float = 0.1) -> Optional[Circuit]:
        """
        Genetic algorithm synthesis.
        """
        if target.n_bits != self.n_bits:
            raise ValueError("Target permutation has wrong number of bits")
        
        # Check if identity
        if target.is_identity():
            return Circuit.empty(self.n_bits)
        
        # Initialize population
        population = []
        for _ in range(population_size):
            length = random.randint(1, initial_length * 2)
            circuit = self._random_circuit(length)
            fitness = self._fitness(circuit, target)
            population.append((circuit, fitness))
            
            if fitness >= 10000 - initial_length * 2:
                # Found solution
                return circuit
        
        # Evolution
        for gen in range(generations):
            # Sort by fitness
            population.sort(key=lambda x: x[1], reverse=True)
            
            # Check for solution
            best = population[0]
            if best[1] >= 9000:  # Found valid solution
                return best[0]
            
            # Create new generation
            new_population = []
            
            # Elitism: keep best
            new_population.append(population[0])
            
            while len(new_population) < population_size:
                parent1 = self._tournament_select(population)
                parent2 = self._tournament_select(population)
                
                child = self._crossover(parent1, parent2)
                child = self._mutate(child, mutation_rate)
                
                fitness = self._fitness(child, target)
                new_population.append((child, fitness))
                
                if fitness >= 9000:
                    return child
            
            population = new_population
        
        # Return best found
        population.sort(key=lambda x: x[1], reverse=True)
        best = population[0]
        if best[0].to_permutation() == target:
            return best[0]
        
        return None
