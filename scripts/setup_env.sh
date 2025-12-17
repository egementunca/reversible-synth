#!/bin/bash
#$ -N setup_env
#$ -cwd
#$ -j y
#$ -o logs/setup.$JOB_ID.log
#$ -l h_rt=1:00:00
#$ -l mem_per_core=4G

# Environment Setup Job
# Run this FIRST before any other jobs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Environment Setup Job ==="
echo "Project: $PROJECT_DIR"
echo ""

# Create directories
mkdir -p "${PROJECT_DIR}/cache"
mkdir -p "${PROJECT_DIR}/data"
mkdir -p "${PROJECT_DIR}/logs"
mkdir -p "${PROJECT_DIR}/results"

# Load Python module
module load python3 2>/dev/null || module load python/3.9 2>/dev/null || module load python 2>/dev/null

echo "Python: $(which python3)"
echo "Version: $(python3 --version)"

# Create virtual environment
cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install package
echo "Installing package..."
pip install --upgrade pip
pip install -e .

echo ""
echo "=== Setup Complete ==="
echo "Virtual environment: ${PROJECT_DIR}/venv"
