#!/usr/bin/env bash
# Fetch the reference repos (git submodules) for code-driven animation/video into repos/.
# Usage: bash scripts/clone_repos.sh   (safe to re-run)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1 — $2" >&2; exit 1; }; }
need git "install with: sudo apt-get install -y git"
need ffmpeg "install with: sudo apt-get install -y ffmpeg"
need node "install Node.js 22+ (https://nodejs.org or nvm install 22)"
node_major="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$node_major" -lt 22 ]; then
  echo "Node.js 22+ required (found $(node --version))" >&2
  exit 1
fi

cd "$ROOT"
# The repos are git submodules (see .gitmodules); fetch only the pinned commit.
# HyperFrames keeps heavy test videos in Git LFS; skip downloading them.
GIT_LFS_SKIP_SMUDGE=1 git submodule update --init --depth 1 -- repos
git submodule status -- repos
