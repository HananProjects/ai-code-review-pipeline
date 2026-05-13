#!/usr/bin/env bash
# Start the FastAPI server + ngrok tunnel, then register the webhook on GitHub.
#
# Prerequisites:
#   brew install ngrok           (or download from ngrok.com)
#   ngrok config add-authtoken <your-token>
#   pip install -r requirements.txt
#   .env file with GITHUB_TOKEN and GITHUB_WEBHOOK_SECRET
#
# Usage:
#   ./scripts/dev.sh owner/repo

set -euo pipefail

REPO="${1:?Usage: ./scripts/dev.sh owner/repo}"
PORT=8080

echo "==> Starting FastAPI on port $PORT..."
uvicorn webhook.handler:app --host 0.0.0.0 --port "$PORT" --reload &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "==> Shutting down..."
    kill "$SERVER_PID" 2>/dev/null || true
    kill "$NGROK_PID"  2>/dev/null || true
    # Optionally remove the webhook on exit:
    # python scripts/setup_webhook.py --repo "$REPO" --url "$PUBLIC_URL/webhook" --delete
    exit 0
}
trap cleanup INT TERM

echo "==> Starting ngrok tunnel..."
ngrok http "$PORT" --log=stdout --log-format=json > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to print the public URL
echo -n "==> Waiting for ngrok URL"
PUBLIC_URL=""
for i in $(seq 1 30); do
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
        | python3 -c "import sys,json; t=json.load(sys.stdin)['tunnels']; print(next(t['public_url'] for t in t if t['proto']=='https'), end='')" 2>/dev/null || true)
    if [[ -n "$PUBLIC_URL" ]]; then break; fi
    echo -n "."
    sleep 1
done
echo ""

if [[ -z "$PUBLIC_URL" ]]; then
    echo "ERROR: Could not get ngrok URL. Check /tmp/ngrok.log"
    cleanup
fi

echo "==> Public URL: $PUBLIC_URL"
echo "==> Registering webhook on $REPO..."
python scripts/setup_webhook.py --repo "$REPO" --url "$PUBLIC_URL/webhook"

echo ""
echo "Ready! Open a PR on $REPO to trigger a review."
echo "Logs → tail -f /tmp/ngrok.log"
echo "Press Ctrl+C to stop."

wait "$SERVER_PID"
