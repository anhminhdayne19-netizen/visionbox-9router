#!/usr/bin/env bash
cd "$(dirname "$0")"
PORT=8080

while ss -tuln | grep -q ":$PORT "; do
  PORT=$((PORT + 1))
done

echo "=================================================="
echo "  VisionBox (tích hợp 9Router) đang chạy tại:    "
echo "  http://localhost:$PORT                          "
echo "=================================================="

if which xdg-open > /dev/null 2>&1; then
  (sleep 1 && xdg-open "http://localhost:$PORT") &
fi

python3 -m http.server "$PORT"
