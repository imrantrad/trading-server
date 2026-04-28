#!/bin/bash
# TRD v12.3 — Auto-start script with PERMANENT domain support

cd ~/trading-server
git pull origin main 2>/dev/null

# Kill old processes
sudo fuser -k 8000/tcp 2>/dev/null
pkill -f uvicorn 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 2

# Start FastAPI
cd ~/trading-server/backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 > /tmp/api.log 2>&1 &
echo "FastAPI started (PID $!)"
sleep 5

# Try permanent named tunnel first
if [ -f ~/.cloudflared/config.yml ]; then
    nohup cloudflared tunnel run trd-trading > /tmp/cf.log 2>&1 &
    sleep 3
    PERM_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com\|https://[^ ]*\.cloudflare\.com' ~/.cloudflared/config.yml | head -1)
    if [ ! -z "$PERM_URL" ]; then
        echo "SERVER: RUNNING"
        echo "PERMANENT URL: $PERM_URL"
        echo "BHEJO CLAUDE KO: $PERM_URL"
        exit 0
    fi
fi

# Fallback: Quick tunnel
nohup cloudflared tunnel --url http://localhost:8000 > /tmp/cf.log 2>&1 &
sleep 8

URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cf.log | head -1)
echo "SERVER: RUNNING"
echo "URL: $URL"
echo "BHEJO CLAUDE KO: $URL"
