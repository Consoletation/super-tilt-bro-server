#!/bin/bash

# Determine the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BASE_DIR="${SCRIPT_DIR}/.."

# Create and activate a virtualenv if not already done
if [ ! -d "${BASE_DIR}/python/.venv" ]; then
    python3 -m virtualenv "${BASE_DIR}/python/.venv"
fi
source "${BASE_DIR}/python/.venv/bin/activate"
pip install "${BASE_DIR}/python"

mkdir -p /tmp/stb_games
STB_GAME_SUMMARIES=/tmp/stb_games ../src/server/stb_server &
server_pid=$!
stb-login-server --db-file /tmp/stb_login.json --log-file /tmp/stb_login.log &
login_pid=$!
stb-ranking-server --db-file /tmp/stb_ranking.json --log-file /tmp/stb_ranking.log &
ranking_pid=$!
mkdir -p /tmp/stb_replay
stb-replay-server --db-file /tmp/stb_replay.json --replay-dir /tmp/stb_replay --log-file /tmp/stb_replay.log --bmov-to-fm2 ../tools/bmov_to_fm2 &
replay_pid=$!

echo "PIDs"
echo "  server  $server_pid"
echo "  login   $login_pid"
echo "  ranking $ranking_pid"
echo "  replay  $replay_pid"

sleep 5
tail -n0 -F /tmp/stb_games/games.log 2> /dev/null | ./game_ranking_pusher.py --bmov-dir=/tmp/stb_games &
pusher_pid=$!

watch "echo 'ranking:' ; curl -s http://127.0.0.1:8123/api/rankings ; echo ; echo 'replays:' ; curl -s http://127.0.0.1:8125/api/replay/games/"

kill $server_pid $login_pid $ranking_pid $replay_pid $pusher_pid
