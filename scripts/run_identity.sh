#!/bin/bash
#$ -N identity_gen
#$ -cwd
#$ -j y
#$ -o logs/$JOB_NAME.$JOB_ID.log
#$ -l h_rt=4:00:00
#$ -l mem_per_core=4G

# Non-Trivial Identity Circuit Generator - Cluster Submission Script
# 
# Usage (SGE/qsub):
#   qsub -v WIDTH=3,COUNT=1000,LENGTH=6 run_identity.sh
#   qsub -v WIDTH=5,COUNT=100,LENGTH=10,USE_DB=1,USE_CACHE=1 run_identity.sh
#
# Parameters (via environment variables):
#   WIDTH     - Circuit width (default: 3)
#   COUNT     - Number of circuits to generate (default: 100)
#   LENGTH    - Target circuit length (default: 6)
#   DEPTH     - Alias for LENGTH
#   USE_DB    - Store in database (1=yes, default: 1)
#   USE_CACHE - Use BFS cache (1=yes, default: 1)

# Defaults
WIDTH=${WIDTH:-3}
COUNT=${COUNT:-100}
LENGTH=${LENGTH:-${DEPTH:-6}}
USE_DB=${USE_DB:-1}
USE_CACHE=${USE_CACHE:-1}

# Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create output directories
mkdir -p "${PROJECT_DIR}/results"
mkdir -p "${PROJECT_DIR}/logs"
mkdir -p "${PROJECT_DIR}/cache"
mkdir -p "${PROJECT_DIR}/data"

# Job ID for output naming
if [ -n "$JOB_ID" ]; then
    JOB_TAG="$JOB_ID"
elif [ -n "$PBS_JOBID" ]; then
    JOB_TAG="$PBS_JOBID"
else
    JOB_TAG="$$"
fi

echo "=== Identity Generator Cluster Job ==="
echo "Width:     $WIDTH"
echo "Count:     $COUNT"
echo "Length:    $LENGTH"
echo "Use DB:    $USE_DB"
echo "Use Cache: $USE_CACHE"
echo "Job ID:    $JOB_TAG"
echo ""

# Load Python module (adjust for your cluster)
module load python3 2>/dev/null || module load python/3.9 2>/dev/null || true

# Activate virtual environment if it exists
if [ -f "${PROJECT_DIR}/venv/bin/activate" ]; then
    source "${PROJECT_DIR}/venv/bin/activate"
fi

# Export for Python script
export WIDTH COUNT LENGTH USE_DB USE_CACHE
export JOB_ID="$JOB_TAG"

# Run the generator
cd "$PROJECT_DIR"

# Build command
CMD="python3 scripts/generate_identities.py --width $WIDTH --count $COUNT --length $LENGTH --verbose --verify"

if [ "$USE_DB" = "1" ]; then
    CMD="$CMD --db"
else
    OUTPUT="${PROJECT_DIR}/results/identities_W${WIDTH}_L${LENGTH}_${JOB_TAG}.json"
    CMD="$CMD --output $OUTPUT"
fi

if [ "$USE_CACHE" = "1" ]; then
    CMD="$CMD --use-cache"
fi

echo "Running: $CMD"
echo ""

eval $CMD

EXIT_CODE=$?

echo ""
echo "=== Job Complete ==="
echo "Exit code: $EXIT_CODE"

exit $EXIT_CODE
