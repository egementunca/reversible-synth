#!/bin/bash
#$ -N bfs_precompute
#$ -cwd
#$ -j y
#$ -o logs/$JOB_NAME.$JOB_ID.log
#$ -l h_rt=24:00:00
#$ -l mem_per_core=16G

# BFS Table Pre-computation - Cluster Job
#
# Usage:
#   qsub -v WIDTH=5,MAX_DEPTH=8 precompute_bfs_job.sh
#
# Parameters:
#   WIDTH     - Circuit width (required)
#   MAX_DEPTH - Maximum depth to enumerate (default: 8)

if [ -z "$WIDTH" ]; then
    echo "ERROR: WIDTH not specified"
    exit 1
fi

MAX_DEPTH=${MAX_DEPTH:-8}

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

mkdir -p "${PROJECT_DIR}/cache"
mkdir -p "${PROJECT_DIR}/logs"

echo "=== BFS Pre-computation Job ==="
echo "Width:     $WIDTH"
echo "Max Depth: $MAX_DEPTH"
echo ""

# Activate virtual environment if it exists
if [ -f "${PROJECT_DIR}/venv/bin/activate" ]; then
    source "${PROJECT_DIR}/venv/bin/activate"
fi

cd "$PROJECT_DIR"

python3 scripts/precompute_bfs.py --width "$WIDTH" --max-depth "$MAX_DEPTH"

EXIT_CODE=$?

echo ""
echo "=== Job Complete ==="
echo "Exit code: $EXIT_CODE"

exit $EXIT_CODE
