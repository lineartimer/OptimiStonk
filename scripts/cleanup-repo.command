#!/usr/bin/env bash
echo
echo "Cleaning up..."
echo

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

rm -rf ../src/backend/__pycache__
rm -rf ../src/backend/api/__pycache__
rm -rf ../src/backend/core/__pycache__
rm -rf ../src/backend/core/agents/__pycache__
rm -rf ../src/backend/core/tools/__pycache__
rm -rf ../src/backend/database/__pycache__

rm -rf ../src/database.db
rm -rf ../src/database.db-journal

rm -rf ../src/.venv

echo
read -p "Press any key to continue..."