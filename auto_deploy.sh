#!/bin/bash
# TRD Auto-Deploy Script — Ensures 100% reliable deployment
# Usage: bash auto_deploy.sh

echo "🚀 TRD AUTO-DEPLOY"
echo "=================="

cd ~/trading-server || { echo "❌ Wrong directory"; exit 1; }

# 1. Pull latest code
echo "📥 Pulling latest..."
git fetch origin main
git reset --hard origin/main  # Force overwrite local changes
echo "✅ Code: $(git log --oneline -1)"

# 2. Kill old process
echo "🔪 Stopping old server..."
sudo fuser -k 8000/tcp 2>/dev/null
sleep 3

# 3. Clear Python cache
echo "🧹 Clearing Python cache..."
find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete 2>/dev/null

# 4. Start new server
echo "🚀 Starting server..."
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 > /tmp/api.log 2>&1 &disown
sleep 6

# 5. Verify
VERSION=$(curl -s http://localhost:8000/version 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('version','UNKNOWN'))" 2>/dev/null)
NIFTY_LOT=$(curl -s http://localhost:8000/version 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('lot_sizes',{}).get('NIFTY','?'))" 2>/dev/null)

echo ""
echo "=================================="
echo "✅ DEPLOYED — Version: $VERSION"
echo "   NIFTY Lot Size: $NIFTY_LOT (expected 65)"
echo "=================================="
echo ""

if [ "$NIFTY_LOT" != "65" ]; then
  echo "❌ WARNING: Lot size mismatch! Server may have old code."
  echo "Check logs: tail /tmp/api.log"
fi

# 6. Check tunnel
TUNNEL=$(grep -o 'https://[a-z-]*\.trycloudflare\.com' /tmp/tunnel.log 2>/dev/null | tail -1)
if [ -z "$TUNNEL" ]; then
  echo "⚠️ No Cloudflare tunnel running. Restart with:"
  echo "   pkill cloudflared 2>/dev/null; nohup cloudflared tunnel --url http://localhost:8000 > /tmp/tunnel.log 2>&1 &disown"
else
  echo "🌐 Public URL: $TUNNEL"
fi
