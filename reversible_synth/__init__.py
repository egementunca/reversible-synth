"""
Reversible Circuit Synthesizer for Custom Universal Gate
Gate: Target XOR (Control1 OR NOT Control2)
"""

__version__ = "0.1.0"
__all__ = [
    'Permutation', 'CustomGate', 'Circuit', 
    'ExactSynthesizer', 'TransformationSynthesizer', 
    'IdentityGenerator', 'NonTrivialIdentityGenerator'
]

from .permutation import Permutation
from .gates import CustomGate, Circuit
from .synthesis_exact import ExactSynthesizer
from .synthesis_heuristic import TransformationSynthesizer
from .identity_generator import IdentityGenerator
from .identity_synthesis import NonTrivialIdentityGenerator