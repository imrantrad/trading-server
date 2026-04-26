#!/bin/bash
sudo fuser -k 8000/tcp 2>/dev/null
pkill cloudflared 2>/dev/null
sleep 2
cd ~/trading-server
git pull origin main
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 > /tmp/api.log 2>&1 &
disown
sleep 8
# Start tunnel with browser check bypass
nohup ~/cloudflared tunnel \
  --url http://localhost:8000 \
  --http-host-header "localhost:8000" \
  > /tmp/tunnel.log 2>&1 &
disown
sleep 15
URL=$(grep -o 'https://[a-zA-Z0-9-]*.trycloudflare.com' /tmp/tunnel.log | tail -1)
echo "================================"
echo "SERVER: RUNNING"
echo "URL: $URL"
echo "BHEJO CLAUDE KO: $URL"
echo "================================"
