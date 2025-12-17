# Cluster Execution Guide

All commands are submitted as jobs (no direct Python execution on login node).

## Step 1: Clone Repository

```bash
cd /path/to/your/work/directory
git clone <your-repo-url>
cd reversible-synth
mkdir -p logs
```

## Step 2: Setup Environment (FIRST JOB)

```bash
qsub scripts/setup_env.sh
```

Wait for this to complete before proceeding. Check: `cat logs/setup.*.log`

## Step 3: Pre-compute BFS Tables

```bash
# Width 3-4 (fast)
qsub -v WIDTH=3,MAX_DEPTH=8 scripts/precompute_bfs_job.sh
qsub -v WIDTH=4,MAX_DEPTH=8 scripts/precompute_bfs_job.sh

# Width 5-8 (slower, larger memory)
qsub -v WIDTH=5,MAX_DEPTH=8 scripts/precompute_bfs_job.sh
qsub -v WIDTH=6,MAX_DEPTH=8 scripts/precompute_bfs_job.sh
qsub -v WIDTH=7,MAX_DEPTH=8 scripts/precompute_bfs_job.sh
qsub -v WIDTH=8,MAX_DEPTH=8 scripts/precompute_bfs_job.sh
```

Wait for BFS jobs to finish before generating templates.

## Step 4: Generate Templates

```bash
# Width 3 (fast)
qsub -v WIDTH=3,LENGTH=6,COUNT=10000 scripts/run_identity.sh
qsub -v WIDTH=3,LENGTH=8,COUNT=10000 scripts/run_identity.sh
qsub -v WIDTH=3,LENGTH=10,COUNT=10000 scripts/run_identity.sh

# Width 4
qsub -v WIDTH=4,LENGTH=6,COUNT=5000 scripts/run_identity.sh
qsub -v WIDTH=4,LENGTH=8,COUNT=5000 scripts/run_identity.sh

# Width 5
qsub -v WIDTH=5,LENGTH=8,COUNT=1000 scripts/run_identity.sh

# Width 6-8
qsub -v WIDTH=6,LENGTH=8,COUNT=500 scripts/run_identity.sh
qsub -v WIDTH=7,LENGTH=8,COUNT=100 scripts/run_identity.sh
qsub -v WIDTH=8,LENGTH=8,COUNT=50 scripts/run_identity.sh
```

## Step 5: Check Results

```bash
# Check job logs
cat logs/identity_gen.*.log

# Database is at: data/templates.db
```

## Quick Reference

| Width | BFS Time | Gen Rate | Count |
|-------|----------|----------|-------|
| 3 | <1min | 1000/s | 10000 |
| 4 | ~5min | 50/s | 5000 |
| 5 | ~1hr | 10/s | 1000 |
| 6 | ~4hr | 1/s | 500 |
| 7 | ~12hr | 0.1/s | 100 |
| 8 | ~24hr | slow | 50 |
