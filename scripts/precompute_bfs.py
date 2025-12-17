#!/usr/bin/env python3
"""
Pre-compute and cache BFS tables for fast identity generation.

Usage:
    python precompute_bfs.py --width 3 --max-depth 6
    python precompute_bfs.py --width 4 --max-depth 8
    
The BFS table maps each reachable permutation to its shortest circuit.
This is cached to disk so multiple generation jobs can share it.
"""

import argparse
import os
import sys
import time
import pickle
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(script_dir.parent))

from reversible_synth.synthesis_exact import ExactSynthesizer
from reversible_synth.permutation import Permutation


def get_cache_path(width: int, max_depth: int, cache_dir: str = "cache") -> Path:
    """Get the path for a cached BFS table."""
    return Path(cache_dir) / f"bfs_width{width}_depth{max_depth}.pkl"


def precompute_bfs_table(width: int, max_depth: int, verbose: bool = True) -> dict:
    """
    Pre-compute BFS table mapping permutations to shortest circuits.
    
    Args:
        width: Number of bits/wires
        max_depth: Maximum circuit depth to enumerate
        verbose: Print progress information
    
    Returns:
        Dict mapping Permutation -> Circuit
    """
    if verbose:
        print(f"Pre-computing BFS table for width={width}, max_depth={max_depth}")
        print(f"  State space size: {1 << width}")
    
    synth = ExactSynthesizer(width)
    
    start = time.time()
    table = synth.enumerate_all(max_depth=max_depth)
    elapsed = time.time() - start
    
    if verbose:
        print(f"  Enumerated {len(table)} permutations in {elapsed:.2f}s")
        print(f"  Coverage: {len(table)}/{(1 << width)**2 - 1} possible permutations")
    
    return table


def save_bfs_table(table: dict, cache_path: Path, verbose: bool = True):
    """Save BFS table to disk."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to serializable format
    # Circuits need to be converted to dict representation
    serializable = {}
    for perm, circuit in table.items():
        perm_key = tuple(perm._map)
        circuit_data = {
            'n_bits': circuit.n_bits,
            'gates': [(g.target, g.control1, g.control2) for g in circuit.gates]
        }
        serializable[perm_key] = circuit_data
    
    with open(cache_path, 'wb') as f:
        pickle.dump({
            'version': 1,
            'width': list(table.values())[0].n_bits if table else 0,
            'count': len(table),
            'data': serializable
        }, f)
    
    size_mb = cache_path.stat().st_size / (1024 * 1024)
    if verbose:
        print(f"  Saved to {cache_path} ({size_mb:.2f} MB)")


def load_bfs_table(cache_path: Path, verbose: bool = True) -> dict:
    """Load BFS table from disk."""
    from reversible_synth.gates import CustomGate, Circuit
    
    with open(cache_path, 'rb') as f:
        data = pickle.load(f)
    
    if verbose:
        print(f"Loading BFS table from {cache_path}")
        print(f"  Contains {data['count']} permutations")
    
    # Reconstruct table
    table = {}
    width = data['width']
    for perm_tuple, circuit_data in data['data'].items():
        perm = Permutation(width, list(perm_tuple))
        gates = [CustomGate(t, c1, c2, width) for t, c1, c2 in circuit_data['gates']]
        circuit = Circuit(width, gates)
        table[perm] = circuit
    
    return table


def main():
    parser = argparse.ArgumentParser(description="Pre-compute BFS tables")
    parser.add_argument("--width", "-w", type=int, required=True,
                        help="Circuit width")
    parser.add_argument("--max-depth", "-d", type=int, default=6,
                        help="Maximum depth to enumerate")
    parser.add_argument("--cache-dir", type=str, default="cache",
                        help="Directory for cache files")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Recompute even if cache exists")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress output")
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    cache_path = get_cache_path(args.width, args.max_depth, args.cache_dir)
    
    if cache_path.exists() and not args.force:
        if verbose:
            print(f"Cache already exists: {cache_path}")
            print("Use --force to recompute")
        return 0
    
    # Compute and save
    table = precompute_bfs_table(args.width, args.max_depth, verbose)
    save_bfs_table(table, cache_path, verbose)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
