#!/usr/bin/env python3
"""
Cluster-compatible script for generating non-trivial identity circuits.

Usage:
    # Direct run with JSON output
    python generate_identities.py --width 3 --count 100 --length 6 --output results.json
    
    # Run with database storage
    python generate_identities.py --width 3 --count 100 --length 6 --db
    
    # Use cached BFS table (much faster for width 5+)
    python generate_identities.py --width 5 --count 100 --length 8 --db --use-cache

For qsub submission:
    qsub -N identity_gen -v WIDTH=3,COUNT=100,LENGTH=6 scripts/run_identity.sh
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent.absolute()
project_dir = script_dir.parent
sys.path.insert(0, str(project_dir))

from reversible_synth.identity_synthesis import (
    NonTrivialIdentityGenerator,
    draw_circuit,
    verify_identity,
)
from reversible_synth.gates import Circuit


def circuit_to_dict(circuit: Circuit, gen: NonTrivialIdentityGenerator) -> dict:
    """Convert a circuit to a JSON-serializable dictionary."""
    return {
        "n_bits": circuit.n_bits,
        "length": len(circuit),
        "gates": [
            {"target": g.target, "control1": g.control1, "control2": g.control2}
            for g in circuit.gates
        ],
        "is_identity": circuit.to_permutation().is_identity(),
        "hardness_score": gen.hardness_score(circuit),
        "is_trivial": gen.is_trivial(circuit),
    }


def load_bfs_cache(width: int, max_depth: int) -> dict:
    """Load cached BFS table if available."""
    from scripts.precompute_bfs import get_cache_path, load_bfs_table
    
    cache_path = get_cache_path(width, max_depth, str(project_dir / "cache"))
    
    if not cache_path.exists():
        # Try to find any matching cache
        cache_dir = project_dir / "cache"
        for f in cache_dir.glob(f"bfs_width{width}_depth*.pkl"):
            return load_bfs_table(f, verbose=True)
        return None
    
    return load_bfs_table(cache_path, verbose=True)


def generate_with_cache(gen: NonTrivialIdentityGenerator, 
                        bfs_table: dict,
                        target_length: int,
                        max_attempts: int = 500) -> Circuit:
    """Generate identity using pre-computed BFS table."""
    import random
    
    half_depth = max(2, target_length // 2)
    
    for _ in range(max_attempts):
        # Build random first half
        c1 = gen._build_random_half(half_depth)
        if c1 is None:
            continue
        
        # Lookup inverse
        perm = c1.to_permutation()
        inv_perm = perm.inverse()
        
        if inv_perm not in bfs_table:
            continue
        
        c2 = bfs_table[inv_perm]
        
        # Check junction
        if len(c1) > 0 and len(c2) > 0:
            if c1.gates[-1] == c2.gates[0]:
                continue
        
        # Combine and verify
        full = c1.concatenate(c2)
        
        if full.to_permutation().is_identity() and not gen.is_trivial(full):
            return full
    
    return None


def main():
    # Check for environment variables (for qsub)
    width = int(os.environ.get("WIDTH", 3))
    count = int(os.environ.get("COUNT", 100))
    length = int(os.environ.get("LENGTH", os.environ.get("DEPTH", 6)))
    output = os.environ.get("OUTPUT", None)
    job_id = os.environ.get("PBS_JOBID", os.environ.get("JOB_ID", "local"))
    use_db = os.environ.get("USE_DB", "0") == "1"
    use_cache = os.environ.get("USE_CACHE", "0") == "1"
    
    # Command-line arguments override environment
    parser = argparse.ArgumentParser(description="Generate non-trivial identity circuits")
    parser.add_argument("--width", "-w", type=int, default=width,
                        help="Circuit width (number of wires)")
    parser.add_argument("--count", "-c", type=int, default=count,
                        help="Number of circuits to generate")
    parser.add_argument("--length", "-l", type=int, default=length,
                        help="Target circuit length")
    parser.add_argument("--output", "-o", type=str, default=output,
                        help="Output JSON file")
    parser.add_argument("--db", action="store_true", default=use_db,
                        help="Store in SQLite database instead of JSON")
    parser.add_argument("--use-cache", action="store_true", default=use_cache,
                        help="Use pre-computed BFS table")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print progress information")
    parser.add_argument("--verify", action="store_true", default=True,
                        help="Double-check all circuits are identities")
    
    args = parser.parse_args()
    
    # Set output filename if not specified and not using DB
    if args.output is None and not args.db:
        args.output = f"identities_W{args.width}_L{args.length}_{job_id}.json"
    
    if args.verbose:
        print(f"=== Non-Trivial Identity Generator ===")
        print(f"Width:     {args.width}")
        print(f"Count:     {args.count}")
        print(f"Length:    {args.length}")
        print(f"Output:    {args.output or 'database'}")
        print(f"Use cache: {args.use_cache}")
        print(f"Job ID:    {job_id}")
        print()
    
    # Initialize generator
    gen = NonTrivialIdentityGenerator(args.width)
    
    # Load BFS cache if requested
    bfs_table = None
    if args.use_cache:
        bfs_table = load_bfs_cache(args.width, args.length // 2 + 2)
        if bfs_table and args.verbose:
            print(f"Using cached BFS table with {len(bfs_table)} entries")
    
    # Initialize database if needed
    db = None
    if args.db:
        from scripts.template_database import TemplateDatabase
        db = TemplateDatabase()
        if args.verbose:
            print(f"Using database: {db.db_path}")
    
    # Generate circuits
    start_time = time.time()
    templates = []
    failed = 0
    duplicates = 0
    
    for i in range(args.count):
        # Generate using cache or standard method
        if bfs_table:
            circuit = generate_with_cache(gen, bfs_table, args.length, max_attempts=1000)
        else:
            circuit = gen.generate_fast(target_length=args.length, max_attempts=500)
            if circuit is None:
                circuit = gen.generate(half_length=args.length // 2, max_attempts=100)
        
        if circuit is not None:
            # Verify
            if args.verify:
                is_id = verify_identity(circuit, verbose=False)
                if not is_id:
                    if args.verbose:
                        print(f"  WARNING: Circuit {i} is NOT identity! Skipping.")
                    failed += 1
                    continue
            
            score = gen.hardness_score(circuit)
            
            # Store
            if args.db:
                success, _ = db.add_template(circuit, score, job_id)
                if not success:
                    duplicates += 1
                    continue
            else:
                templates.append(circuit_to_dict(circuit, gen))
            
            if args.verbose and (i + 1) % max(1, args.count // 10) == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"  Generated {i + 1}/{args.count} ({rate:.1f}/s)")
        else:
            failed += 1
            if args.verbose and failed <= 5:
                print(f"  Failed to generate circuit {i}")
    
    end_time = time.time()
    
    # Summary
    generated = args.count - failed - duplicates
    
    if not args.db:
        results = {
            "metadata": {
                "width": args.width,
                "target_length": args.length,
                "requested_count": args.count,
                "generated_count": len(templates),
                "failed_count": failed,
                "generation_time_seconds": end_time - start_time,
                "job_id": job_id,
            },
            "circuits": templates
        }
        
        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
    
    if args.verbose:
        print()
        print(f"=== Summary ===")
        print(f"Generated:  {generated}")
        print(f"Duplicates: {duplicates}")
        print(f"Failed:     {failed}")
        print(f"Time:       {end_time - start_time:.2f}s")
        if generated > 0:
            print(f"Rate:       {generated / (end_time - start_time):.1f} circuits/s")
        if args.db:
            print(f"Database:   {db.db_path}")
            stats = db.get_stats()
            print(f"Total in DB: {stats['total_templates']}")
        else:
            print(f"Output:     {args.output}")
    
    # Return exit code based on success
    if generated < args.count * 0.5:
        sys.exit(1)  # Less than 50% success rate
    sys.exit(0)


if __name__ == "__main__":
    main()
