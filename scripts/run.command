#!/usr/bin/env bash

# Position terminal window
W=$(($(system_profiler SPDisplaysDataType | grep Resolution | awk '{print $2}' | head -1) / 2))
H=$(($(system_profiler SPDisplaysDataType | grep Resolution | awk '{print $4}' | head -1) / 2))

K=60
WW=$((W * K / 100))
WH=$((H * K / 100))
X=$(((W - WW) / 2))
Y=$(((H - WH) / 2))

osascript <<eof
tell application "Terminal"
    set bounds of front window to {$X, $Y, $((X + WW)), $((Y + WH))}
end tell
eof

cd -- "$(dirname -- "$BASH_SOURCE")"
cd ../src

source backend/.venv/bin/activate

set -a
source .env
set +a

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null' EXIT

export BACKEND_URL="http://127.0.0.1:8000"

echo
echo "Backend running at: http://127.0.0.1:8000"
echo "Frontend running at: http://127.0.0.1:3000"
echo

cd frontend
node node_modules/next/dist/bin/next dev --hostname 127.0.0.1 --port 3000
