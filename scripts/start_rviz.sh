#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
NAME=${SCAN_CONTAINER:-scan-sim2real-noetic}
if [ -z "${DISPLAY:-}" ]; then echo 'Set DISPLAY from the NEW server desktop (or use SSH X forwarding; see docs). No fixed :20 assumption.' >&2; exit 2; fi
bash "$ROOT/scripts/container.sh" start
if ! docker exec "$NAME" bash -c 'source /work/scripts/ros_env.sh; rosnode list >/dev/null 2>&1'; then
  docker exec -d "$NAME" bash -c 'source /work/scripts/ros_env.sh; exec roscore -p 11321 > /work/logs/roscore.log 2>&1'
fi
for ATTEMPT in $(seq 1 30); do
  if docker exec "$NAME" bash -c 'source /work/scripts/ros_env.sh; rosnode list >/dev/null 2>&1'; then break; fi
  sleep 1
done
docker exec "$NAME" bash -c 'source /work/scripts/ros_env.sh; rosnode list >/dev/null'
if docker exec "$NAME" pgrep -x rviz >/dev/null; then echo 'RViz process already exists; inspect the desktop and logs.'; exit 0; fi
docker exec -d "$NAME" bash -c 'source /work/scripts/ros_env.sh; exec rviz -d /work/configs/calibration.rviz > /work/logs/rviz.log 2>&1'
echo 'RViz requested. Check rosnode list, logs/rviz.log AND the rendered desktop; request success is not rendering verification.'
