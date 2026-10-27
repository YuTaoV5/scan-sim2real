#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$ROOT/logs"
docker build --network=host -f "$ROOT/docker/Dockerfile" -t scan-sim2real:noetic "$ROOT" 2>&1 | tee "$ROOT/logs/docker-build.log"
docker image inspect scan-sim2real:noetic > "$ROOT/logs/docker-image-inspect.json"
