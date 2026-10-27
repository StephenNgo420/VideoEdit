#!/bin/bash
# Chạy lệnh dài ở nền (tool call bị giới hạn ~300s). Dùng: bash run_bg.sh <logfile> <lệnh...>
# Theo dõi: tail -3 <logfile>   (dòng 'DONE' = xong)
LOG="$1"; shift
setsid nohup "$@" > "$LOG" 2>&1 < /dev/null &
echo "started pid=$! log=$LOG"
