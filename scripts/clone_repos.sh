#!/usr/bin/env bash
# Clone reference repos for code-driven animation/video into repos/.
# Usage: bash scripts/clone_repos.sh   (re-running skips repos already present)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/repos"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1 — $2" >&2; exit 1; }; }
need git "install with: sudo apt-get install -y git"
need ffmpeg "install with: sudo apt-get install -y ffmpeg"
need node "install Node.js 22+ (https://nodejs.org or nvm install 22)"
node_major="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$node_major" -lt 22 ]; then
  echo "Node.js 22+ required (found $(node --version))" >&2
  exit 1
fi

REPOS=(
  JohnHeibel/PDoomVideo
  JohnHeibel/ClaudeAnimationBase
  buildwithhanif/claude-animation-skill
  heygen-com/hyperframes
  WinterArc21/Battle-of-Austerlitz-Film
  guanmo-ai/awesome-ai-motion
  athemeroy/awesome-opus-5-5-videos
)

mkdir -p "$DEST"
for slug in "${REPOS[@]}"; do
  name="${slug#*/}"
  if [ -d "$DEST/$name/.git" ]; then
    echo "skip  $name (already cloned)"
    continue
  fi
  # HyperFrames keeps heavy test videos in Git LFS; skip downloading them.
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 "https://github.com/$slug.git" "$DEST/$name"
  echo "done  $name"
done
