#!/usr/bin/env python3
"""
Master orchestrator for submitting identity generation jobs to cluster.

Usage:
    python submit_all_jobs.py --widths 3,4,5 --max-depth 10
    python submit_all_jobs.py --widths 6,7,8 --max-depth 8 --count-per-job 1000
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

script_dir = Path(__file__).parent.absolute()
project_dir = script_dir.parent


# Configuration for each width
WIDTH_CONFIG = {
    3: {'max_depth': 12, 'count_per_job': 10000, 'precompute_first': False},
    4: {'max_depth': 12, 'count_per_job': 5000, 'precompute_first': False},
    5: {'max_depth': 10, 'count_per_job': 1000, 'precompute_first': True},
    6: {'max_depth': 10, 'count_per_job': 500, 'precompute_first': True},
    7: {'max_depth': 8, 'count_per_job': 100, 'precompute_first': True},
    8: {'max_depth': 8, 'count_per_job': 50, 'precompute_first': True},
}


def get_min_depth(width: int) -> int:
    """Minimum depth to touch all wires."""
    return width


def get_job_script_path() -> Path:
    """Get path to the job script."""
    return script_dir / "run_identity.sh"


def get_precompute_script_path() -> Path:
    """Get path to precompute script."""
    return script_dir / "precompute_bfs.py"


def get_tracking_file() -> Path:
    """Get path to job tracking file."""
    return project_dir / "data" / "job_tracking.json"


def load_tracking() -> dict:
    """Load job tracking data."""
    path = get_tracking_file()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {'jobs': {}, 'completed': [], 'failed': []}


def save_tracking(data: dict):
    """Save job tracking data."""
    path = get_tracking_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)


def submit_qsub_job(width: int, depth: int, count: int, 
                    dry_run: bool = False) -> str:
    """Submit a single job via qsub."""
    job_script = get_job_script_path()
    
    # Create job-specific environment
    env_vars = f"WIDTH={width},DEPTH={depth},COUNT={count}"
    job_name = f"ident_w{width}_d{depth}"
    
    cmd = [
        "qsub",
        "-N", job_name,
        "-v", env_vars,
        "-o", str(project_dir / "logs" / f"{job_name}.log"),
        "-e", str(project_dir / "logs" / f"{job_name}.err"),
        str(job_script)
    ]
    
    if dry_run:
        print(f"  [DRY RUN] {' '.join(cmd)}")
        return f"dry_run_{job_name}"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        job_id = result.stdout.strip()
        print(f"  Submitted {job_name}: {job_id}")
        return job_id
    except subprocess.CalledProcessError as e:
        print(f"  ERROR submitting {job_name}: {e.stderr}")
        return None
    except FileNotFoundError:
        print("  ERROR: qsub not found. Are you on a cluster?")
        return None


def precompute_bfs_if_needed(width: int, max_depth: int, 
                              dry_run: bool = False) -> bool:
    """Pre-compute BFS table if not cached."""
    cache_path = project_dir / "cache" / f"bfs_width{width}_depth{max_depth}.pkl"
    
    if cache_path.exists():
        print(f"  BFS cache exists for width {width}")
        return True
    
    print(f"  Pre-computing BFS table for width {width}, depth {max_depth}...")
    
    if dry_run:
        print(f"  [DRY RUN] Would precompute BFS for width {width}")
        return True
    
    cmd = [
        sys.executable,
        str(get_precompute_script_path()),
        "--width", str(width),
        "--max-depth", str(max_depth)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ERROR precomputing BFS: {e}")
        return False


def generate_job_matrix(widths: list, max_depth: int = None, 
                        count_per_job: int = None) -> list:
    """Generate list of (width, depth, count) jobs to submit."""
    jobs = []
    
    for width in widths:
        config = WIDTH_CONFIG.get(width, {
            'max_depth': 8,
            'count_per_job': 100,
            'precompute_first': True
        })
        
        w_max_depth = max_depth or config['max_depth']
        w_count = count_per_job or config['count_per_job']
        min_depth = get_min_depth(width)
        
        for depth in range(min_depth, w_max_depth + 1, 2):  # Even depths only
            jobs.append((width, depth, w_count))
    
    return jobs


def main():
    parser = argparse.ArgumentParser(description="Submit identity generation jobs")
    parser.add_argument("--widths", "-w", type=str, default="3,4,5",
                        help="Comma-separated list of widths")
    parser.add_argument("--max-depth", "-d", type=int, default=None,
                        help="Maximum depth (overrides per-width defaults)")
    parser.add_argument("--count-per-job", "-c", type=int, default=None,
                        help="Templates per job (overrides defaults)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing")
    parser.add_argument("--skip-precompute", action="store_true",
                        help="Skip BFS pre-computation")
    parser.add_argument("--show-matrix", action="store_true",
                        help="Show job matrix and exit")
    
    args = parser.parse_args()
    
    widths = [int(w) for w in args.widths.split(",")]
    
    # Create directories
    (project_dir / "logs").mkdir(exist_ok=True)
    (project_dir / "cache").mkdir(exist_ok=True)
    (project_dir / "data").mkdir(exist_ok=True)
    
    print("=== Identity Template Job Orchestrator ===")
    print(f"Widths: {widths}")
    print()
    
    # Generate job matrix
    jobs = generate_job_matrix(widths, args.max_depth, args.count_per_job)
    
    if args.show_matrix:
        print("Job Matrix:")
        for w, d, c in jobs:
            print(f"  Width={w}, Depth={d}, Count={c}")
        print(f"\nTotal jobs: {len(jobs)}")
        return 0
    
    # Pre-compute BFS tables for widths that need it
    if not args.skip_precompute:
        print("Step 1: Pre-compute BFS tables")
        for width in widths:
            config = WIDTH_CONFIG.get(width, {'precompute_first': True})
            if config.get('precompute_first', True):
                max_d = args.max_depth or config.get('max_depth', 8)
                if not precompute_bfs_if_needed(width, max_d, args.dry_run):
                    print(f"  Failed to precompute for width {width}, skipping")
                    continue
        print()
    
    # Submit jobs
    print("Step 2: Submit generation jobs")
    tracking = load_tracking()
    submitted = 0
    skipped = 0
    
    for width, depth, count in jobs:
        job_key = f"w{width}_d{depth}"
        
        # Skip if already submitted/completed
        if job_key in tracking['completed']:
            print(f"  Skipping {job_key}: already completed")
            skipped += 1
            continue
        
        if job_key in tracking['jobs']:
            print(f"  Skipping {job_key}: already submitted")
            skipped += 1
            continue
        
        job_id = submit_qsub_job(width, depth, count, args.dry_run)
        
        if job_id:
            tracking['jobs'][job_key] = {
                'job_id': job_id,
                'width': width,
                'depth': depth,
                'count': count,
                'submitted_at': datetime.now().isoformat()
            }
            submitted += 1
    
    save_tracking(tracking)
    
    print()
    print(f"=== Summary ===")
    print(f"Submitted: {submitted}")
    print(f"Skipped:   {skipped}")
    print(f"Total:     {len(jobs)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
