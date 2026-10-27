# Source this file in each new shell: source scripts/activate.sh
ANLIFE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ANLIFE_ROOT/.venv/bin/activate"
export SK="$ANLIFE_ROOT/.agents/skills/anlife"
export HF_HOME="$ANLIFE_ROOT/.cache/huggingface"
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
