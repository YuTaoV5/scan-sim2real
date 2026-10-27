#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
NAME=${SCAN_CONTAINER:-scan-sim2real-noetic}
case "${1:-start}" in
  start)
    if docker container inspect "$NAME" >/dev/null 2>&1; then
      if [ "$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/work"}}{{.Source}}{{end}}{{end}}' "$NAME")" != "$ROOT" ]; then
        echo 'Existing container mounts another checkout. Choose SCAN_CONTAINER or inspect it manually.' >&2; exit 2
      fi
      docker start "$NAME"; exit 0
    fi
    mkdir -p "$ROOT/data" "$ROOT/generated" "$ROOT/logs" "$ROOT/workspaces"
    EXTRA=()
    if [ -n "${DISPLAY:-}" ] && [ -d /tmp/.X11-unix ]; then
      EXTRA+=(-e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix:ro)
      AUTH=${XAUTHORITY:-"$HOME/.Xauthority"}
      if [ -f "$AUTH" ]; then EXTRA+=(-v "$AUTH:/tmp/host.xauthority:ro" -e XAUTHORITY=/tmp/host.xauthority); fi
    fi
    docker run -d --name "$NAME" --network=host \
      -e ROS_MASTER_URI=http://127.0.0.1:11321 -e ROS_IP=127.0.0.1 \
      -e QT_X11_NO_MITSHM=1 -e LIBGL_ALWAYS_SOFTWARE=1 \
      "${EXTRA[@]}" -v "$ROOT:/work" scan-sim2real:noetic sleep infinity
    ;;
  shell) exec docker exec -it "$NAME" bash ;;
  stop) docker stop "$NAME" ;;
  *) echo 'Usage: container.sh [start|shell|stop]' >&2; exit 2 ;;
esac
