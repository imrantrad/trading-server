"""
Trading System v12.3 - Complete Backend
FastAPI + Event Bus + Paper Engine + Risk Manager + Full NLP + Hedge NLP
"""
import sys, os, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

try:
    from events.event_bus import bus, Event, EventType
    from events.market_events import market_handler
    from events.signal_events import signal_handler
    from events.order_events import order_handler
    from events.risk_events import risk_event_handler
    from paper.paper_engine import PaperTradingEngine
    from risk.risk_manager import RiskManager, RiskParams
    from nlp.hedge_nlp import parse_hedge
    EVENT_DRIVEN = True
except Exception as e:
    print(f"Event system: {e}")
    EVENT_DRIVEN = False

app = FastAPI(title="Trading System v12.3 - Event-Driven")

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import os

# Serve dashboard at root
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    dashboard_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            content_str = f.read()
    else:
        content_str = DASHBOARD_HTML
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Access-Control-Allow-Origin": "*",
    }
    return HTMLResponse(content=content_str, headers=headers)

@app.get("/app", response_class=HTMLResponse)
async def serve_app():
    return await serve_dashboard()


# Disable Cloudflare browser integrity check
from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
# Embedded dashboard
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>TRD v12.3 — Institutional Trading</title>
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="TRD Pro">
<meta name="theme-color" content="#00ff88">
<meta name="msapplication-TileColor" content="#060608">
<meta name="description" content="Institutional Derivative Trading Platform — AI-Powered, Professional">
<link rel="manifest" href="/trading-server/manifest.json">
<link rel="apple-touch-icon" href="/trading-server/icons/icon-192.png">
<link rel="icon" type="image/svg+xml" href="/trading-server/icons/icon-96.png">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
:root{--bg:#060608;--bg2:#0d0e14;--bg3:#12131c;--bg4:#181924;--bo:#1e2030;--bo2:#2a2d45;--gr:#00ff88;--rd:#ff3355;--bl:#4f8ef7;--am:#f59e0b;--pu:#a855f7;--cy:#06d6d6;--tx:#e2e8f0;--mu:#64748b}
body.th-midnight{--bg:#00000f;--bg2:#05051a;--bg3:#0a0a25;--bg4:#0f0f30;--bo:#1a1a40;--gr:#00ffcc;--bl:#5555ff;--tx:#dde8ff;--mu:#5060a0}
body.th-matrix{--bg:#000a04;--bg2:#041008;--bg3:#081a0c;--bg4:#0d2412;--bo:#1a3a1e;--gr:#00ff44;--bl:#00cc88;--tx:#ccffdd;--mu:#3a6645}
body.th-purple{--bg:#080412;--bg2:#100820;--bg3:#180c2e;--bg4:#1f1040;--bo:#2a1a50;--gr:#a855f7;--rd:#f43f5e;--bl:#818cf8;--am:#fb923c;--tx:#ede9fe;--mu:#6d28d9}
body.th-solar{--bg:#002b36;--bg2:#073642;--bg3:#0d4654;--bg4:#125465;--bo:#1a5a6e;--gr:#859900;--rd:#dc322f;--bl:#268bd2;--am:#b58900;--tx:#839496;--mu:#586e75}
body.th-light{--bg:#f0f4f8;--bg2:#e2e8f0;--bg3:#d1dce8;--bg4:#c2d0e0;--bo:#94a3b8;--bo2:#64748b;--gr:#059669;--rd:#dc2626;--bl:#2563eb;--am:#d97706;--tx:#1e293b;--mu:#64748b}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--tx);font-family:'JetBrains Mono',monospace;height:100vh;display:flex;flex-direction:column;overflow:hidden;transition:background .3s,color .3s}
::-webkit-scrollbar{width:3px;height:3px}::-webkit-scrollbar-thumb{background:var(--bo2);border-radius:2px}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes fadeIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@keyframes ticker{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.hdr{height:44px;background:var(--bg2);border-bottom:1px solid var(--bo);display:flex;align-items:center;justify-content:space-between;padding:0 14px;flex-shrink:0}
.tkr-wrap{height:24px;background:var(--bg2);border-bottom:1px solid var(--bo);overflow:hidden;flex-shrink:0}
.tkr-inner{display:flex;gap:28px;animation:ticker 45s linear infinite;white-space:nowrap;padding-left:100%;font-size:9px;align-items:center;height:24px}
.tabs-bar{background:var(--bg2);border-bottom:1px solid var(--bo);display:flex;overflow-x:auto;flex-shrink:0;scrollbar-width:none}
.tabs-bar::-webkit-scrollbar{display:none}
.tab-btn{padding:9px 14px;font-size:8px;letter-spacing:1.2px;cursor:pointer;border:none;background:none;color:var(--mu);border-bottom:2px solid transparent;white-space:nowrap;font-family:inherit;font-weight:500;transition:color .2s}
.tab-btn:hover{color:var(--tx)}.tab-btn.active{color:var(--gr);border-bottom-color:var(--gr)}
.main{flex:1;overflow:hidden;position:relative}
.panel{display:none;position:absolute;inset:0;overflow-y:auto;padding:12px;flex-direction:column;gap:10px;animation:fadeIn .2s ease}
.panel.active{display:flex}
.card{background:var(--bg3);border:1px solid var(--bo);border-radius:8px;padding:12px;box-shadow:0 2px 8px rgba(0,0,0,.3)}
.card-hdr{font-size:8px;color:var(--mu);letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;font-weight:600}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.stat{background:var(--bg4);border:1px solid var(--bo);border-radius:6px;padding:10px}
.slbl{font-size:8px;color:var(--mu);letter-spacing:1px;font-weight:500}
.sval{font-size:18px;font-weight:700;margin-top:4px;line-height:1.1}
.ssub{font-size:8px;color:var(--mu);margin-top:2px}
.btn{font-family:inherit;cursor:pointer;border-radius:5px;font-size:9px;letter-spacing:1px;border:1px solid;font-weight:600;transition:all .15s;white-space:nowrap}
.btn:hover{filter:brightness(1.25);transform:translateY(-1px)}.btn:active{transform:scale(.97)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.bg{background:#001a0e;color:var(--gr);border-color:var(--gr)}
.br{background:#1a0008;color:var(--rd);border-color:var(--rd)}
.bb{background:#0a1628;color:var(--bl);border-color:var(--bl)}
.ba{background:#1a0e00;color:var(--am);border-color:var(--am)}
.bp{background:#160a28;color:var(--pu);border-color:var(--pu)}
.bsm{padding:4px 10px}.bmd{padding:8px 16px}.blg{padding:11px 0;width:100%;font-size:11px}
.tog{padding:5px 10px;font-size:9px;font-family:inherit;background:var(--bg4);border:1px solid var(--bo);color:var(--mu);cursor:pointer;border-radius:4px;letter-spacing:1px;transition:all .15s}
.tg{background:#001a0e;border-color:var(--gr);color:var(--gr);font-weight:700}
.tr{background:#1a0008;border-color:var(--rd);color:var(--rd);font-weight:700}
.tb{background:#0a1628;border-color:var(--bl);color:var(--bl);font-weight:700}
.ta{background:#1a0e00;border-color:var(--am);color:var(--am);font-weight:700}
input,select,textarea{background:var(--bg4);border:1px solid var(--bo2);color:var(--tx);font-family:inherit;font-size:11px;border-radius:5px;padding:7px 10px;outline:none;width:100%;transition:border-color .2s}
input:focus,select:focus,textarea:focus{border-color:var(--gr)}
textarea{resize:vertical;min-height:60px}
.lbl{font-size:8px;color:var(--mu);letter-spacing:1px;margin-bottom:3px;font-weight:500}
.tbl{width:100%;font-size:9px;border-collapse:collapse}
.tbl th{color:var(--mu);font-size:7px;letter-spacing:1px;padding:7px 8px;text-align:left;border-bottom:1px solid var(--bo);font-weight:600;background:var(--bg4)}
.tbl td{padding:7px 8px;border-bottom:1px solid var(--bo)}
.tbl tr:hover td{background:rgba(255,255,255,.02)}
.pb{height:4px;background:var(--bg4);border-radius:2px;overflow:hidden;margin-top:3px}
.pf{height:100%;border-radius:2px;transition:width .6s ease}
.bdg{font-size:7px;padding:2px 7px;border-radius:10px;font-weight:700;letter-spacing:1px;border:1px solid}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.dot.pulse{animation:pulse 1.5s infinite}
.log-line{display:flex;gap:8px;padding:3px 0;border-bottom:1px solid rgba(30,32,48,.5);font-size:9px;animation:fadeIn .2s}
#toast{position:fixed;top:52px;right:14px;z-index:9999;background:var(--bg2);border-left:3px solid var(--gr);border:1px solid var(--bo);border-radius:5px;padding:10px 14px;font-size:10px;display:none;max-width:300px;box-shadow:0 4px 16px rgba(0,0,0,.4)}
.plan-card{background:var(--bg4);border:2px solid var(--bo);border-radius:8px;padding:14px;cursor:pointer;text-align:center;transition:all .2s}
.plan-card:hover{transform:translateY(-2px)}.plan-card.active{border-color:var(--gr);background:#001a0e}
.th-card{border:2px solid var(--bo);border-radius:8px;padding:12px;cursor:pointer;text-align:center;transition:all .2s}
.th-card:hover,.th-card.active{border-color:var(--gr)}
.ptab{padding:7px 12px;font-size:8px;cursor:pointer;border:none;background:none;color:var(--mu);border-bottom:2px solid transparent;font-family:inherit;letter-spacing:1px;transition:color .2s}
.ptab.active{color:var(--gr);border-bottom-color:var(--gr)}
.cal-cell{border-radius:4px;display:flex;flex-direction:column;align-items:center;justify-content:center;cursor:pointer;transition:filter .2s;border:1px solid transparent;width:36px;height:36px;font-size:7px}
.cal-cell:hover{filter:brightness(1.5)}
@media(max-width:600px){.g4{grid-template-columns:1fr 1fr}}

/* ── MOBILE OPTIMIZATIONS ── */
@media(max-width:768px){
  .hdr{height:48px;padding:0 10px}
  .tabs-bar{-webkit-overflow-scrolling:touch}
  .tab-btn{padding:10px 12px;font-size:9px}
  .panel{padding:8px}
  .g4{grid-template-columns:1fr 1fr}
  .g3{grid-template-columns:1fr 1fr}
  .card{padding:10px}
  .sval{font-size:16px}
}
/* INSTALL BANNER */
#install-banner{display:none;position:fixed;bottom:0;left:0;right:0;background:linear-gradient(135deg,#001a0e,#0a1628);border-top:1px solid var(--gr);padding:12px 16px;z-index:500;animation:slideUp .3s ease}
@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
/* CHAT WIDGET */
#chat-widget{position:fixed;bottom:80px;right:14px;z-index:998}
#chat-btn{width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,var(--gr),var(--bl));border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:22px;box-shadow:0 4px 16px rgba(0,255,136,.3);transition:all .2s}
#chat-btn:hover{transform:scale(1.1);box-shadow:0 6px 24px rgba(0,255,136,.5)}
#chat-window{display:none;position:fixed;bottom:140px;right:14px;width:340px;height:500px;background:var(--bg2);border:1px solid var(--bo2);border-radius:12px;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,.5);z-index:999;flex-direction:column;animation:fadeIn .25s ease}
#chat-window.open{display:flex}
@media(max-width:768px){#chat-window{width:calc(100vw - 20px);right:10px;height:420px;bottom:130px}}
.chat-hdr{background:linear-gradient(135deg,#001a0e,#0a1628);padding:14px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;border-bottom:1px solid var(--bo)}
.chat-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth}
.chat-msg{max-width:85%;padding:10px 12px;border-radius:10px;font-size:10px;line-height:1.6;animation:fadeIn .2s}
.chat-msg.bot{background:var(--bg4);border:1px solid var(--bo);align-self:flex-start;border-bottom-left-radius:3px}
.chat-msg.user{background:linear-gradient(135deg,#001a0e,#0a1628);border:1px solid var(--gr)30;color:var(--gr);align-self:flex-end;border-bottom-right-radius:3px}
.chat-typing{font-size:9px;color:var(--mu);padding:6px 12px;animation:pulse 1s infinite}
.chat-suggestions{display:flex;flex-wrap:wrap;gap:4px;padding:8px 12px;border-top:1px solid var(--bo);flex-shrink:0;overflow-x:auto}
.chat-sugg{font-size:8px;padding:4px 10px;background:var(--bg4);border:1px solid var(--bo2);border-radius:12px;cursor:pointer;white-space:nowrap;font-family:inherit;color:var(--mu);transition:all .15s}
.chat-sugg:hover{border-color:var(--gr);color:var(--gr)}
.chat-inp-wrap{display:flex;gap:6px;padding:10px;border-top:1px solid var(--bo);flex-shrink:0}
.chat-inp-wrap input{border-radius:20px;font-size:11px;padding:8px 14px}
.chat-send{width:36px;height:36px;border-radius:50%;background:var(--gr);border:none;cursor:pointer;color:#000;font-size:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .15s}
.chat-send:hover{background:var(--bl);}
/* BOTTOM NAV (mobile) */
#bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;background:var(--bg2);border-top:1px solid var(--bo);z-index:400;padding:6px 0;padding-bottom:env(safe-area-inset-bottom)}
@media(max-width:600px){
  #bottom-nav{display:flex;justify-content:space-around}
  .tabs-bar{display:none}
  .main{padding-bottom:60px}
  #chat-widget{bottom:72px}
}
.bnav-btn{display:flex;flex-direction:column;align-items:center;gap:2px;cursor:pointer;padding:4px 8px;border-radius:6px;border:none;background:none;color:var(--mu);font-family:inherit;font-size:7px;letter-spacing:.5px;transition:color .2s;min-width:50px}
.bnav-btn.active{color:var(--gr)}
.bnav-btn span:first-child{font-size:18px}
/* NOTIFICATION BADGE */
.notif-badge{position:absolute;top:-4px;right:-4px;width:16px;height:16px;background:var(--rd);border-radius:50%;font-size:9px;display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff}
</style></head>
<body id="body">
<div id="toast"></div>
<!-- HEADER -->
<div class="hdr">
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-family:'Orbitron';font-size:12px;color:var(--gr);font-weight:900;letter-spacing:2px">▶ TRD v12.3</span>
    <span class="bdg bg" id="mode-bdg" style="border-color:var(--bl);background:#0a1628;color:var(--bl)">PAPER</span>
    <span class="bdg" id="plan-bdg" style="border-color:var(--pu);background:#160a28;color:var(--pu)">PRO</span>
  </div>
  <div style="display:flex;align-items:center;gap:10px">
    <span style="font-size:9px;color:var(--mu)" id="clk"></span>
    <div style="display:flex;align-items:center;gap:5px">
      <div class="dot pulse" id="api-dot" style="background:var(--am)"></div>
      <span style="font-size:8px;color:var(--mu)" id="api-lbl">CONNECTING</span>
    </div>
    <span class="bdg" id="src-bdg" style="border-color:var(--gr)20;background:var(--bg3);color:var(--mu);font-size:7px">DATA</span>
    <button class="btn bsm br" id="kill-btn" onclick="toggleKill()">■ KILL</button>
    <div style="display:flex;align-items:center;gap:6px;cursor:pointer" onclick="showPanel('profile')">
      <div style="width:30px;height:30px;border-radius:50%;background:var(--gr);color:#000;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px" id="hdr-av">D</div>
      <span style="font-size:9px;color:var(--mu)">demo</span>
    </div>
  </div>
</div>
<div class="tkr-wrap"><div class="tkr-inner" id="ticker"></div></div>
<div class="tabs-bar">
  <button class="tab-btn active" onclick="showPanel('trade',this)">◈ TRADE</button>
  <button class="tab-btn" onclick="showPanel('positions',this)">◉ POSITIONS</button>
  <button class="tab-btn" onclick="showPanel('risk',this)">⚡ RISK</button>
  <button class="tab-btn" onclick="showPanel('scanner',this)">◎ SCANNER</button>
  <button class="tab-btn" onclick="showPanel('options',this)">◆ OPTIONS</button>
  <button class="tab-btn" onclick="showPanel('backtest',this)">∞ BACKTEST</button>
  <button class="tab-btn" onclick="showPanel('strategies',this)">★ STRATEGIES</button>
  <button class="tab-btn" onclick="showPanel('journal',this)">✎ JOURNAL</button>
  <button class="tab-btn" onclick="showPanel('reports',this)">📊 REPORTS</button>
  <button class="tab-btn" onclick="showPanel('calc',this)">∑ CALC</button>
  <button class="tab-btn" onclick="showPanel('ai',this)">🤖 AI ENGINE</button>
  <button class="tab-btn" onclick="showPanel('admin',this)">⚙ ADMIN</button>
  <button class="tab-btn" onclick="showPanel('legal',this)">📋 LEGAL</button>
  <button class="tab-btn" onclick="showPanel('profile',this)">👤 PROFILE</button>
</div>
<div class="main">
<!-- TRADE PANEL -->
<div id="panel-trade" class="panel active">
  <div class="g4">
    <div class="stat"><div class="slbl">TOTAL P&L</div><div class="sval" id="s-pnl" style="color:var(--gr)">₹0</div><div class="ssub" id="s-pp">0% return</div></div>
    <div class="stat"><div class="slbl">TODAY P&L</div><div class="sval" id="s-dp" style="color:var(--gr)">₹0</div><div class="ssub" id="s-tc">0 trades</div></div>
    <div class="stat"><div class="slbl">WIN RATE</div><div class="sval" id="s-wr" style="color:var(--gr)">0%</div><div class="ssub" id="s-wl">0W / 0L</div></div>
    <div class="stat"><div class="slbl">CAPITAL</div><div class="sval" id="s-cap" style="color:var(--bl);font-size:14px">₹5.0L</div><div class="ssub" id="s-dd">Drawdown: 0%</div></div>
  </div>
  <div class="g2" style="gap:10px">
    <div class="card">
      <div class="card-hdr">ORDER ENTRY</div>
      <div style="margin-bottom:8px"><div class="lbl">TRADING MODE</div>
        <div style="display:flex;gap:4px"><button class="tog tb" id="m-PAPER" onclick="setMode('PAPER',this)">PAPER</button><button class="tog" id="m-LIVE" onclick="setMode('LIVE',this)">LIVE</button><button class="tog" id="m-BACKTEST" onclick="setMode('BACKTEST',this)">BACKTEST</button></div>
      </div>
      <div style="margin-bottom:8px"><div class="lbl">INSTRUMENT</div>
        <div style="display:flex;gap:4px;flex-wrap:wrap">
          <button class="tog ta" id="bi-NIFTY" onclick="setInst('NIFTY',this)">NIFTY</button>
          <button class="tog" id="bi-BANKNIFTY" onclick="setInst('BANKNIFTY',this)">BANKNIFTY</button>
          <button class="tog" id="bi-FINNIFTY" onclick="setInst('FINNIFTY',this)">FINNIFTY</button>
          <button class="tog" id="bi-SENSEX" onclick="setInst('SENSEX',this)">SENSEX</button>
        </div>
      </div>
      <div class="g2" style="gap:6px;margin-bottom:8px">
        <div><div class="lbl">ACTION</div><div style="display:flex;gap:4px"><button class="tog tg" id="ba-BUY" onclick="setAction('BUY')">BUY</button><button class="tog" id="ba-SELL" onclick="setAction('SELL')">SELL</button></div></div>
        <div><div class="lbl">OPTION TYPE</div><div style="display:flex;gap:4px"><button class="tog tb" id="bt-CE" onclick="setType('CE')">CE</button><button class="tog" id="bt-PE" onclick="setType('PE')">PE</button><button class="tog" id="bt-FUT" onclick="setType('FUT')">FUT</button></div></div>
      </div>
      <div class="g2" style="gap:6px;margin-bottom:6px">
        <div><div class="lbl">STRIKE</div><input type="number" id="f-strike" placeholder="23900"></div>
        <div><div class="lbl">LOTS</div><input type="number" id="f-lots" value="1" min="1"></div>
      </div>
      <div class="g2" style="gap:6px;margin-bottom:6px">
        <div><div class="lbl">ENTRY PRICE ₹</div><input type="number" id="f-price" placeholder="Premium"></div>
        <div><div class="lbl">EXPIRY</div><select id="f-expiry"><option>WEEKLY</option><option>NEXT_WEEKLY</option><option>MONTHLY</option></select></div>
      </div>
      <div class="g2" style="gap:6px;margin-bottom:6px">
        <div><div class="lbl">STOP LOSS (pts)</div><input type="number" id="f-sl" placeholder="100"></div>
        <div><div class="lbl">TARGET (pts)</div><input type="number" id="f-tgt" placeholder="200"></div>
      </div>
      <div style="margin-bottom:10px"><div class="lbl">TRAILING SL (pts)</div><input type="number" id="f-trail" value="0"></div>
      <button class="btn blg bg" id="exec-btn" onclick="executeTrade()">▶ EXECUTE BUY NIFTY CE</button>
      <div style="margin-top:12px"><div class="lbl" style="margin-bottom:6px">EXECUTED ORDERS</div>
        <div style="overflow-x:auto"><table class="tbl"><thead><tr><th>ID</th><th>INST</th><th>OPT</th><th>STRIKE</th><th>LOTS</th><th>ENTRY</th><th>SL</th><th>TGT</th><th>SIDE</th><th>STATUS</th></tr></thead><tbody id="exec-rows"></tbody></table></div>
      </div>
    </div>
    <div style="display:flex;flex-direction:column;gap:8px">
      <div class="card">
        <div class="card-hdr">◆ NLP ORDER ENTRY</div>
        <textarea id="nlp-input" rows="3" placeholder="buy nifty atm call if rsi under 30 sl 100 target 300&#10;sell banknifty iron condor weekly vix above 15&#10;kharido nifty 2 lots subah ema crossover trailing sl 50"></textarea>
        <div style="display:flex;gap:6px;margin-top:6px">
          <button class="btn bmd bb" style="flex:1" onclick="nlpParse()">◆ PARSE</button>
          <button class="btn bmd bg" style="flex:1" onclick="nlpExecute()">▶ PARSE + EXEC</button>
        </div>
        <div id="nlp-output" style="display:none;margin-top:8px;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:8px;font-size:8px;line-height:2;max-height:90px;overflow-y:auto"></div>
      </div>
      <div class="card">
        <div class="card-hdr">MARKET WATCH <span id="src-label" style="font-size:7px;color:var(--mu)">LOADING...</span></div>
        <div id="mkt-watch" style="display:grid;grid-template-columns:repeat(3,1fr);gap:4px"></div>
      </div>
      <div class="card">
        <div class="card-hdr">LOG <button class="btn bsm ba" onclick="document.getElementById('log-box').innerHTML=''">CLR</button></div>
        <div id="log-box" style="max-height:110px;overflow-y:auto"></div>
      </div>
    </div>
  </div>
</div>

<!-- POSITIONS PANEL -->
<div id="panel-positions" class="panel">
  <div class="g3">
    <div class="stat"><div class="slbl">OPEN POSITIONS</div><div class="sval" id="p-open" style="color:var(--bl)">0</div></div>
    <div class="stat"><div class="slbl">UNREALIZED P&L</div><div class="sval" id="p-upnl" style="color:var(--gr)">₹0</div></div>
    <div class="stat"><div class="slbl">REALIZED P&L</div><div class="sval" id="p-rpnl" style="color:var(--gr)">₹0</div></div>
  </div>
  <div class="card">
    <div class="card-hdr">OPEN POSITIONS
      <div style="display:flex;gap:6px"><button class="btn bsm ba" onclick="loadPositions()">↻</button><button class="btn bsm br" onclick="closeAllPositions()">✕ ALL</button></div>
    </div>
    <div style="overflow-x:auto"><table class="tbl"><thead><tr><th>ID</th><th>INST</th><th>TYPE</th><th>STRIKE</th><th>QTY</th><th>ENTRY</th><th>LTP</th><th>SL</th><th>TGT</th><th>P&L</th><th>ACT</th></tr></thead><tbody id="pos-table"></tbody></table></div>
  </div>
</div>

<!-- RISK PANEL -->
<div id="panel-risk" class="panel">
  <div class="g4">
    <div class="stat"><div class="slbl">RISK STATUS</div><div class="sval" id="r-status" style="color:var(--gr);font-size:13px">● GREEN</div></div>
    <div class="stat"><div class="slbl">DAILY LOSS</div><div class="sval" id="r-dloss" style="color:var(--gr)">₹0</div><div class="ssub" id="r-dlosspct">0% used</div></div>
    <div class="stat"><div class="slbl">DRAWDOWN</div><div class="sval" id="r-dd" style="color:var(--gr)">0%</div></div>
    <div class="stat"><div class="slbl">CONSEC LOSSES</div><div class="sval" id="r-cl" style="color:var(--am)">0</div></div>
  </div>
  <div class="g2" style="gap:10px">
    <div class="card">
      <div class="card-hdr">RISK METERS</div>
      <div style="display:flex;flex-direction:column;gap:10px">
        <div><div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:3px"><span style="color:var(--mu)">DAILY LOSS LIMIT</span><span id="rm-dl">0% / 3%</span></div><div class="pb"><div class="pf" id="pb-dl" style="width:0%;background:var(--gr)"></div></div></div>
        <div><div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:3px"><span style="color:var(--mu)">DRAWDOWN</span><span id="rm-dd">0% / 10%</span></div><div class="pb"><div class="pf" id="pb-dd" style="width:0%;background:var(--bl)"></div></div></div>
        <div><div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:3px"><span style="color:var(--mu)">OPEN POSITIONS</span><span id="rm-pos">0 / 5</span></div><div class="pb"><div class="pf" id="pb-pos" style="width:0%;background:var(--am)"></div></div></div>
        <div><div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:3px"><span style="color:var(--mu)">TRADES TODAY</span><span id="rm-trd">0 / 10</span></div><div class="pb"><div class="pf" id="pb-trd" style="width:0%;background:var(--pu)"></div></div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-hdr">POSITION SIZER</div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <div class="g2" style="gap:4px"><div><div class="lbl">CAPITAL ₹</div><input type="number" id="ps-cap" value="500000"></div><div><div class="lbl">RISK %</div><input type="number" id="ps-risk" value="1" step="0.5"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">SL POINTS</div><input type="number" id="ps-sl" value="100"></div><div><div class="lbl">LOT SIZE</div><input type="number" id="ps-lot" value="50"></div></div>
        <button class="btn bmd bb" onclick="calcPositionSize()" style="width:100%">∑ CALC LOTS</button>
        <div id="ps-result" style="display:none;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px;font-size:10px"></div>
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-hdr">EMERGENCY CONTROLS</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn bmd br" onclick="toggleKill()">■ KILL SWITCH</button>
      <button class="btn bmd bg" onclick="resumeTrading()">▶ RESUME</button>
      <button class="btn bmd ba" onclick="resetPaper()">↺ RESET PAPER</button>
    </div>
  </div>
</div>

<!-- SCANNER PANEL -->
<div id="panel-scanner" class="panel">
  <div class="card"><div class="card-hdr">MARKET SCANNER<button class="btn bmd bg" onclick="runScanner()">◎ SCAN NOW</button></div><div id="scanner-out" style="min-height:80px"><div style="color:var(--mu);padding:20px;text-align:center">Click SCAN NOW</div></div></div>
  <div class="g2" style="gap:10px">
    <div class="card"><div class="card-hdr">IV RANK</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <div class="g2" style="gap:4px"><div><div class="lbl">INSTRUMENT</div><select id="iv-inst"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option></select></div><div><div class="lbl">CURRENT IV %</div><input type="number" id="iv-val" value="15" step="0.5"></div></div>
        <button class="btn bmd bb" onclick="getIVRank()" style="width:100%">GET IV RANK</button>
        <div id="iv-out" style="display:none;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px"></div>
      </div>
    </div>
    <div class="card"><div class="card-hdr">FII/DII + EXPIRY</div>
      <button class="btn bmd bb" onclick="getFIIDII()" style="width:100%;margin-bottom:8px">FETCH FII/DII</button>
      <div id="fii-out" style="font-size:9px;color:var(--mu);margin-bottom:10px">Click to load</div>
      <button class="btn bmd ba" onclick="getExpiryData()" style="width:100%">GET EXPIRY</button>
      <div id="expiry-out" style="font-size:9px;color:var(--mu);margin-top:8px">Click to load</div>
    </div>
  </div>
</div>

<!-- OPTIONS PANEL -->
<div id="panel-options" class="panel">
  <div class="card">
    <div class="card-hdr">OPTIONS CHAIN<button class="btn bmd bg" onclick="loadOptionsChain()">◆ LOAD</button></div>
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">
      <div style="flex:1;min-width:80px"><div class="lbl">INSTRUMENT</div><select id="ch-inst"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option></select></div>
      <div style="flex:1;min-width:60px"><div class="lbl">DTE</div><input type="number" id="ch-dte" value="7"></div>
      <div style="flex:1;min-width:60px"><div class="lbl">IV %</div><input type="number" id="ch-iv" value="15" step="0.5"></div>
    </div>
    <div style="overflow-x:auto"><table class="tbl"><thead><tr><th style="color:var(--gr)">CE OI</th><th style="color:var(--gr)">CE LTP</th><th style="color:var(--gr)">CE Δ</th><th style="color:var(--gr)">CE θ</th><th style="background:var(--bg3);color:var(--am);text-align:center">STRIKE</th><th style="color:var(--rd)">PE θ</th><th style="color:var(--rd)">PE Δ</th><th style="color:var(--rd)">PE LTP</th><th style="color:var(--rd)">PE OI</th></tr></thead><tbody id="chain-table"></tbody></table></div>
  </div>
  <div class="g2" style="gap:10px">
    <div class="card"><div class="card-hdr">GREEKS CALCULATOR</div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <div class="g2" style="gap:4px"><div><div class="lbl">SPOT</div><input type="number" id="bs-spot" placeholder="23900"></div><div><div class="lbl">STRIKE</div><input type="number" id="bs-strike" placeholder="24000"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">DTE</div><input type="number" id="bs-dte" value="7"></div><div><div class="lbl">IV %</div><input type="number" id="bs-iv" value="15"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">TYPE</div><select id="bs-type"><option>CE</option><option>PE</option></select></div><div><div class="lbl">RATE %</div><input type="number" id="bs-rate" value="6.5"></div></div>
        <button class="btn bmd bg" onclick="calcGreeks()" style="width:100%">◆ CALC GREEKS</button>
        <div id="greeks-out" style="display:none;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px"></div>
      </div>
    </div>
    <div class="card"><div class="card-hdr">MARGIN CALC</div>
      <div style="display:flex;flex-direction:column;gap:6px">
        <div><div class="lbl">INSTRUMENT</div><select id="mg-inst"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option></select></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">LOTS</div><input type="number" id="mg-lots" value="1"></div><div><div class="lbl">PRICE ₹</div><input type="number" id="mg-price" placeholder="100"></div></div>
        <select id="mg-type"><option>OPTIONS</option><option>FUTURES</option></select>
        <button class="btn bmd bb" onclick="calcMargin()" style="width:100%">∑ MARGIN</button>
        <div id="margin-out" style="display:none;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px;font-size:10px"></div>
      </div>
    </div>
  </div>
</div>

<!-- BACKTEST PANEL -->
<div id="panel-backtest" class="panel">
  <div class="card">
    <div class="card-hdr">ADVANCED BACKTEST — DATE-WISE P&L CALENDAR</div>
    <div class="g2" style="gap:8px;margin-bottom:8px">
      <div><div class="lbl">STRATEGY</div>
        <select id="bt-strategy">
          <optgroup label="HIGH WIN-RATE">
            <option value="STR_THETA_DECAY">Weekly Theta Decay (72% WR)</option>
            <option value="STR_ORB">Opening Range Breakout (68%)</option>
            <option value="STR_IRON_CONDOR_WEEKLY">Weekly Iron Condor (78%)</option>
            <option value="STR_VWAP_PULLBACK">VWAP Pullback (65%)</option>
            <option value="STR_GAP_FADE">Gap Fade (74%)</option>
            <option value="STR_SUPERTREND_EMA">Supertrend+EMA (63%)</option>
            <option value="STR_PCR_REVERSAL">PCR Reversal (71%)</option>
            <option value="STR_BANKNIFTY_SCALP">BankNifty Scalp (62%)</option>
            <option value="STR_MAX_PAIN_EXPIRY">Max Pain Expiry (76%)</option>
            <option value="STR_FII_MOMENTUM">FII Momentum (69%)</option>
          </optgroup>
          <optgroup label="CLASSIC">
            <option value="EMA_CROSS">EMA Crossover</option>
            <option value="RSI_MEAN_REVERSION">RSI Mean Reversion</option>
            <option value="BOLLINGER_BREAKOUT">Bollinger Breakout</option>
          </optgroup>
        </select>
      </div>
      <div><div class="lbl">YOUR CAPITAL (₹)</div><input type="number" id="bt-capital" value="100000" placeholder="100000"></div>
    </div>
    <div class="g2" style="gap:8px;margin-bottom:10px">
      <div><div class="lbl">PERIOD</div><select id="bt-months"><option value="1">1 Month</option><option value="3" selected>3 Months</option><option value="6">6 Months</option><option value="12">12 Months</option></select></div>
      <div><div class="lbl">LOTS</div><input type="number" id="bt-lots" value="1" min="1"></div>
    </div>
    <button class="btn blg bg" id="bt-btn" onclick="runBacktest()">∞ RUN BACKTEST + DATE-WISE CALENDAR</button>
    <div id="bt-result" style="display:none;margin-top:12px"></div>
  </div>
</div>
<!-- STRATEGIES PANEL -->
<div id="panel-strategies" class="panel">
  <div style="display:flex;gap:6px;flex-wrap:wrap">
    <button class="btn bmd bg" onclick="loadBuiltinStrategies()">★ 10 BUILT-IN</button>
    <button class="btn bmd bb" onclick="loadMyStrategies()">MY STRATEGIES</button>
    <button class="btn bmd ba" onclick="toggleNLPBuilder()">◆ NLP BUILDER</button>
  </div>
  <div id="nlp-builder" class="card" style="display:none;border:1px solid var(--gr)30">
    <div class="card-hdr" style="color:var(--gr)">◆ NLP STRATEGY BUILDER — AUTO-FILL FROM NATURAL LANGUAGE</div>
    <div style="margin-bottom:8px"><div class="lbl">DESCRIBE YOUR STRATEGY</div>
      <textarea id="nlp-strat-input" rows="3" placeholder="buy nifty atm call if rsi under 30 and ema crossover stop loss 100 target 300&#10;sell banknifty iron condor weekly vix above 15&#10;kharido nifty 2 lots subah fii buying trailing sl 50"></textarea>
    </div>
    <button class="btn bmd bg" onclick="parseNLPStrategy()" style="width:100%;margin-bottom:10px">◆ PARSE → AUTO-FILL ALL FIELDS</button>
    <div id="nlp-strat-parsed" style="display:none;background:#001a0e;border:1px solid var(--gr)30;border-radius:5px;padding:8px;font-size:8px;margin-bottom:10px;line-height:2;color:var(--gr)"></div>
    <div class="g2" style="gap:8px;margin-bottom:8px">
      <div><div class="lbl">STRATEGY NAME</div><input id="ns-name" placeholder="Auto-filled"></div>
      <div><div class="lbl">INSTRUMENT</div><select id="ns-inst"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option></select></div>
    </div>
    <div class="g2" style="gap:8px;margin-bottom:8px">
      <div><div class="lbl">ENTRY CONDITIONS</div><textarea id="ns-entry" rows="3" placeholder="Auto-filled from NLP"></textarea></div>
      <div><div class="lbl">EXIT CONDITIONS</div><textarea id="ns-exit" rows="3" placeholder="Auto-filled from NLP"></textarea></div>
    </div>
    <div class="g2" style="gap:8px;margin-bottom:8px">
      <div><div class="lbl">SL POINTS</div><input type="number" id="ns-sl" value="100"></div>
      <div><div class="lbl">TARGET POINTS</div><input type="number" id="ns-tgt" value="200"></div>
    </div>
    <div class="g2" style="gap:8px;margin-bottom:8px">
      <div><div class="lbl">TIMEFRAME</div><select id="ns-tf"><option>5MIN</option><option selected>15MIN</option><option>1HOUR</option><option>DAILY</option></select></div>
      <div><div class="lbl">LOTS</div><input type="number" id="ns-lots" value="1"></div>
    </div>
    <div style="margin-bottom:10px"><div class="lbl">TAGS</div><input id="ns-tags" placeholder="momentum,ema,intraday"></div>
    <div style="display:flex;gap:6px">
      <button class="btn bmd bg" onclick="saveMyStrategy()" style="flex:1">✓ SAVE</button>
      <button class="btn bmd ba" onclick="backtestMyStrategy()" style="flex:1">∞ BACKTEST</button>
      <button class="btn bmd br" onclick="toggleNLPBuilder()">✕</button>
    </div>
  </div>
  <div id="strat-list" style="display:flex;flex-direction:column;gap:8px"><div style="color:var(--mu);padding:24px;text-align:center">Select a tab above</div></div>
</div>

<!-- JOURNAL PANEL -->
<div id="panel-journal" class="panel">
  <div class="g4">
    <div class="stat"><div class="slbl">PROFIT FACTOR</div><div class="sval" id="j-pf" style="color:var(--gr)">0</div></div>
    <div class="stat"><div class="slbl">AVG WIN</div><div class="sval" id="j-aw" style="color:var(--gr)">₹0</div></div>
    <div class="stat"><div class="slbl">AVG LOSS</div><div class="sval" id="j-al" style="color:var(--rd)">₹0</div></div>
    <div class="stat"><div class="slbl">EXPECTANCY</div><div class="sval" id="j-ex" style="color:var(--bl)">₹0</div></div>
  </div>
  <div class="g2" style="gap:10px">
    <div class="card"><div class="card-hdr">ADD JOURNAL ENTRY</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <div class="g2" style="gap:4px"><div><div class="lbl">INSTRUMENT</div><input id="jn-inst" placeholder="NIFTY"></div><div><div class="lbl">P&L ₹</div><input type="number" id="jn-pnl" placeholder="500"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">EMOTION</div><select id="jn-emotion"><option>CALM</option><option>DISCIPLINED</option><option>FOMO</option><option>GREEDY</option><option>FEARFUL</option><option>REVENGE</option></select></div><div><div class="lbl">RATING 1-10</div><input type="number" id="jn-rating" value="7" min="1" max="10"></div></div>
        <div><div class="lbl">MISTAKES</div><textarea id="jn-mistakes" rows="2" placeholder="What went wrong?"></textarea></div>
        <div><div class="lbl">LESSONS</div><textarea id="jn-lessons" rows="2" placeholder="What did I learn?"></textarea></div>
        <button class="btn bmd bg" onclick="saveJournalEntry()" style="width:100%">✎ SAVE</button>
      </div>
    </div>
    <div class="card"><div class="card-hdr">TRADE HISTORY<button class="btn bsm bb" onclick="loadTradeHistory()">↻</button></div>
      <div style="overflow-x:auto"><table class="tbl"><thead><tr><th>ID</th><th>INST</th><th>ACTION</th><th>ENTRY</th><th>EXIT</th><th>REASON</th><th>P&L</th></tr></thead><tbody id="trades-table"></tbody></table></div>
    </div>
  </div>
</div>

<!-- REPORTS PANEL -->
<div id="panel-reports" class="panel">
  <div style="display:flex;gap:6px;flex-wrap:wrap">
    <button class="btn bmd bg" onclick="getReport('daily')">📊 DAILY</button>
    <button class="btn bmd bb" onclick="getReport('weekly')">📈 WEEKLY</button>
    <button class="btn bmd ba" onclick="getReport('performance')">∑ PERFORMANCE</button>
    <button class="btn bmd bp" onclick="getExpiryReport()">📅 EXPIRY</button>
  </div>
  <div class="card"><div class="card-hdr" id="report-title">REPORTS</div><div id="report-body" style="color:var(--mu);font-size:10px;padding:10px 0">Select a report above</div></div>
</div>

<!-- CALC PANEL -->
<div id="panel-calc" class="panel">
  <div class="g2" style="gap:10px">
    <div class="card"><div class="card-hdr">R:R CALCULATOR</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <div class="g2" style="gap:4px"><div><div class="lbl">ENTRY</div><input type="number" id="rr-entry" placeholder="23900"></div><div><div class="lbl">STOP LOSS</div><input type="number" id="rr-sl" placeholder="23800"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">TARGET</div><input type="number" id="rr-target" placeholder="24200"></div><div><div class="lbl">LOTS</div><input type="number" id="rr-lots" value="1"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">LOT SIZE</div><input type="number" id="rr-lotsize" value="50"></div><div><div class="lbl">CAPITAL ₹</div><input type="number" id="rr-capital" value="500000"></div></div>
        <button class="btn bmd bb" onclick="calcRR()" style="width:100%">∑ CALCULATE</button>
        <div id="rr-result" style="display:none;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px"></div>
      </div>
    </div>
    <div class="card"><div class="card-hdr">BLACK-SCHOLES</div>
      <div style="display:flex;flex-direction:column;gap:8px">
        <div class="g2" style="gap:4px"><div><div class="lbl">SPOT</div><input type="number" id="bsc-spot" placeholder="23900"></div><div><div class="lbl">STRIKE</div><input type="number" id="bsc-k" placeholder="24000"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">DTE</div><input type="number" id="bsc-dte" value="7"></div><div><div class="lbl">IV %</div><input type="number" id="bsc-iv" value="15"></div></div>
        <div class="g2" style="gap:4px"><div><div class="lbl">TYPE</div><select id="bsc-type"><option>CE</option><option>PE</option></select></div><div><div class="lbl">RATE %</div><input type="number" id="bsc-rate" value="6.5"></div></div>
        <button class="btn bmd bg" onclick="calcBS()" style="width:100%">◆ PRICE + GREEKS</button>
        <div id="bsc-result" style="display:none;background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px"></div>
      </div>
    </div>
  </div>
</div>

<!-- AI ENGINE PANEL -->
<div id="panel-ai" class="panel">
  <div class="g4">
    <div class="stat"><div class="slbl">ENGINE</div><div class="sval" id="ai-status" style="color:var(--gr);font-size:11px">LOADING</div></div>
    <div class="stat"><div class="slbl">SYNTHESIZED</div><div class="sval" id="ai-synth" style="color:var(--bl)">0</div></div>
    <div class="stat"><div class="slbl">APPROVED</div><div class="sval" id="ai-approved" style="color:var(--gr)">0</div></div>
    <div class="stat"><div class="slbl">SIGNALS TODAY</div><div class="sval" id="ai-signals" style="color:var(--am)">0</div></div>
  </div>
  <div class="card" style="border:1px solid var(--gr)20">
    <div class="card-hdr" style="color:var(--gr)">🤖 AUTONOMOUS AI ENGINE — Genetic Algorithm + LSTM + RL (PPO)</div>
    <div class="g2" style="gap:8px;margin-bottom:10px">
      <div class="card"><div style="font-size:8px;color:var(--mu);margin-bottom:8px">ARCHITECTURE</div>
        <div style="font-size:9px;display:flex;flex-direction:column;gap:5px">
          <div><span style="color:var(--gr)">🧬 </span>Genetic Algorithm — Strategy DNA Evolution</div>
          <div><span style="color:var(--bl)">🧠 </span>LSTM Neural Network — Pattern Discovery</div>
          <div><span style="color:var(--pu)">⚡ </span>RL (PPO/SAC) — Self-Optimization</div>
          <div><span style="color:var(--am)">📋 </span>15-Day Mandatory Paper Test</div>
          <div><span style="color:var(--rd)">🔴 </span>Circuit Breaker (VIX>35)</div>
        </div>
      </div>
      <div class="card"><div style="font-size:8px;color:var(--mu);margin-bottom:8px">APPROVAL GATES</div>
        <div style="font-size:9px;display:flex;flex-direction:column;gap:5px">
          <div><span style="color:var(--gr)">✓ </span>Min Win Rate: 62%</div>
          <div><span style="color:var(--gr)">✓ </span>Min Profit Factor: 1.5×</div>
          <div><span style="color:var(--gr)">✓ </span>15-day forward test</div>
          <div><span style="color:var(--am)">⚠ </span>Anti-overfit penalty</div>
          <div><span style="color:var(--rd)">■ </span>VIX>35 = Circuit Breaker</div>
        </div>
      </div>
    </div>
    <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:flex-end">
      <div><div class="lbl">INSTRUMENT</div><select id="ai-inst" style="width:130px"><option>NIFTY</option><option>BANKNIFTY</option><option>FINNIFTY</option></select></div>
      <div><div class="lbl">VIX</div><input type="number" id="ai-vix" value="19.5" step="0.5" style="width:80px"></div>
    </div>
    <div style="display:flex;gap:6px;flex-wrap:wrap">
      <button class="btn bmd bg" onclick="evolveStrategies()">🧬 EVOLVE (5 Gen)</button>
      <button class="btn bmd bb" onclick="getAISignal()">⚡ AI SIGNAL</button>
      <button class="btn bmd bp" onclick="detectRegime()">🔍 REGIME</button>
      <button class="btn bmd ba" onclick="loadAIStrategies()">★ VIEW ALL</button>
    </div>
  </div>
  <div id="ai-signal-box" style="display:none" class="card"></div>
  <div id="ai-regime-box" style="display:none" class="card"></div>
  <div id="ai-strat-list" style="display:flex;flex-direction:column;gap:8px"></div>
</div>

<!-- ADMIN PANEL -->
<div id="panel-admin" class="panel">
  <div style="display:flex;gap:6px;margin-bottom:4px">
    <button class="btn bmd bg" onclick="loadAdminDashboard()">↻ REFRESH</button>
    <button class="btn bmd bb" onclick="loadAuditLog()">🔐 AUDIT LOG</button>
    <button class="btn bmd ba" onclick="loadAdminUsers()">👥 USERS</button>
  </div>
  <div class="g4">
    <div class="stat"><div class="slbl">TOTAL USERS</div><div class="sval" id="adm-users" style="color:var(--bl)">—</div></div>
    <div class="stat"><div class="slbl">ACTIVE TODAY</div><div class="sval" id="adm-active" style="color:var(--gr)">—</div></div>
    <div class="stat"><div class="slbl">TOTAL REVENUE</div><div class="sval" id="adm-rev" style="color:var(--am);font-size:13px">—</div></div>
    <div class="stat"><div class="slbl">MRR</div><div class="sval" id="adm-mrr" style="color:var(--gr);font-size:13px">—</div></div>
    <div class="stat"><div class="slbl">TOTAL TRADES</div><div class="sval" id="adm-trades" style="color:var(--am)">—</div></div>
    <div class="stat"><div class="slbl">AI STRATEGIES</div><div class="sval" id="adm-ai" style="color:var(--pu)">—</div></div>
    <div class="stat"><div class="slbl">NEW THIS WEEK</div><div class="sval" id="adm-new" style="color:var(--cy)">—</div></div>
    <div class="stat"><div class="slbl">API STATUS</div><div class="sval" style="color:var(--gr);font-size:10px">ONLINE ●</div></div>
  </div>
  <div class="g2" style="gap:10px">
    <div class="card"><div class="card-hdr">FEATURE USAGE</div><div id="adm-features" style="font-size:9px;color:var(--mu)">Click REFRESH</div></div>
    <div class="card"><div class="card-hdr">PLAN DISTRIBUTION</div><div id="adm-plans" style="font-size:9px;color:var(--mu)">Click REFRESH</div></div>
  </div>
  <div class="card"><div class="card-hdr">🔐 SECURITY AUDIT LOG</div><div id="adm-audit" style="font-size:9px;max-height:160px;overflow-y:auto;color:var(--mu)">Click AUDIT LOG</div></div>
  <div class="card"><div class="card-hdr">👥 USERS</div><div style="overflow-x:auto"><table class="tbl"><thead><tr><th>USERNAME</th><th>EMAIL</th><th>PLAN</th><th>CAPITAL</th><th>LOGINS</th><th>LAST LOGIN</th></tr></thead><tbody id="adm-user-table"></tbody></table></div></div>
</div>

<!-- LEGAL PANEL -->
<div id="panel-legal" class="panel">
  <div style="display:flex;gap:6px;flex-wrap:wrap">
    <button class="btn bmd bg" onclick="showLegalDoc('tos')">📄 ToS</button>
    <button class="btn bmd bb" onclick="showLegalDoc('privacy')">🔒 Privacy</button>
    <button class="btn bmd br" onclick="showLegalDoc('risk_disclosure')">⚠ Risk</button>
    <button class="btn bmd ba" onclick="showLegalDoc('kyc_info')">🪪 KYC</button>
  </div>
  <div class="card" id="legal-doc-card"><div class="card-hdr">LEGAL DOCUMENTS</div><div style="color:var(--mu)">Select above</div></div>
  <div class="card">
    <div class="card-hdr" style="color:var(--rd)">⚠ RISK DISCLOSURE — DIGITAL SIGNATURE</div>
    <div style="background:#1a0008;border:1px solid var(--rd)30;border-radius:6px;padding:12px;margin-bottom:12px">
      <div style="color:var(--rd);font-weight:700;font-size:10px;margin-bottom:10px">Check all before trading:</div>
      <label style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;cursor:pointer;font-size:9px"><input type="checkbox" id="ck1" style="width:auto;margin-top:2px"><span>⚠️ I understand derivatives can result in TOTAL LOSS of capital</span></label>
      <label style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;cursor:pointer;font-size:9px"><input type="checkbox" id="ck2" style="width:auto;margin-top:2px"><span>⚠️ I trade with capital I can afford to lose completely</span></label>
      <label style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;cursor:pointer;font-size:9px"><input type="checkbox" id="ck3" style="width:auto;margin-top:2px"><span>⚠️ TRD is a TOOL — NOT a SEBI-registered advisor</span></label>
      <label style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px;cursor:pointer;font-size:9px"><input type="checkbox" id="ck4" style="width:auto;margin-top:2px"><span>⚠️ I accept full responsibility for trading decisions</span></label>
      <label style="display:flex;gap:10px;align-items:flex-start;cursor:pointer;font-size:9px"><input type="checkbox" id="ck5" style="width:auto;margin-top:2px"><span>✓ I have read Terms of Service and Privacy Policy</span></label>
    </div>
    <button class="btn blg br" onclick="signRiskDisclosure()">✍ DIGITALLY SIGN RISK DISCLOSURE</button>
    <div id="sig-box" style="display:none;margin-top:10px;background:#001a0e;border:1px solid var(--gr);border-radius:6px;padding:10px;font-size:9px"></div>
  </div>
</div>

<!-- PROFILE PANEL -->
<div id="panel-profile" class="panel">
  <div class="card" style="background:linear-gradient(135deg,var(--bg3),var(--bg4));border:1px solid var(--gr)20">
    <div style="display:flex;gap:14px;align-items:center;margin-bottom:14px">
      <div style="width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,var(--gr),var(--bl));display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;color:#000">D</div>
      <div style="flex:1">
        <div style="font-size:18px;font-weight:700">Demo Trader</div>
        <div style="font-size:9px;color:var(--mu);margin-top:2px">demo@trading.com</div>
        <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap">
          <span class="bdg" id="prof-plan-badge" style="border-color:var(--pu);background:#160a28;color:var(--pu)">PRO</span>
          <span class="bdg" style="border-color:var(--bl);background:#0a1628;color:var(--bl)">ZERODHA</span>
          <span class="bdg" style="border-color:var(--gr);background:#001a0e;color:var(--gr)">VERIFIED ✓</span>
        </div>
      </div>
      <div style="text-align:right">
        <div style="font-size:9px;color:var(--mu)">CAPITAL</div>
        <div style="font-size:22px;font-weight:700;color:var(--gr)">₹5.0L</div>
      </div>
    </div>
    <div class="g4" style="gap:6px;margin-bottom:12px">
      <div class="stat"><div class="slbl">STRATEGIES</div><div class="sval" id="prof-strats" style="color:var(--bl)">0</div></div>
      <div class="stat"><div class="slbl">TRADES</div><div class="sval" id="prof-trades" style="color:var(--am)">0</div></div>
      <div class="stat"><div class="slbl">P&L</div><div class="sval" id="prof-pnl" style="color:var(--gr)">₹0</div></div>
      <div class="stat"><div class="slbl">WIN RATE</div><div class="sval" id="prof-wr" style="color:var(--gr)">0%</div></div>
    </div>
    <div style="display:flex;gap:6px"><button class="btn bsm bg" onclick="refreshProfileStats()">↻ REFRESH</button></div>
  </div>
  <div style="display:flex;gap:0;border-bottom:1px solid var(--bo)">
    <button class="ptab active" onclick="switchProfileTab('settings',this)">⚙ SETTINGS</button>
    <button class="ptab" onclick="switchProfileTab('sub',this)">💳 PLANS</button>
    <button class="ptab" onclick="switchProfileTab('themes',this)">🎨 THEMES</button>
    <button class="ptab" onclick="switchProfileTab('notifs',this)">🔔 ALERTS</button>
  </div>
  <div id="prof-settings" class="card">
    <div class="g2" style="gap:8px;margin-bottom:8px"><div><div class="lbl">FULL NAME</div><input id="pf-name" placeholder="Your name"></div><div><div class="lbl">PHONE</div><input id="pf-phone" placeholder="+91 9876543210"></div></div>
    <div class="g2" style="gap:8px;margin-bottom:8px"><div><div class="lbl">CAPITAL ₹</div><input type="number" id="pf-capital" value="500000"></div><div><div class="lbl">RISK %</div><input type="number" id="pf-risk" value="1" step="0.5"></div></div>
    <div class="g2" style="gap:8px;margin-bottom:8px"><div><div class="lbl">MAX DAILY LOSS %</div><input type="number" id="pf-maxloss" value="3"></div><div><div class="lbl">BROKER</div><select id="pf-broker"><option>ZERODHA</option><option>ANGEL</option><option>FYERS</option></select></div></div>
    <div style="margin-bottom:8px"><div class="lbl">TELEGRAM CHAT ID</div><input id="pf-telegram" placeholder="123456789"></div>
    <div style="margin-bottom:10px"><div class="lbl">BIO</div><textarea id="pf-bio" rows="2" placeholder="About yourself as a trader..."></textarea></div>
    <button class="btn bmd bg" onclick="saveProfileSettings()" style="width:100%">✓ SAVE SETTINGS</button>
  </div>
  <div id="prof-sub" class="card" style="display:none">
    <div class="card-hdr">SUBSCRIPTION PLANS</div>
    <div class="g2" style="gap:8px;margin-bottom:10px">
      <div class="plan-card" id="pl-FREE" onclick="selectPlan('FREE',this)"><div style="font-weight:700">FREE</div><div style="font-size:22px;font-weight:700;color:var(--gr);margin:6px 0">₹0</div><div style="font-size:8px;color:var(--mu);text-align:left;line-height:1.8">✓ 3 Strategies<br>✓ 1 Month Backtest<br>✓ Paper Trading<br>✗ Scanner<br>✗ AI Engine</div></div>
      <div class="plan-card" id="pl-BASIC" onclick="selectPlan('BASIC',this)"><div style="font-weight:700;color:var(--bl)">BASIC</div><div style="font-size:22px;font-weight:700;color:var(--gr);margin:6px 0">₹499/mo</div><div style="font-size:8px;color:var(--mu);text-align:left;line-height:1.8">✓ 20 Strategies<br>✓ 6 Month Backtest<br>✓ Scanner<br>✓ 50 Alerts<br>✗ AI Engine</div></div>
      <div class="plan-card active" id="pl-PRO" onclick="selectPlan('PRO',this)"><div style="font-weight:700;color:var(--gr)">PRO ★</div><div style="font-size:22px;font-weight:700;color:var(--gr);margin:6px 0">₹1499/mo</div><div style="font-size:8px;color:var(--mu);text-align:left;line-height:1.8">✓ Unlimited All<br>✓ 12 Month BT<br>✓ AI Engine<br>✓ Live API<br>✓ Priority Support</div><div style="background:var(--gr);color:#000;font-size:8px;border-radius:3px;padding:2px 6px;display:inline-block;margin-top:4px">RECOMMENDED</div></div>
      <div class="plan-card" id="pl-INSTITUTIONAL" onclick="selectPlan('INSTITUTIONAL',this)"><div style="font-weight:700;color:var(--am)">INSTITUTIONAL</div><div style="font-size:22px;font-weight:700;color:var(--am);margin:6px 0">₹4999/mo</div><div style="font-size:8px;color:var(--mu);text-align:left;line-height:1.8">✓ Everything<br>✓ 5yr Backtest<br>✓ Multi-user<br>✓ White Label<br>✓ Dedicated</div></div>
    </div>
    <button class="btn blg bg" onclick="upgradePlan()">💳 UPGRADE PLAN</button>
  </div>
  <div id="prof-themes" class="card" style="display:none">
    <div class="card-hdr">🎨 THEMES</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
      <div class="th-card active" id="th-default" onclick="applyTheme('default',this)"><div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:#00ff88"></div><div style="width:16px;height:16px;border-radius:50%;background:#ff3355"></div><div style="width:16px;height:16px;border-radius:50%;background:#4f8ef7"></div></div><div style="font-size:10px;font-weight:700">DARK</div></div>
      <div class="th-card" id="th-midnight" onclick="applyTheme('midnight',this)"><div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:#00ffcc"></div><div style="width:16px;height:16px;border-radius:50%;background:#5555ff"></div></div><div style="font-size:10px;font-weight:700">MIDNIGHT</div></div>
      <div class="th-card" id="th-matrix" onclick="applyTheme('matrix',this)"><div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:#00ff44"></div><div style="width:16px;height:16px;border-radius:50%;background:#00cc88"></div></div><div style="font-size:10px;font-weight:700">MATRIX</div></div>
      <div class="th-card" id="th-purple" onclick="applyTheme('purple',this)"><div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:#a855f7"></div><div style="width:16px;height:16px;border-radius:50%;background:#f43f5e"></div></div><div style="font-size:10px;font-weight:700">COSMIC</div></div>
      <div class="th-card" id="th-solar" onclick="applyTheme('solar',this)"><div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:#859900"></div><div style="width:16px;height:16px;border-radius:50%;background:#268bd2"></div></div><div style="font-size:10px;font-weight:700">SOLARIZED</div></div>
      <div class="th-card" id="th-light" onclick="applyTheme('light',this)"><div style="display:flex;gap:4px;justify-content:center;margin-bottom:8px"><div style="width:16px;height:16px;border-radius:50%;background:#059669"></div><div style="width:16px;height:16px;border-radius:50%;background:#2563eb"></div></div><div style="font-size:10px;font-weight:700;color:#1e293b">LIGHT</div></div>
    </div>
  </div>
  <div id="prof-notifs" class="card" style="display:none">
    <div class="card-hdr">🔔 ALERT SETTINGS</div>
    <div style="display:flex;flex-direction:column;gap:6px">
      <label style="display:flex;justify-content:space-between;align-items:center;padding:10px;background:var(--bg4);border-radius:5px"><span style="font-size:10px">Trade Executed</span><input type="checkbox" id="na-trade" checked style="width:auto"></label>
      <label style="display:flex;justify-content:space-between;align-items:center;padding:10px;background:var(--bg4);border-radius:5px"><span style="font-size:10px">Stop Loss Hit</span><input type="checkbox" id="na-sl" checked style="width:auto"></label>
      <label style="display:flex;justify-content:space-between;align-items:center;padding:10px;background:var(--bg4);border-radius:5px"><span style="font-size:10px">Target Achieved</span><input type="checkbox" id="na-tgt" checked style="width:auto"></label>
      <label style="display:flex;justify-content:space-between;align-items:center;padding:10px;background:var(--bg4);border-radius:5px"><span style="font-size:10px">Scanner Signals</span><input type="checkbox" id="na-scan" style="width:auto"></label>
      <label style="display:flex;justify-content:space-between;align-items:center;padding:10px;background:var(--bg4);border-radius:5px"><span style="font-size:10px">Daily P&L Report</span><input type="checkbox" id="na-report" checked style="width:auto"></label>
      <button class="btn bmd bg" onclick="toast('Alert settings saved ✅','success')" style="width:100%;margin-top:4px">✓ SAVE</button>
    </div>
  </div>
</div>
</div><!-- /main -->

<!-- PWA INSTALL BANNER -->
<div id="install-banner">
  <div style="display:flex;align-items:center;justify-content:space-between">
    <div style="display:flex;align-items:center;gap:10px">
      <div style="width:36px;height:36px;background:linear-gradient(135deg,var(--gr),var(--bl));border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:900;color:#000">▶</div>
      <div>
        <div style="font-size:11px;font-weight:700;color:var(--gr)">Install TRD Pro App</div>
        <div style="font-size:9px;color:var(--mu)">Fast access • Works offline • Push alerts</div>
      </div>
    </div>
    <div style="display:flex;gap:8px">
      <button onclick="document.getElementById('install-banner').style.display='none'" style="background:none;border:1px solid var(--bo);color:var(--mu);border-radius:4px;padding:6px 10px;cursor:pointer;font-size:9px;font-family:inherit">Later</button>
      <button id="install-btn" onclick="installPWA()" class="btn bsm bg">⬇ INSTALL</button>
    </div>
  </div>
</div>

<!-- AI CUSTOMER CARE CHAT -->
<div id="chat-widget">
  <div id="chat-window">
    <!-- Chat Header -->
    <div class="chat-hdr">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,var(--gr),var(--bl));display:flex;align-items:center;justify-content:center;font-size:16px">🤖</div>
        <div>
          <div style="font-size:11px;font-weight:700;color:var(--gr)">TRD Support</div>
          <div style="font-size:8px;color:var(--mu)"><span style="color:var(--gr)">●</span> Online — AI + Human hybrid</div>
        </div>
      </div>
      <button onclick="toggleChat()" style="background:none;border:none;color:var(--mu);cursor:pointer;font-size:18px;padding:4px">✕</button>
    </div>
    <!-- Messages -->
    <div class="chat-msgs" id="chat-msgs">
      <div class="chat-msg bot">
        Namaste! 🙏 Main TRD Support hoon — aapki kaise madad kar sakta hoon?<br><br>
        <span style="color:var(--mu);font-size:9px">Trading guide, AI engine, subscription, ya koi bhi sawaal poochein! 😊</span>
      </div>
    </div>
    <!-- Typing indicator -->
    <div class="chat-typing" id="chat-typing" style="display:none">🤖 Typing...</div>
    <!-- Quick Suggestions -->
    <div class="chat-suggestions" id="chat-suggestions">
      <button class="chat-sugg" onclick="chatSend('How to place first trade?')">How to trade?</button>
      <button class="chat-sugg" onclick="chatSend('Plans & pricing')">💳 Plans</button>
      <button class="chat-sugg" onclick="chatSend('AI signals kaise kaam karte hain?')">🤖 AI Signals</button>
      <button class="chat-sugg" onclick="chatSend('App offline hai')">🔧 Offline fix</button>
    </div>
    <!-- Input -->
    <div class="chat-inp-wrap">
      <input id="chat-inp" placeholder="Apna sawaal type karo..." onkeypress="if(event.key==='Enter')chatSend()">
      <button class="chat-send" onclick="chatSend()">➤</button>
    </div>
  </div>
  <button id="chat-btn" onclick="toggleChat()">💬</button>
</div>

<!-- MOBILE BOTTOM NAV -->
<div id="bottom-nav">
  <button class="bnav-btn active" id="bn-trade" onclick="showPanel('trade',this);updateBottomNav('trade')">
    <span>◈</span><span>TRADE</span>
  </button>
  <button class="bnav-btn" id="bn-scanner" onclick="showPanel('scanner',this);updateBottomNav('scanner')">
    <span>◎</span><span>SCAN</span>
  </button>
  <button class="bnav-btn" id="bn-ai" onclick="showPanel('ai',this);updateBottomNav('ai')">
    <span>🤖</span><span>AI</span>
  </button>
  <button class="bnav-btn" id="bn-strategies" onclick="showPanel('strategies',this);updateBottomNav('strategies')">
    <span>★</span><span>STRATS</span>
  </button>
  <button class="bnav-btn" id="bn-profile" onclick="showPanel('profile',this);updateBottomNav('profile')">
    <span>👤</span><span>PROFILE</span>
  </button>
</div>

<script>
'use strict';
const API='http://13.53.175.88';

// Self-test connection on load
window.addEventListener('load', async()=>{
  try{
    const r = await fetch('http://13.53.175.88/stats', {
      method:'GET',
      mode:'cors', 
      cache:'no-cache',
      signal: AbortSignal.timeout(6000)
    });
    if(r.ok){
      const dot=$('api-dot');if(dot){dot.style.background='var(--gr)';dot.className='dot';}
      const lbl=$('api-lbl');if(lbl)lbl.textContent='ONLINE';
      const sb=$('src-bdg');if(sb)sb.textContent='LIVE ●';
      addLog('SUCCESS','✅ API Connected!');
      loadStats();fetchMarketData();
    }
  }catch(ex){
    addLog('ERROR','Connection failed: '+ex.message);
    // Show IP for manual test
    const lbl=$('api-lbl');if(lbl)lbl.textContent='ERROR';
  }
});  // localtunnel  // Same origin - no CORS needed!
const UID='USR124535215';
let MODE='PAPER',INST='NIFTY',ACTION='BUY',OPTTYPE='CE',KILL=false,SELPLAN='PRO';
let prices={NIFTY:23897,BANKNIFTY:56089,FINNIFTY:26141,SENSEX:76664,VIX:19.71,USDINR:94.2};
let changes={NIFTY:-1.14,BANKNIFTY:-.38,FINNIFTY:-.4,SENSEX:-1.29,VIX:6.04,USDINR:.14};
const fmt=n=>(n>=0?'₹+':'₹')+Math.round(n).toLocaleString('en-IN');
const r2=n=>Math.round(n*100)/100;
const now=()=>new Date().toLocaleTimeString('en-IN',{hour12:false});
const $=id=>document.getElementById(id);
const val=id=>{const e=$(id);return e?e.value:''};
const num=id=>parseFloat(val(id))||0;
const int=id=>parseInt(val(id))||0;

function toast(msg,type='info'){
  const t=$('toast'),c={success:'var(--gr)',error:'var(--rd)',info:'var(--bl)',warn:'var(--am)'};
  t.style.display='block';t.style.borderLeftColor=c[type]||c.info;t.innerHTML=msg;
  clearTimeout(t._t);t._t=setTimeout(()=>t.style.display='none',3500);
}
function addLog(type,msg){
  const b=$('log-box');if(!b)return;
  const c={SUCCESS:'var(--gr)',ERROR:'var(--rd)',INFO:'var(--am)',SYSTEM:'var(--bl)',WARN:'var(--pu)'};
  const d=document.createElement('div');d.className='log-line';
  d.innerHTML=`<span style="color:var(--mu);min-width:52px">${now()}</span><span style="color:${c[type]||'var(--mu)'};min-width:65px">[${type}]</span><span>${msg}</span>`;
  b.appendChild(d);b.scrollTop=b.scrollHeight;if(b.children.length>100)b.removeChild(b.firstChild);
}
async function api(url,method='GET',data=null){
  try{
    const o={method,headers:{
      'Content-Type':'application/json',
      'Accept':'application/json, text/html, */*',
      'Accept-Language':'en-IN,en;q=0.9',
      'Cache-Control':'no-cache',
      'Pragma':'no-cache',
    },credentials:'same-origin',signal:AbortSignal.timeout(10000)};
    if(data)o.body=JSON.stringify(data);
    const r=await fetch(API+url,o);if(!r.ok)throw new Error('HTTP '+r.status);return await r.json();
  }catch(e){addLog('ERROR',url+' — '+e.message);return null;}
}
setInterval(()=>{const e=$('clk');if(e)e.textContent=now()+' IST';},1000);

function showPanel(name,btn){
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(t=>t.classList.remove('active'));
  const p=$('panel-'+name);if(p)p.classList.add('active');
  if(btn&&btn.classList)btn.classList.add('active');
  if(name==='positions')loadPositions();
  if(name==='risk')loadRiskData();
  if(name==='journal'){loadTradeHistory();loadJournalStats();}
  if(name==='ai')loadAIStatus();
  if(name==='admin')loadAdminDashboard();
  if(name==='profile')refreshProfileStats();
}

async function fetchMarketData(){
  try{
    const r=await fetch(API+'/market/all',{credentials:'omit',headers:{'Accept':'application/json'},signal:AbortSignal.timeout(8000)});
    if(!r.ok)throw new Error();
    const d=await r.json();
    Object.keys(d.data||{}).forEach(k=>{if(d.data[k]?.price>0){prices[k]=d.data[k].price;if(d.data[k].pChange!==undefined)changes[k]=d.data[k].pChange;}});
    const s=$('src-bdg');if(s){s.textContent='LIVE ●';s.style.color='var(--gr)';}
    const dot=$('api-dot');if(dot)dot.style.background='var(--gr)';
    const lbl=$('api-lbl');if(lbl)lbl.textContent='ONLINE';
    const sl=$('src-label');if(sl)sl.textContent='YAHOO FINANCE LIVE';
  }catch{
    Object.keys(prices).forEach(k=>prices[k]=parseFloat((prices[k]*(1+(Math.random()-.5)*.0003)).toFixed(2)));
    const dot=$('api-dot');if(dot)dot.style.background='var(--rd)';
    const lbl=$('api-lbl');if(lbl)lbl.textContent='OFFLINE';
    const sl=$('src-label');if(sl)sl.textContent='SIMULATED';
  }
  renderTicker();renderMarketWatch();
}
function renderTicker(){
  const keys=['NIFTY','BANKNIFTY','SENSEX','FINNIFTY','VIX','USDINR'];
  const t=$('ticker');if(!t)return;
  t.innerHTML=[...keys,...keys].map(k=>{const up=(changes[k]||0)>=0;return `<span style="display:flex;gap:6px;align-items:center"><span style="color:var(--mu);font-size:8px">${k}</span><strong style="font-size:10px">${(prices[k]||0).toFixed(2)}</strong><span style="color:${up?'var(--gr)':'var(--rd)'};font-size:8px">${up?'▲':'▼'}${Math.abs(changes[k]||0).toFixed(2)}%</span></span>`;}).join('');
}
function renderMarketWatch(){
  const keys=['NIFTY','BANKNIFTY','FINNIFTY','SENSEX','VIX','USDINR'];
  const el=$('mkt-watch');if(!el)return;
  el.innerHTML=keys.map(k=>{const up=(changes[k]||0)>=0;return `<div style="background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:8px;text-align:center"><div style="font-size:7px;color:var(--mu);margin-bottom:2px">${k}</div><div style="font-size:12px;font-weight:700">${(prices[k]||0).toFixed(2)}</div><div style="font-size:8px;color:${up?'var(--gr)':'var(--rd)'};font-weight:700">${up?'▲':'▼'}${Math.abs(changes[k]||0).toFixed(2)}%</div></div>`;}).join('');
}
fetchMarketData();setInterval(fetchMarketData,30000);

async function loadStats(){
  const d=await api('/stats');if(!d)return;const p=d.performance||{};
  const set=(id,v,c)=>{const e=$(id);if(e){e.textContent=v;if(c)e.style.color=c;}};
  set('s-pnl',fmt(p.total_pnl||0),(p.total_pnl||0)>=0?'var(--gr)':'var(--rd)');
  set('s-pp',(p.total_pnl_pct||0)+'%',null);
  set('s-dp',fmt(p.daily_pnl||0),(p.daily_pnl||0)>=0?'var(--gr)':'var(--rd)');
  set('s-tc',(p.total_trades||0)+' trades',null);
  const wr=p.win_rate||0;set('s-wr',wr+'%',wr>=60?'var(--gr)':wr>=40?'var(--am)':'var(--rd)');
  set('s-wl',(p.winning_trades||0)+'W / '+(p.losing_trades||0)+'L',null);
  set('s-cap','₹'+((p.capital||500000)/100000).toFixed(1)+'L','var(--bl)');
  set('s-dd','Drawdown: '+(p.max_drawdown_pct||0)+'%',null);
  set('j-pf',p.profit_factor||'0',null);set('j-aw',fmt(p.avg_win||0),null);
  set('j-al',fmt(p.avg_loss||0),null);set('j-ex',fmt(p.expectancy||0),null);
  set('prof-trades',p.total_trades||0,null);
  set('prof-pnl',fmt(p.total_pnl||0),(p.total_pnl||0)>=0?'var(--gr)':'var(--rd)');
  set('prof-wr',(p.win_rate||0)+'%',null);
}
loadStats();setInterval(loadStats,20000);

function setMode(m,btn){MODE=m;document.querySelectorAll('[id^="m-"]').forEach(b=>b.className='tog');if(btn)btn.className='tog tb';const mb=$('mode-bdg');if(mb)mb.textContent=m;updateExecBtn();}
function setInst(i,btn){INST=i;document.querySelectorAll('[id^="bi-"]').forEach(b=>b.className='tog');if(btn)btn.className='tog ta';updateExecBtn();}
function setAction(a){ACTION=a;$('ba-BUY').className='tog'+(a==='BUY'?' tg':'');$('ba-SELL').className='tog'+(a==='SELL'?' tr':'');updateExecBtn();}
function setType(t){OPTTYPE=t;['CE','PE','FUT'].forEach(x=>{$('bt-'+x).className='tog'+(x===t?' tb':'');});updateExecBtn();}
function updateExecBtn(){const b=$('exec-btn');if(!b)return;b.textContent='▶ EXECUTE '+ACTION+' '+INST+' '+OPTTYPE;b.className='btn blg '+(ACTION==='BUY'?'bg':'br');}

async function executeTrade(){
  const entry_price=num('f-price')||100,lots=int('f-lots')||1;
  const sl=num('f-sl'),tgt=num('f-tgt'),trail=num('f-trail'),strike=int('f-strike');
  const rm={};if(sl)rm.stoploss_points=sl;if(tgt)rm.target_points=tgt;if(trail)rm.trailing_sl=trail;
  addLog('INFO','Sending '+ACTION+' '+INST+' '+OPTTYPE+'@'+entry_price);
  const r=await api('/trade','POST',{instrument:INST,action:ACTION,option_type:OPTTYPE,strike,expiry:val('f-expiry')||'WEEKLY',quantity:lots,entry_price,confidence:.92,risk_metrics:rm,broker:'ZERODHA',mode:MODE});
  if(r){
    if(r.status==='EXECUTED'){
      addLog('SUCCESS','EXECUTED → '+(r.position_id||'').slice(-6));
      loadStats();toast(ACTION+' '+INST+' '+OPTTYPE+' EXECUTED ✅','success');
      const tb=$('exec-rows');if(tb){const row=document.createElement('tr');row.innerHTML=`<td style="color:var(--mu)">${(r.position_id||'').slice(-6)}</td><td style="font-weight:700">${INST}</td><td style="color:var(--bl)">${OPTTYPE}</td><td style="color:var(--am)">${strike||'ATM'}</td><td>${lots}</td><td style="color:var(--gr)">${entry_price}</td><td style="color:var(--rd)">${sl||'—'}</td><td style="color:var(--gr)">${tgt||'—'}</td><td style="color:${ACTION==='BUY'?'var(--gr)':'var(--rd)'};font-weight:700">${ACTION}</td><td><span style="color:var(--gr);font-size:8px">● OPEN</span></td>`;tb.insertBefore(row,tb.firstChild);}
    }else{addLog('ERROR','REJECTED: '+(r.reason||''));toast('Rejected: '+(r.reason||'Unknown'),'error');}
  }
}

async function nlpParse(){
  const text=val('nlp-input').trim();if(!text){toast('Type a strategy','warn');return;}
  const r=await api('/strategy','POST',{text});if(!r)return;
  const out=$('nlp-output');if(out){out.style.display='block';out.innerHTML=Object.entries(r).filter(([k,v])=>v&&k!=='timestamp').slice(0,10).map(([k,v])=>`<span style="display:inline-flex;gap:3px;margin:2px;background:var(--bg);border:1px solid var(--bo);border-radius:3px;padding:2px 6px;font-size:8px"><span style="color:var(--mu)">${k}:</span><b>${typeof v==='object'?JSON.stringify(v):v}</b></span>`).join('');}
  if(r.instrument)setInst(r.instrument,$('bi-'+r.instrument)||document.createElement('div'));
  if(r.action)setAction(r.action);if(r.option_type)setType(r.option_type);
  if(r.quantity&&$('f-lots'))$('f-lots').value=r.quantity;
  if(r.risk_metrics){if(r.risk_metrics.stoploss_points&&$('f-sl'))$('f-sl').value=r.risk_metrics.stoploss_points;if(r.risk_metrics.target_points&&$('f-tgt'))$('f-tgt').value=r.risk_metrics.target_points;if(r.risk_metrics.trailing_sl&&$('f-trail'))$('f-trail').value=r.risk_metrics.trailing_sl;}
  if(r.strike&&!Array.isArray(r.strike)&&$('f-strike'))$('f-strike').value=r.strike;
  addLog('SUCCESS','NLP: '+r.instrument+' '+r.action+' '+r.option_type+' conf:'+r.confidence);
  toast('Order entry auto-filled ✅','success');
}
async function nlpExecute(){await nlpParse();await executeTrade();}

async function loadPositions(){
  const d=await api('/positions');if(!d)return;
  const tb=$('pos-table');
  if(!d.positions||!d.positions.length){if(tb)tb.innerHTML='<tr><td colspan="11" style="text-align:center;color:var(--mu);padding:20px">No open positions</td></tr>';}
  else{if(tb)tb.innerHTML=d.positions.map(p=>{const c=p.pnl>=0?'var(--gr)':'var(--rd)';return `<tr><td style="color:var(--mu)">${(p.id||'').slice(-6)}</td><td style="font-weight:700">${p.instrument||''}</td><td style="color:var(--bl)">${p.option_type||''}</td><td style="color:var(--am)">${p.strike||'—'}</td><td>${p.quantity||1}</td><td style="color:var(--gr)">${p.entry_price||0}</td><td>${p.current_price||0}</td><td style="color:var(--rd)">${p.stoploss||'—'}</td><td style="color:var(--gr)">${p.target||'—'}</td><td style="color:${c};font-weight:700">${fmt(p.pnl||0)}</td><td><button class="btn bsm br" onclick="closePos('${p.id}',${p.current_price||0})">✕</button></td></tr>`;}).join('');}
  if($('p-open'))$('p-open').textContent=d.count||0;
  const up=(d.positions||[]).reduce((s,p)=>s+(p.pnl||0),0);
  const ue=$('p-upnl');if(ue){ue.textContent=fmt(up);ue.style.color=up>=0?'var(--gr)':'var(--rd)';}
}
async function closePos(id,cur){const p=parseFloat(prompt('Exit price?',cur)||0);if(!p)return;const r=await api('/trade/close','POST',{position_id:id,exit_price:p,reason:'MANUAL'});if(r){addLog('SUCCESS','Closed: '+fmt(r.net_pnl||0));loadPositions();loadStats();}}
async function closeAllPositions(){if(!confirm('Close ALL?'))return;const d=await api('/positions');if(!d)return;for(const p of(d.positions||[]))await api('/trade/close','POST',{position_id:p.id,exit_price:p.current_price||0,reason:'CLOSE_ALL'});loadPositions();loadStats();toast('All closed','success');}

async function loadRiskData(){
  const d=await api('/stats');if(!d)return;const r=d.risk||{};
  const st=$('r-status');if(st){st.textContent='● '+(r.risk_status||'GREEN');st.style.color=r.risk_status==='GREEN'?'var(--gr)':r.risk_status==='YELLOW'?'var(--am)':'var(--rd)';}
  if($('r-dloss'))$('r-dloss').textContent='₹'+(r.daily_loss||0);
  if($('r-dlosspct'))$('r-dlosspct').textContent=(r.daily_loss_used_pct||0)+'% used';
  const rdd=$('r-dd');if(rdd){rdd.textContent=(r.current_drawdown_pct||0)+'%';rdd.style.color=(r.current_drawdown_pct||0)>5?'var(--rd)':'var(--gr)';}
  const rcl=$('r-cl');if(rcl){rcl.textContent=r.consecutive_losses||0;rcl.style.color=(r.consecutive_losses||0)>2?'var(--rd)':'var(--am)';}
  const dlp=r.daily_loss_used_pct||0;const pb=$('pb-dl');if(pb){pb.style.width=Math.min(dlp,100)+'%';pb.style.background=dlp>70?'var(--rd)':dlp>40?'var(--am)':'var(--gr)';}
  if($('rm-dl'))$('rm-dl').textContent=dlp.toFixed(1)+'% / 3%';
  const ddp=(r.current_drawdown_pct||0)*10;const pbd=$('pb-dd');if(pbd)pbd.style.width=Math.min(ddp,100)+'%';
  if($('rm-dd'))$('rm-dd').textContent=(r.current_drawdown_pct||0)+'% / 10%';
  const posp=((r.open_positions||0)/5)*100;const pbp=$('pb-pos');if(pbp)pbp.style.width=posp+'%';
  if($('rm-pos'))$('rm-pos').textContent=(r.open_positions||0)+' / 5';
  const trdp=((r.trades_today||0)/10)*100;const pbt=$('pb-trd');if(pbt)pbt.style.width=trdp+'%';
  if($('rm-trd'))$('rm-trd').textContent=(r.trades_today||0)+' / 10';
}
function calcPositionSize(){const cap=num('ps-cap')||500000,risk=num('ps-risk')||1,sl=num('ps-sl')||100,lot=int('ps-lot')||50;const lots=Math.max(1,Math.floor(cap*risk/100/(sl*lot)));const out=$('ps-result');if(!out)return;out.style.display='block';out.innerHTML=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px"><div><div class="slbl">OPTIMAL LOTS</div><div style="font-size:22px;font-weight:700;color:var(--gr)">${lots}</div></div><div><div class="slbl">RISK AMOUNT</div><div style="font-size:16px;font-weight:700;color:var(--rd)">₹${(lots*sl*lot).toLocaleString('en-IN')}</div></div><div><div class="slbl">REWARD (2:1)</div><div style="color:var(--gr)">₹${(lots*sl*2*lot).toLocaleString('en-IN')}</div></div><div><div class="slbl">CAPITAL RISK</div><div style="color:var(--am)">${risk}%</div></div></div>`;}
async function toggleKill(){const ns=!KILL;if(ns&&!confirm('⚠️ KILL SWITCH?\\nAll trading will stop!'))return;const d=await api('/risk/kill_switch?active='+ns,'POST');if(d!==null){KILL=ns;const btn=$('kill-btn');if(btn){btn.textContent=ns?'▶ RESUME':'■ KILL';btn.className='btn bsm '+(ns?'bg':'br');}const mb=$('mode-bdg');if(ns&&mb){mb.textContent='KILLED';mb.style.background='#1a0008';mb.style.color='var(--rd)';}else if(mb)mb.textContent=MODE;toast(ns?'⚠️ KILL SWITCH ON':'✅ Trading Resumed',ns?'error':'success');}}
async function resumeTrading(){await api('/risk/kill_switch?active=false','POST');KILL=false;toast('Trading resumed ✅','success');}
async function resetPaper(){if(!confirm('Reset paper engine?'))return;const c=parseFloat(prompt('Capital:','500000'))||500000;await api('/paper/reset?capital='+c,'POST');toast('Paper reset ₹'+c.toLocaleString('en-IN'),'success');loadStats();}

async function runScanner(){const out=$('scanner-out');if(out)out.innerHTML='<div style="color:var(--am);padding:20px;text-align:center">⏳ Scanning...</div>';const d=await api('/scanner/run');if(!d||!d.opportunities||!d.opportunities.length){if(out)out.innerHTML='<div style="color:var(--mu);padding:20px;text-align:center">No signals now</div>';return;}if(out)out.innerHTML=d.opportunities.slice(0,10).map(o=>`<div style="display:flex;align-items:center;gap:10px;padding:9px;border-bottom:1px solid var(--bo)"><span style="color:var(--am);min-width:110px;font-weight:700;font-size:10px">${o.instrument}</span><span style="min-width:35px;color:${o.action==='BUY'?'var(--gr)':'var(--rd)'};font-weight:700">${o.action}</span><span style="color:var(--mu);flex:1;font-size:9px">${o.strategy}</span><span style="background:var(--bg4);border:1px solid var(--bo);border-radius:10px;padding:2px 8px;font-size:8px;color:var(--bl)">${((o.confidence||0)*100).toFixed(0)}%</span><button class="btn bsm ${o.action==='BUY'?'bg':'br'}" onclick="scannerFill('${o.instrument}','${o.action}','${o.option_type||'CE'}')">USE</button></div>`).join('');}
function scannerFill(inst,action,opt){setInst(inst,$('bi-'+inst)||document.createElement('div'));setAction(action);setType(opt||'CE');showPanel('trade',null);toast(inst+' '+action+' loaded ✅','success');}
async function getIVRank(){const d=await api('/iv/rank/'+val('iv-inst')+'?current_iv='+(num('iv-val')||15));const out=$('iv-out');if(!out)return;out.style.display='block';if(!d){out.innerHTML='<span style="color:var(--rd)">Failed</span>';return;}const c=d.iv_rank>70?'var(--rd)':d.iv_rank<30?'var(--gr)':'var(--am)';out.innerHTML=`<div style="font-size:16px;font-weight:700;color:${c};margin-bottom:6px">${d.regime||'—'}</div><div style="font-size:10px">IV Rank: <span style="color:${c};font-weight:700">${d.iv_rank||0}%</span></div><div style="font-size:9px;color:var(--mu);margin-top:4px">→ ${d.recommendation||''}</div><div style="font-size:9px;color:var(--bl);margin-top:4px">Strategy: ${d.signal||''}</div>`;}
async function getFIIDII(){const d=await api('/fii_dii');const out=$('fii-out');if(!out)return;if(!d){out.textContent='Failed';return;}out.innerHTML=`<div>FII: <span style="color:${d.fii?.activity==='BUYING'?'var(--gr)':'var(--rd)'};font-weight:700">${d.fii?.activity||'—'}</span></div><div style="margin-top:4px">DII: <span style="color:${d.dii?.activity==='BUYING'?'var(--gr)':'var(--rd)'};font-weight:700">${d.dii?.activity||'—'}</span></div><div style="margin-top:4px;color:var(--mu)">${d.market_impact||''}</div>`;}
async function getExpiryData(){const d=await api('/reports/expiry_calendar');const out=$('expiry-out');if(!out)return;if(!d){out.textContent='Failed';return;}const wc=d.days_to_weekly<=2?'var(--rd)':d.days_to_weekly<=5?'var(--am)':'var(--gr)';out.innerHTML=`<div>Weekly: <span style="color:${wc};font-weight:700">${d.nifty_weekly_expiry||'—'}</span> (${d.days_to_weekly||0}d)</div><div style="margin-top:4px">Monthly: <span style="color:var(--bl);font-weight:700">${d.nifty_monthly_expiry||'—'}</span> (${d.days_to_monthly||0}d)</div><div style="margin-top:6px;color:${wc};font-weight:700;font-size:10px">${d.theta_warning||''}</div>`;}

async function loadOptionsChain(){const d=await api('/market/options_chain_live/'+val('ch-inst')+'?dte='+(int('ch-dte')||7));const tb=$('chain-table');if(!tb)return;if(!d||!d.chain){tb.innerHTML='<tr><td colspan="9" style="color:var(--mu);padding:10px;text-align:center">Load failed</td></tr>';return;}tb.innerHTML=d.chain.map(s=>{const atm=s.moneyness==='ATM';return `<tr style="${atm?'background:rgba(245,158,11,.08);':''}"><td style="color:var(--mu)">${((s.CE?.oi||0)/1000).toFixed(0)}K</td><td style="color:var(--gr);font-weight:${atm?700:400}">${s.CE?.price||0}</td><td style="color:var(--bl)">${s.CE?.delta||0}</td><td style="color:var(--rd)">${s.CE?.theta||0}</td><td style="background:var(--bg4);text-align:center;font-weight:700;color:${atm?'var(--am)':'var(--tx)'}">${s.strike}</td><td style="color:var(--rd)">${s.PE?.theta||0}</td><td style="color:var(--bl)">${s.PE?.delta||0}</td><td style="color:var(--rd);font-weight:${atm?700:400}">${s.PE?.price||0}</td><td style="color:var(--mu)">${((s.PE?.oi||0)/1000).toFixed(0)}K</td></tr>`;}).join('');}

function normCDF(x){const t=1/(1+.2316419*Math.abs(x));const d=.3989423*Math.exp(-x*x/2);const p=d*t*(.3193815+t*(-.3565638+t*(1.7814779+t*(-1.821256+t*1.3302744))));return x>0?1-p:p;}
function bsp(S,K,T,v,r,type){if(!S||!K||!T||!v)return null;const t=T/365,sig=v/100,rf=r/100;const d1=(Math.log(S/K)+(rf+sig*sig/2)*t)/(sig*Math.sqrt(t)),d2=d1-sig*Math.sqrt(t);let price,delta;if(type==='CE'){price=S*normCDF(d1)-K*Math.exp(-rf*t)*normCDF(d2);delta=normCDF(d1);}else{price=K*Math.exp(-rf*t)*normCDF(-d2)-S*normCDF(-d1);delta=normCDF(d1)-1;}const gamma=Math.exp(-d1*d1/2)/(S*sig*Math.sqrt(2*Math.PI*t));const theta=(-(S*sig*Math.exp(-d1*d1/2))/(2*Math.sqrt(2*Math.PI*t))-rf*K*Math.exp(-rf*t)*(type==='CE'?normCDF(d2):normCDF(-d2)))/365;const vega=S*Math.sqrt(t)*Math.exp(-d1*d1/2)/Math.sqrt(2*Math.PI)/100;return{price,delta,gamma,theta,vega};}
function calcGreeks(){const res=bsp(num('bs-spot'),num('bs-strike'),num('bs-dte'),num('bs-iv'),num('bs-rate'),val('bs-type'));const out=$('greeks-out');if(!out)return;if(!res){out.style.display='block';out.innerHTML='<span style="color:var(--rd)">Fill all fields</span>';return;}out.style.display='block';out.innerHTML=`<div style="font-size:20px;font-weight:700;color:var(--gr);margin-bottom:10px">₹${res.price.toFixed(2)}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:10px"><div><span style="color:var(--mu)">Δ: </span><span style="color:var(--bl);font-weight:700">${res.delta.toFixed(4)}</span></div><div><span style="color:var(--mu)">Γ: </span><span style="color:var(--pu)">${res.gamma.toFixed(6)}</span></div><div><span style="color:var(--mu)">θ/day: </span><span style="color:var(--rd);font-weight:700">₹${(res.theta*100).toFixed(2)}</span></div><div><span style="color:var(--mu)">ν/1%: </span><span style="color:var(--cy);font-weight:700">₹${(res.vega*100).toFixed(2)}</span></div></div>`;}
async function calcMargin(){const d=await api('/margin/calculate?instrument='+val('mg-inst')+'&quantity='+val('mg-lots')+'&position_type='+val('mg-type')+'&price='+(val('mg-price')||100));const out=$('margin-out');if(!out)return;out.style.display='block';if(!d){out.innerHTML='<span style="color:var(--rd)">Server offline</span>';return;}out.innerHTML=`<div>Required: <span style="color:var(--rd);font-size:16px;font-weight:700">₹${(d.margin_required||0).toLocaleString('en-IN')}</span></div><div style="font-size:9px;color:var(--mu);margin-top:4px">Contract: ₹${(d.total_lots_value||0).toLocaleString('en-IN')}</div><div style="font-size:9px;color:var(--gr);margin-top:4px">Max lots ₹5L: ${d.max_lots_with_5L||0}</div>`;}

async function runBacktest(){
  const btn=$('bt-btn');if(btn){btn.textContent='⏳ Running...';btn.disabled=true;}
  const d=await api('/backtest/advanced','POST',{strategy:val('bt-strategy'),capital:num('bt-capital')||100000,months:int('bt-months')||3,quantity:int('bt-lots')||1,sl_pct:1,target_pct:2});
  if(btn){btn.textContent='∞ RUN BACKTEST + DATE-WISE CALENDAR';btn.disabled=false;}
  if(!d||d.error)return;
  const out=$('bt-result');if(!out)return;out.style.display='block';
  const cap=d.capital_invested||100000,pc=d.total_pnl>=0?'var(--gr)':'var(--rd)';
  let html=`<div class="g4" style="gap:6px;margin-bottom:12px">
    <div class="stat"><div class="slbl">TOTAL P&L</div><div class="sval" style="color:${pc};font-size:14px">₹${(d.total_pnl||0).toLocaleString('en-IN')}</div><div class="ssub">${d.total_pnl_pct||0}%</div></div>
    <div class="stat"><div class="slbl">FINAL CAPITAL</div><div class="sval" style="color:var(--bl);font-size:13px">₹${(d.final_capital||0).toLocaleString('en-IN')}</div></div>
    <div class="stat"><div class="slbl">WIN RATE</div><div class="sval" style="color:var(--am)">${d.win_rate||0}%</div><div class="ssub">${d.winning_trades||0}W/${d.losing_trades||0}L</div></div>
    <div class="stat"><div class="slbl">MAX DRAWDOWN</div><div class="sval" style="color:var(--rd)">${d.max_drawdown_pct||0}%</div></div>
    <div class="stat"><div class="slbl">PROFIT DAYS</div><div class="sval" style="color:var(--gr)">${d.profitable_days||0}</div></div>
    <div class="stat"><div class="slbl">LOSS DAYS</div><div class="sval" style="color:var(--rd)">${d.loss_days||0}</div></div>
    <div class="stat"><div class="slbl">PROFIT FACTOR</div><div class="sval" style="color:var(--bl)">${d.profit_factor||0}</div></div>
    <div class="stat"><div class="slbl">SHARPE</div><div class="sval" style="color:var(--pu)">${d.sharpe_ratio||0}</div></div>
  </div>`;
  if(d.monthly_summary?.length){html+=`<div class="card" style="margin-bottom:10px"><div class="card-hdr">MONTHLY BREAKDOWN</div><div style="display:flex;gap:8px;flex-wrap:wrap">${d.monthly_summary.map(m=>`<div style="flex:1;min-width:90px;background:var(--bg4);border:2px solid ${m.pnl>=0?'var(--gr)':'var(--rd)'};border-radius:6px;padding:10px;text-align:center"><div style="font-size:9px;color:var(--mu)">${m.month}</div><div style="font-size:16px;font-weight:700;color:${m.pnl>=0?'var(--gr)':'var(--rd)'}">₹${(m.pnl||0).toLocaleString('en-IN')}</div><div style="font-size:8px;color:var(--mu)">${m.trades||0}T | ${m.win_rate||0}%WR</div></div>`).join('')}</div></div>`;}
  html+=`<div class="g2" style="gap:10px;margin-bottom:10px"><div class="card"><div class="card-hdr" style="color:var(--gr)">🏆 BEST DAYS</div>${[...(d.best_days||[])].reverse().map(day=>`<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--bo);font-size:9px"><span style="color:var(--mu)">${day.date}</span><span style="color:var(--gr);font-weight:700">₹${(day.pnl||0).toLocaleString('en-IN')}</span></div>`).join('')}</div><div class="card"><div class="card-hdr" style="color:var(--rd)">📉 WORST DAYS</div>${(d.worst_days||[]).map(day=>`<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--bo);font-size:9px"><span style="color:var(--mu)">${day.date}</span><span style="color:var(--rd);font-weight:700">₹${(day.pnl||0).toLocaleString('en-IN')}</span></div>`).join('')}</div></div>`;
  html+=`<div class="card"><div class="card-hdr">📅 DATE-WISE P&L — Capital: ₹${cap.toLocaleString('en-IN')}</div><div style="display:flex;flex-wrap:wrap;gap:3px;max-height:240px;overflow-y:auto">${(d.daily_results||[]).map(r=>`<div class="cal-cell" style="background:${r.pnl>0?'rgba(0,255,136,.15)':r.pnl<0?'rgba(255,51,85,.15)':'var(--bg4)'};border-color:${r.pnl>0?'rgba(0,255,136,.35)':r.pnl<0?'rgba(255,51,85,.35)':'var(--bo)'}" title="${r.date}: ₹${r.pnl}" onclick="alert('${r.date}\\\\nP&L: ₹${r.pnl}\\\\nTrades: ${r.trades}\\\\nCumulative: ₹${r.cumulative}')"><div style="color:var(--mu)">${(r.date||'').slice(5)}</div><div style="font-weight:700;color:${r.pnl>0?'var(--gr)':r.pnl<0?'var(--rd)':'var(--mu)'}">${Math.abs(r.pnl||0)>999?Math.round((r.pnl||0)/1000)+'k':Math.round(r.pnl||0)||'—'}</div></div>`).join('')}</div><div style="display:flex;gap:14px;margin-top:8px;font-size:8px;color:var(--mu)"><span>🟢 Profitable</span><span>🔴 Loss</span><span>⬛ No trade</span></div></div>`;
  out.innerHTML=html;
}

function toggleNLPBuilder(){const el=$('nlp-builder');if(el)el.style.display=el.style.display==='none'?'block':'none';}
async function parseNLPStrategy(){const text=val('nlp-strat-input').trim();if(!text){toast('Type strategy first','warn');return;}const r=await api('/strategies/from_nlp','POST',{user_id:UID,nlp_text:text});if(!r)return;const s=r.strategy||{},p=r.parsed||{};if(s.name&&$('ns-name'))$('ns-name').value=s.name;if(p.instrument&&$('ns-inst'))$('ns-inst').value=p.instrument;if(s.entry_conditions&&$('ns-entry'))$('ns-entry').value=(s.entry_conditions||[]).join('\\n');if(s.exit_conditions&&$('ns-exit'))$('ns-exit').value=(s.exit_conditions||[]).join('\\n');if(s.sl_value&&$('ns-sl'))$('ns-sl').value=s.sl_value;if(s.target_value&&$('ns-tgt'))$('ns-tgt').value=s.target_value;if(s.quantity&&$('ns-lots'))$('ns-lots').value=s.quantity;if(s.tags&&$('ns-tags'))$('ns-tags').value=(s.tags||[]).join(',');const box=$('nlp-strat-parsed');if(box){box.style.display='block';box.innerHTML='◆ PARSED: '+Object.entries(p).filter(([,v])=>v).slice(0,8).map(([k,v])=>`<span style="margin-right:10px">${k}: <b>${typeof v==='object'?JSON.stringify(v):v}</b></span>`).join('');}toast('Fields auto-filled ✅','success');}
async function saveMyStrategy(){const entry=(val('ns-entry')||'').split('\\n').filter(l=>l.trim()),exit_c=(val('ns-exit')||'').split('\\n').filter(l=>l.trim()),tags=(val('ns-tags')||'').split(',').map(t=>t.trim()).filter(t=>t);const d=await api('/strategies/save','POST',{user_id:UID,name:val('ns-name')||'My Strategy',instrument:val('ns-inst')||'NIFTY',timeframe:val('ns-tf')||'15MIN',entry_conditions:entry,exit_conditions:exit_c,sl_value:num('ns-sl')||100,target_value:num('ns-tgt')||200,quantity:int('ns-lots')||1,tags,nlp_input:val('nlp-strat-input')});if(d&&d.strategy_id){toast('Strategy saved ✅','success');$('nlp-builder').style.display='none';loadMyStrategies();}else toast('Save failed','error');}
function backtestMyStrategy(){$('bt-strategy').value='EMA_CROSS';showPanel('backtest',null);}
async function loadBuiltinStrategies(){const d=await api('/strategies/builtin');const list=$('strat-list');if(!list)return;if(!d||!d.strategies){list.innerHTML='<div style="color:var(--rd);padding:20px">Failed to load</div>';return;}list.innerHTML=d.strategies.map(s=>`<div class="card" style="border-left:3px solid ${s.avg_win_rate>=70?'var(--gr)':s.avg_win_rate>=65?'var(--am)':'var(--bl)'}"><div style="display:flex;justify-content:space-between;margin-bottom:8px"><div><div style="font-size:12px;font-weight:700">${s.name}</div><div style="font-size:8px;color:var(--mu)">${s.instrument||''} | ${s.type||''}</div></div><div style="text-align:right"><div style="font-size:18px;font-weight:700;color:${s.avg_win_rate>=70?'var(--gr)':'var(--am)'}">${s.avg_win_rate}%</div><div style="font-size:8px;color:var(--bl)">${s.avg_monthly_return}%/mo | DD:${s.max_drawdown}%</div></div></div><div style="font-size:9px;color:var(--mu);margin-bottom:8px">${s.description}</div>${s.notes?`<div style="font-size:8px;color:var(--am);margin-bottom:8px;padding:6px;background:#1a0e00;border-radius:4px">💡 ${s.notes}</div>`:''}<div style="display:flex;gap:6px"><button class="btn bsm bg" onclick="$('bt-strategy').value='${s.id}';showPanel('backtest',null)">∞ BT</button><button class="btn bsm bb" onclick="setInst('${(s.instrument||'NIFTY').split('/')[0]}',document.createElement('div'));showPanel('trade',null)">USE</button></div></div>`).join('');}
async function loadMyStrategies(){const d=await api('/strategies/user/'+UID);const list=$('strat-list');if(!list)return;const strats=d?.user_strategies||[];if(!strats.length){list.innerHTML=`<div style="text-align:center;padding:30px;color:var(--mu)">No saved strategies yet<br><br><button class="btn bmd bg" onclick="toggleNLPBuilder()">◆ CREATE WITH NLP</button></div>`;return;}list.innerHTML=strats.map(s=>`<div class="card" style="border-left:3px solid var(--bl)"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><div style="font-size:12px;font-weight:700">${s.name}</div><button class="btn bsm br" onclick="deleteStrategy('${s.id}')">✕</button></div><div style="font-size:9px;color:var(--mu)">${s.instrument} | ${s.timeframe} | SL:${s.sl_value}→TGT:${s.target_value}</div>${s.nlp_input?`<div style="font-size:8px;color:var(--bl);font-style:italic;margin-top:4px">"${(s.nlp_input||'').slice(0,70)}..."</div>`:''}<div style="display:flex;gap:6px;margin-top:8px"><button class="btn bsm bg" onclick="$('bt-strategy').value='${s.id}';showPanel('backtest',null)">∞ BT</button><button class="btn bsm bb" onclick="setInst('${s.instrument}',document.createElement('div'));showPanel('trade',null)">USE</button></div></div>`).join('');}
async function deleteStrategy(sid){if(!confirm('Delete?'))return;await api('/strategies/'+sid+'?user_id='+UID,'DELETE');loadMyStrategies();}

async function saveJournalEntry(){const d=await api('/journal/add','POST',{instrument:val('jn-inst'),pnl:num('jn-pnl'),emotion:val('jn-emotion'),rating:int('jn-rating')||7,mistakes:val('jn-mistakes'),lessons:val('jn-lessons'),notes:''});if(d&&d.id){toast('Journal saved #'+d.id+' ✅','success');['jn-mistakes','jn-lessons'].forEach(id=>{const e=$(id);if(e)e.value='';});}else toast('Save failed','error');}
async function loadTradeHistory(){const d=await api('/trades');const tb=$('trades-table');if(!tb)return;if(!d||!d.trades||!d.trades.length){tb.innerHTML='<tr><td colspan="7" style="text-align:center;color:var(--mu);padding:20px">No trades yet</td></tr>';return;}tb.innerHTML=[...d.trades].reverse().map(t=>{const c=(t.net_pnl||0)>=0?'var(--gr)':'var(--rd)';return `<tr><td style="color:var(--mu)">${(t.id||'').slice(-6)}</td><td style="font-weight:700">${t.instrument||'—'}</td><td style="color:${t.action==='BUY'?'var(--gr)':'var(--rd)'};font-weight:700">${t.action||'—'}</td><td>${t.entry_price||0}</td><td>${t.exit_price||0}</td><td style="color:var(--am)">${t.exit_reason||'—'}</td><td style="color:${c};font-weight:700">${fmt(t.net_pnl||0)}</td></tr>`;}).join('');}
async function loadJournalStats(){const d=await api('/stats');if(!d||!d.performance)return;const p=d.performance;if($('j-pf'))$('j-pf').textContent=p.profit_factor||'0';if($('j-aw'))$('j-aw').textContent=fmt(p.avg_win||0);if($('j-al'))$('j-al').textContent=fmt(p.avg_loss||0);if($('j-ex'))$('j-ex').textContent=fmt(p.expectancy||0);}

async function getReport(type){const d=await api('/reports/'+type);const title=$('report-title'),body=$('report-body');if(title)title.textContent=type.toUpperCase()+' REPORT';if(!d){if(body)body.innerHTML='<span style="color:var(--rd)">Failed</span>';return;}const p=(type==='daily'&&d.summary)?d.summary:d;const pnl=p.net_pnl||p.total_pnl||0;if(body)body.innerHTML=`<div class="g4" style="gap:6px;margin-bottom:10px"><div class="stat"><div class="slbl">TRADES</div><div class="sval" style="color:var(--am)">${p.total_trades||0}</div></div><div class="stat"><div class="slbl">WIN RATE</div><div class="sval" style="color:var(--gr)">${p.win_rate||0}%</div></div><div class="stat"><div class="slbl">NET P&L</div><div class="sval" style="color:${pnl>=0?'var(--gr)':'var(--rd)'};font-size:13px">₹${Math.round(pnl).toLocaleString('en-IN')}</div></div><div class="stat"><div class="slbl">PROFIT FACTOR</div><div class="sval" style="color:var(--bl)">${p.profit_factor||0}</div></div></div>`;}
async function getExpiryReport(){const d=await api('/reports/expiry_calendar');const title=$('report-title'),body=$('report-body');if(title)title.textContent='EXPIRY CALENDAR';if(!d){if(body)body.innerHTML='<span style="color:var(--rd)">Failed</span>';return;}const wc=d.days_to_weekly<=2?'var(--rd)':d.days_to_weekly<=5?'var(--am)':'var(--gr)';if(body)body.innerHTML=`<div class="g2" style="gap:8px;margin-bottom:10px"><div class="stat"><div class="slbl">WEEKLY</div><div class="sval" style="color:${wc};font-size:13px">${d.nifty_weekly_expiry||'—'}</div><div class="ssub">${d.days_to_weekly||0} days</div></div><div class="stat"><div class="slbl">MONTHLY</div><div class="sval" style="color:var(--bl);font-size:13px">${d.nifty_monthly_expiry||'—'}</div><div class="ssub">${d.days_to_monthly||0} days</div></div></div><div style="padding:12px;background:var(--bg4);border-left:3px solid ${wc};border-radius:5px;font-size:11px;font-weight:700;color:${wc}">${d.theta_warning||''}</div>`;}

function calcRR(){const en=num('rr-entry'),sl=num('rr-sl'),tg=num('rr-target'),lots=int('rr-lots')||1,ls=int('rr-lotsize')||50,cap=num('rr-capital')||500000;if(!en||!sl||!tg){toast('Fill Entry, SL, Target','warn');return;}const slp=Math.abs(en-sl),tgp=Math.abs(tg-en),risk=slp*lots*ls,reward=tgp*lots*ls;const out=$('rr-result');if(!out)return;out.style.display='block';out.innerHTML=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px"><div><div class="slbl">SL PTS</div><div style="font-size:18px;font-weight:700;color:var(--rd)">${slp}</div></div><div><div class="slbl">TGT PTS</div><div style="font-size:18px;font-weight:700;color:var(--gr)">${tgp}</div></div><div><div class="slbl">RISK ₹</div><div style="color:var(--rd);font-weight:700">₹${Math.round(risk).toLocaleString('en-IN')}</div></div><div><div class="slbl">REWARD ₹</div><div style="color:var(--gr);font-weight:700">₹${Math.round(reward).toLocaleString('en-IN')}</div></div></div><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px"><div class="stat"><div class="slbl">R:R</div><div style="color:var(--bl);font-size:14px;font-weight:700">1:${r2(tgp/slp)}</div></div><div class="stat"><div class="slbl">MIN WIN%</div><div style="color:var(--am);font-weight:700">${r2(slp/(slp+tgp)*100)}%</div></div><div class="stat"><div class="slbl">CAP RISK</div><div style="color:var(--am)">${r2(risk/cap*100)}%</div></div><div class="stat"><div class="slbl">EXPECT</div><div style="color:${.5*reward-.5*risk>=0?'var(--gr)':'var(--rd)'}">₹${Math.round(.5*reward-.5*risk).toLocaleString('en-IN')}</div></div></div>`;}
function calcBS(){const res=bsp(num('bsc-spot'),num('bsc-k'),num('bsc-dte'),num('bsc-iv'),num('bsc-rate'),val('bsc-type'));const out=$('bsc-result');if(!out)return;if(!res){out.style.display='block';out.innerHTML='<span style="color:var(--rd)">Fill all fields</span>';return;}out.style.display='block';out.innerHTML=`<div style="font-size:22px;font-weight:700;color:var(--gr);margin-bottom:10px">₹${res.price.toFixed(2)}</div><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:10px"><div><span style="color:var(--mu)">Δ: </span><span style="color:var(--bl);font-weight:700">${res.delta.toFixed(4)}</span></div><div><span style="color:var(--mu)">Γ: </span><span style="color:var(--pu)">${res.gamma.toFixed(6)}</span></div><div><span style="color:var(--mu)">θ/day: </span><span style="color:var(--rd);font-weight:700">₹${(res.theta*100).toFixed(2)}</span></div><div><span style="color:var(--mu)">ν/1%: </span><span style="color:var(--cy);font-weight:700">₹${(res.vega*100).toFixed(2)}</span></div></div>`;}

async function loadAIStatus(){const d=await api('/ai/status');if(!d)return;if($('ai-status'))$('ai-status').textContent=d.status||'RUNNING';if($('ai-synth'))$('ai-synth').textContent=d.total_strategies_synthesized||0;if($('ai-approved'))$('ai-approved').textContent=d.approved_strategies||0;if($('ai-signals'))$('ai-signals').textContent=d.signals_today||0;}
async function evolveStrategies(){toast('🧬 Evolving...','info');const btn=document.querySelector('[onclick="evolveStrategies()"]');if(btn){btn.textContent='⏳...';btn.disabled=true;}const d=await api('/ai/evolve?generations=5','POST');if(btn){btn.textContent='🧬 EVOLVE (5 Gen)';btn.disabled=false;}if(d)toast('✅ Evolved '+d.evolved+' strategies!','success');loadAIStrategies();loadAIStatus();}
async function getAISignal(){const inst=val('ai-inst')||'NIFTY';const d=await api('/ai/signal/'+inst);const box=$('ai-signal-box');if(!box)return;box.style.display='block';if(!d){box.innerHTML='<div style="color:var(--rd)">Failed</div>';return;}const sc=d.signal==='WAIT'?'var(--mu)':d.signal?.includes('BUY')?'var(--gr)':'var(--rd)';box.innerHTML=`<div class="card-hdr" style="color:var(--gr)">⚡ AI SIGNAL — ${inst}</div><div class="g4" style="gap:8px;margin-bottom:10px"><div class="stat"><div class="slbl">SIGNAL</div><div class="sval" style="color:${sc};font-size:14px">${d.signal||'WAIT'}</div></div><div class="stat"><div class="slbl">CONFIDENCE</div><div class="sval" style="color:var(--bl)">${((d.confidence||0)*100).toFixed(1)}%</div></div><div class="stat"><div class="slbl">REGIME</div><div class="sval" style="color:var(--pu);font-size:10px">${d.regime||'—'}</div></div><div class="stat"><div class="slbl">PATTERN</div><div class="sval" style="color:var(--am);font-size:10px">${d.hidden_pattern||'—'}</div></div></div><div style="background:var(--bg4);border:1px solid var(--bo);border-radius:5px;padding:10px;font-size:9px;margin-bottom:8px">Entry: <b>₹${d.entry_price||0}</b> &nbsp;SL: <b style="color:var(--rd)">₹${d.stoploss||0}</b> &nbsp;Target: <b style="color:var(--gr)">₹${d.target||0}</b></div><div style="font-size:9px;color:var(--gr);margin-bottom:10px">💡 ${d.recommended_strategy||''}</div>${d.circuit_breaker?'<div style="color:var(--rd);font-size:10px;font-weight:700;padding:8px;background:#1a0008;border-radius:5px;margin-bottom:8px">⚠ CIRCUIT BREAKER ACTIVE</div>':''}<div style="display:flex;gap:6px"><button class="btn bmd bg" style="flex:1" onclick="useAISignal('${d.signal||''}',${d.entry_price||0},${d.stoploss||0},${d.target||0})">▶ USE</button><button class="btn bmd bb" style="flex:1" onclick="getAISignal()">↻ REFRESH</button></div>`;}
function useAISignal(sig,entry,sl,tgt){if(!sig||sig==='WAIT'){toast('No actionable signal','warn');return;}if(sig.includes('BUY_CE')){setAction('BUY');setType('CE');}else if(sig.includes('BUY_PE')){setAction('BUY');setType('PE');}else if(sig.includes('SELL_CE')){setAction('SELL');setType('CE');}else if(sig.includes('SELL_PE')){setAction('SELL');setType('PE');}if(entry&&$('f-price'))$('f-price').value=entry;if(sl&&$('f-sl'))$('f-sl').value=sl;if(tgt&&$('f-tgt'))$('f-tgt').value=tgt;showPanel('trade',null);toast('AI signal loaded ✅','success');}
async function detectRegime(){const vix=num('ai-vix')||19.5;const d=await api('/ai/regime?vix='+vix);const box=$('ai-regime-box');if(!box)return;box.style.display='block';if(!d){box.innerHTML='<div style="color:var(--rd)">Failed</div>';return;}const rc={'TRENDING_UP':'var(--gr)','TRENDING_DOWN':'var(--rd)','RANGEBOUND':'var(--am)','HIGH_VOLATILITY':'var(--rd)','EXTREME_VOLATILITY':'var(--rd)','ULTRA_LOW_VOL':'var(--bl)'};const c=rc[d.regime]||'var(--mu)';box.innerHTML=`<div class="card-hdr" style="color:var(--pu)">🔍 HIDDEN MARKET REGIME</div><div class="g4" style="gap:8px;margin-bottom:10px"><div class="stat"><div class="slbl">REGIME</div><div class="sval" style="color:${c};font-size:11px">${d.regime||'—'}</div></div><div class="stat"><div class="slbl">VIX</div><div class="sval" style="color:var(--am)">${d.vix||0}</div></div><div class="stat"><div class="slbl">MOMENTUM</div><div class="sval" style="color:${(d.momentum||0)>0?'var(--gr)':'var(--rd)'}">${d.momentum||0}%</div></div><div class="stat"><div class="slbl">CONFIDENCE</div><div class="sval" style="color:var(--bl)">${((d.confidence||0)*100).toFixed(0)}%</div></div></div><div style="background:var(--bg4);border-left:3px solid ${c};border-radius:5px;padding:12px;margin-bottom:8px"><div style="font-size:9px;color:var(--mu);margin-bottom:4px">HIDDEN PATTERN</div><div style="font-size:14px;font-weight:700;color:${c}">${d.hidden_pattern||'—'}</div></div><div style="background:#001a0e;border:1px solid var(--gr)30;border-radius:5px;padding:10px;font-size:9px"><span style="color:var(--mu)">Recommended: </span><span style="color:var(--gr);font-weight:700">${d.recommended_strategy||''}</span></div>`;}
async function loadAIStrategies(){const d=await api('/ai/strategies');const list=$('ai-strat-list');if(!list)return;if(!d||!d.strategies||!d.strategies.length){list.innerHTML='<div style="color:var(--mu);padding:20px;text-align:center">No strategies yet<br><br><button class="btn bmd bg" onclick="evolveStrategies()">🧬 EVOLVE NOW</button></div>';return;}list.innerHTML=d.strategies.slice(0,8).map(s=>`<div class="card" style="border-left:3px solid ${s.status==='APPROVED'?'var(--gr)':s.status==='PAPER_TEST'?'var(--am)':'var(--rd)'}"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px"><div style="font-size:11px;font-weight:700">${s.name}</div><span style="font-size:8px;padding:2px 10px;border-radius:10px;border:1px solid;background:${s.status==='APPROVED'?'#001a0e':s.status==='PAPER_TEST'?'#1a0e00':'#1a0008'};color:${s.status==='APPROVED'?'var(--gr)':s.status==='PAPER_TEST'?'var(--am)':'var(--rd)'}">● ${s.status}</span></div><div class="g4" style="gap:6px;margin-bottom:8px"><div class="stat"><div class="slbl">WIN RATE</div><div style="font-size:14px;font-weight:700;color:${(s.win_rate||0)>=.62?'var(--gr)':'var(--rd)'}">${((s.win_rate||0)*100).toFixed(1)}%</div></div><div class="stat"><div class="slbl">PF</div><div style="font-size:14px;font-weight:700;color:var(--bl)">${s.profit_factor||0}</div></div><div class="stat"><div class="slbl">SHARPE</div><div style="font-size:14px;font-weight:700;color:var(--pu)">${s.sharpe_ratio||0}</div></div><div class="stat"><div class="slbl">MAX DD</div><div style="font-size:14px;font-weight:700;color:var(--rd)">${s.max_drawdown||0}%</div></div></div>${s.status==='PAPER_TEST'?`<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:8px;margin-bottom:3px"><span style="color:var(--mu)">Paper Test</span><span style="color:var(--am)">${s.paper_test_days||0}/15 days</span></div><div class="pb"><div class="pf" style="width:${Math.min(((s.paper_test_days||0)/15)*100,100)}%;background:var(--am)"></div></div></div><button class="btn bsm ba" onclick="advancePaperTest('${s.id}')">+1 Day</button>`:''}</div>`).join('');}
async function advancePaperTest(sid){const d=await api('/ai/paper_test/'+sid+'?days=1','POST');if(!d)return;toast('Paper day '+(d.paper_days||0)+'/15 — '+(((d.paper_wr||0)*100).toFixed(1))+'% WR — '+d.status,'info');loadAIStrategies();}

async function loadAdminDashboard(){const d=await api('/admin/dashboard');if(!d){toast('Admin failed','error');return;}const sets={'adm-users':d.total_users||0,'adm-active':d.active_today||0,'adm-rev':'₹'+(d.total_revenue||0).toLocaleString('en-IN'),'adm-mrr':'₹'+(d.mrr||0).toLocaleString('en-IN'),'adm-trades':d.total_trades||0,'adm-ai':d.ai_strategies_synthesized||0,'adm-new':d.new_this_week||0};Object.entries(sets).forEach(([k,v])=>{const el=$(k);if(el)el.textContent=v;});const feat=$('adm-features');if(feat&&d.top_features)feat.innerHTML=d.top_features.map(f=>`<div style="margin-bottom:8px"><div style="display:flex;justify-content:space-between;font-size:9px;margin-bottom:3px"><span>${f.feature}</span><span style="color:var(--gr);font-weight:700">${f.usage_pct}%</span></div><div class="pb"><div class="pf" style="width:${f.usage_pct}%;background:var(--gr)"></div></div></div>`).join('');const plans=$('adm-plans');if(plans&&d.plan_distribution){const pc={FREE:'var(--mu)',BASIC:'var(--bl)',PRO:'var(--gr)',INSTITUTIONAL:'var(--am)'};plans.innerHTML=Object.entries(d.plan_distribution).map(([p,c])=>`<div style="display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--bo);font-size:9px"><span style="color:${pc[p]||'var(--mu)'}">● ${p}</span><span style="font-weight:700">${c} users</span></div>`).join('');}toast('Refreshed ✅','success');}
async function loadAuditLog(){const d=await api('/security/audit?limit=30');const el=$('adm-audit');if(!el)return;if(!d||!d.logs||!d.logs.length){el.innerHTML='<div style="color:var(--mu);padding:10px">No logs</div>';return;}el.innerHTML=d.logs.map(l=>`<div style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid var(--bo)"><span style="color:var(--mu);min-width:130px;font-size:8px">${(l.timestamp||'').slice(0,16)}</span><span style="min-width:65px;font-size:8px;color:${l.status==='SUCCESS'?'var(--gr)':'var(--rd)'}">● ${l.status}</span><span style="min-width:110px;font-size:8px;color:var(--am)">${l.action||''}</span><span style="font-size:8px;color:var(--mu)">${l.resource||''}</span></div>`).join('');}
async function loadAdminUsers(){const d=await api('/admin/users');const tb=$('adm-user-table');if(!tb)return;if(!d||!d.users||!d.users.length){tb.innerHTML='<tr><td colspan="6" style="color:var(--mu);padding:10px;text-align:center">No users</td></tr>';return;}const pc={FREE:'var(--mu)',BASIC:'var(--bl)',PRO:'var(--gr)',INSTITUTIONAL:'var(--am)'};tb.innerHTML=d.users.map(u=>`<tr><td style="font-weight:700">${u.username||'—'}</td><td style="color:var(--mu)">${u.email||'—'}</td><td style="color:${pc[u.subscription_plan||'FREE']};font-weight:700">${u.subscription_plan||'FREE'}</td><td style="color:var(--gr)">₹${(u.capital||0).toLocaleString('en-IN')}</td><td style="color:var(--am)">${u.login_count||0}</td><td style="color:var(--mu);font-size:8px">${(u.last_login||'—').slice(0,10)}</td></tr>`).join('');}

async function showLegalDoc(type){const d=await api('/legal/'+type);const card=$('legal-doc-card');if(!card)return;if(!d){card.innerHTML='<div class="card-hdr">ERROR</div><div style="color:var(--rd)">Failed to load</div>';return;}let html='<div class="card-hdr">'+type.toUpperCase().replace(/_/g,' ')+'</div>';if(d.title)html+=`<div style="font-size:14px;font-weight:700;color:var(--gr);margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--bo)">${d.title}</div>`;if(d.sections)html+=d.sections.map(s=>`<div style="margin-bottom:12px;padding:10px;background:var(--bg4);border-radius:5px;border-left:3px solid var(--am)"><div style="font-size:10px;font-weight:700;color:var(--am);margin-bottom:6px">${s.heading}</div><div style="font-size:9px;color:var(--mu);line-height:1.8">${s.content}</div></div>`).join('');if(d.warnings)html+=d.warnings.map(w=>`<div style="font-size:9px;color:var(--rd);margin-bottom:5px;padding:5px 10px;background:#1a0008;border-radius:4px">${w}</div>`).join('');card.innerHTML=html;}
async function signRiskDisclosure(){const all=['ck1','ck2','ck3','ck4','ck5'].every(id=>{const e=$(id);return e&&e.checked;});if(!all){toast('Check ALL boxes first','error');return;}const d=await api('/legal/consent?user_id='+UID+'&consent_type=risk_disclosure&version=1.0','POST');const box=$('sig-box');if(!box)return;box.style.display='block';box.innerHTML=`<div style="color:var(--gr);font-size:12px;font-weight:700;margin-bottom:6px">✅ DIGITALLY SIGNED</div><div style="font-size:9px;color:var(--mu)">Signature: <code style="color:var(--bl)">${((d?.digital_signature||'offline_'+Date.now()).slice(0,48))}...</code></div><div style="font-size:9px;color:var(--mu)">Time: ${new Date().toLocaleString('en-IN')}</div>`;toast('Risk disclosure signed ✅','success');}

function switchProfileTab(tab,btn){['settings','sub','themes','notifs'].forEach(t=>{const el=$('prof-'+t);if(el)el.style.display=t===tab?'block':'none';});document.querySelectorAll('.ptab').forEach(b=>b.classList.remove('active'));if(btn)btn.classList.add('active');}
async function refreshProfileStats(){const d=await api('/stats');if(!d)return;const p=d.performance||{};if($('prof-trades'))$('prof-trades').textContent=p.total_trades||0;if($('prof-pnl')){$('prof-pnl').textContent=fmt(p.total_pnl||0);$('prof-pnl').style.color=(p.total_pnl||0)>=0?'var(--gr)':'var(--rd)';}if($('prof-wr'))$('prof-wr').textContent=(p.win_rate||0)+'%';const sc=await api('/strategies/user/'+UID);if(sc&&$('prof-strats'))$('prof-strats').textContent=sc.user_strategies?.length||0;}
async function saveProfileSettings(){const d=await api('/users/'+UID,'PUT',{full_name:val('pf-name'),capital:num('pf-capital')||500000,risk_per_trade:num('pf-risk')||1,max_daily_loss:num('pf-maxloss')||3,broker:val('pf-broker'),telegram_chat_id:val('pf-telegram'),bio:val('pf-bio')});if(d&&d.updated)toast('Profile saved ✅','success');else toast('Save failed','error');}
function selectPlan(p,el){SELPLAN=p;document.querySelectorAll('.plan-card').forEach(c=>{c.classList.remove('active');c.style.borderColor='var(--bo)';});if(el){el.classList.add('active');el.style.borderColor='var(--gr)';}toast('Plan: '+p,'info');}
async function upgradePlan(){const d=await api('/subscriptions/upgrade','POST',{user_id:UID,plan:SELPLAN,payment_id:'SIM_'+Date.now()});if(d&&d.upgraded){toast('Upgraded to '+SELPLAN+' ✅','success');if($('prof-plan-badge'))$('prof-plan-badge').textContent=SELPLAN;if($('plan-bdg'))$('plan-bdg').textContent=SELPLAN;}else toast('Upgrade failed','error');}
function applyTheme(name,btn){document.getElementById('body').className='th-'+name;localStorage.setItem('theme',name);document.querySelectorAll('.th-card').forEach(c=>c.classList.remove('active'));if(btn)btn.classList.add('active');toast('Theme: '+name.toUpperCase()+' ✅','success');}


// ═══════════════════════════════════════════════════════
// PWA — SERVICE WORKER + INSTALL
// ═══════════════════════════════════════════════════════
let deferredPrompt = null;

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/trading-server/sw.js').then(reg => {
    addLog('SYSTEM', 'PWA Service Worker registered ✅');
  }).catch(err => addLog('WARN', 'SW: ' + err.message));
}

window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredPrompt = e;
  const banner = document.getElementById('install-banner');
  if (banner) banner.style.display = 'block';
});

window.addEventListener('appinstalled', () => {
  const banner = document.getElementById('install-banner');
  if (banner) banner.style.display = 'none';
  toast('TRD Pro installed! 🎉', 'success');
  deferredPrompt = null;
});

function installPWA() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(r => {
      if (r.outcome === 'accepted') toast('Installing TRD Pro... 🚀', 'success');
      deferredPrompt = null;
      document.getElementById('install-banner').style.display = 'none';
    });
  } else {
    toast('To install: Browser menu → Add to Home Screen', 'info');
  }
}

// Push notification request
async function requestNotifications() {
  if ('Notification' in window) {
    const perm = await Notification.requestPermission();
    if (perm === 'granted') {
      toast('Notifications enabled ✅', 'success');
      addLog('SYSTEM', 'Push notifications granted');
    }
  }
}

// ═══════════════════════════════════════════════════════
// AI CUSTOMER CARE CHAT
// ═══════════════════════════════════════════════════════
let chatOpen = false;
let chatNotifCount = 0;

function toggleChat() {
  chatOpen = !chatOpen;
  const win = document.getElementById('chat-window');
  if (win) {
    if (chatOpen) win.classList.add('open');
    else win.classList.remove('open');
  }
  chatNotifCount = 0;
  updateChatBadge();
}

function updateChatBadge() {
  const btn = document.getElementById('chat-btn');
  if (!btn) return;
  const existing = btn.querySelector('.notif-badge');
  if (existing) existing.remove();
  if (chatNotifCount > 0) {
    const badge = document.createElement('div');
    badge.className = 'notif-badge';
    badge.style.position = 'absolute';
    badge.textContent = chatNotifCount;
    btn.style.position = 'relative';
    btn.appendChild(badge);
  }
}

function addChatMsg(text, role='bot') {
  const msgs = document.getElementById('chat-msgs');
  if (!msgs) return;
  const div = document.createElement('div');
  div.className = 'chat-msg ' + role;
  // Format markdown-like text
  const formatted = text
    .replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>')
    .replace(/\\*(.*?)\\*/g, '<i>$1</i>')
    .replace(/
/g, '<br>')
    .replace(/\\| (.*?) \\| (.*?) \\| (.*?) \\|/g, '<div style="display:flex;gap:8px;font-size:8px;margin:2px 0"><span style="min-width:120px">$1</span><span style="min-width:60px">$2</span><span>$3</span></div>');
  div.innerHTML = formatted;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function updateSuggestions(suggestions) {
  const box = document.getElementById('chat-suggestions');
  if (!box || !suggestions || !suggestions.length) return;
  box.innerHTML = suggestions.map(s =>
    `<button class="chat-sugg" onclick="chatSend('${s.replace(/'/g,"\\'")}')">${s}</button>`
  ).join('');
}

async function chatSend(overrideMsg) {
  const inp = document.getElementById('chat-inp');
  const msg = overrideMsg || (inp ? inp.value.trim() : '');
  if (!msg) return;
  if (inp && !overrideMsg) inp.value = '';
  
  addChatMsg(msg, 'user');
  
  const typing = document.getElementById('chat-typing');
  if (typing) typing.style.display = 'block';
  
  // Small delay for natural feel
  await new Promise(r => setTimeout(r, 400 + Math.random() * 600));
  
  const result = await api('/support/chat', 'POST', {
    user_id: UID || 'guest',
    message: msg,
    user_name: 'Friend'
  });
  
  if (typing) typing.style.display = 'none';
  
  if (result && result.response) {
    addChatMsg(result.response, 'bot');
    if (result.suggestions) updateSuggestions(result.suggestions);
  } else {
    addChatMsg('Abhi server se connect nahi ho pa raha. Thoda wait karke dobara try karo! 🙏', 'bot');
  }
  
  if (!chatOpen) {
    chatNotifCount++;
    updateChatBadge();
  }
}

// Auto greeting after 30 sec
setTimeout(() => {
  if (!chatOpen) {
    chatNotifCount = 1;
    updateChatBadge();
  }
}, 30000);

// ═══════════════════════════════════════════════════════
// MOBILE BOTTOM NAV
// ═══════════════════════════════════════════════════════
function updateBottomNav(active) {
  document.querySelectorAll('.bnav-btn').forEach(b => {
    b.classList.toggle('active', b.id === 'bn-' + active);
  });
}

// ═══════════════════════════════════════════════════════
// SMART NOTIFICATIONS
// ═══════════════════════════════════════════════════════
function showSystemNotif(title, body, type='info') {
  // In-app toast
  toast(`<b>${title}</b><br><span style="font-size:9px">${body}</span>`, type);
  // Browser notification if permitted
  if (Notification.permission === 'granted') {
    new Notification(title, {
      body,
      icon: '/trading-server/icons/icon-192.png',
      badge: '/trading-server/icons/icon-72.png',
      tag: 'trd-' + type,
      vibrate: [200, 100, 200]
    });
  }
}

// Monitor for trade events and send notifications
const origExecuteTrade = typeof executeTrade === 'function' ? executeTrade : null;

// INIT
(function(){const t=localStorage.getItem('theme');if(t&&t!=='default'){const b=document.getElementById('body');if(b)b.className='th-'+t;const tc=document.getElementById('th-'+t);if(tc){document.querySelectorAll('.th-card').forEach(c=>c.classList.remove('active'));tc.classList.add('active');}}})();
addLog('SYSTEM','TRD v12.3 initialized — http://13.53.175.88');
addLog('INFO','Connecting to server...');

// Immediate connect with retry
async function connectWithRetry(){
  let tries=0;
  while(tries<10){
    try{
      const r=await fetch(API+'/stats',{signal:AbortSignal.timeout(5000)});
      if(r.ok){
        const d=await r.json();
        const dot=$('api-dot');if(dot)dot.style.background='var(--gr)';
        const lbl=$('api-lbl');if(lbl)lbl.textContent='ONLINE';
        const sb=$('src-bdg');if(sb){sb.textContent='LIVE ●';sb.style.color='var(--gr)';}
        addLog('SUCCESS','Connected! Server online');
        loadStats();fetchMarketData();
        return;
      }
    }catch(e){
      tries++;
      addLog('WARN','Retry '+tries+'/10...');
      await new Promise(r=>setTimeout(r,2000));
    }
  }
  addLog('ERROR','Cannot connect - check server');
}

connectWithRetry();
setInterval(loadStats,20000);
setInterval(fetchMarketData,30000);
setInterval(()=>{const a=document.querySelector('.panel.active');if(a?.id==='panel-risk')loadRiskData();if(a?.id==='panel-positions')loadPositions();},15000);
</script></body></html>
"""

from starlette.middleware.base import BaseHTTPMiddleware


# Force disable Cloudflare browser integrity check via response headers
@app.middleware("http")
async def disable_cf_browser_check(request, call_next):
    response = await call_next(request)
    # These headers tell Cloudflare to skip browser check
    response.headers["CF-Cache-Status"] = "DYNAMIC"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Vary"] = "Accept-Encoding"
    return response

class NoCFCheckMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        return response

app.add_middleware(NoCFCheckMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

paper_engine = PaperTradingEngine(capital=500000)
risk_manager = RiskManager()

# ── System log (event-driven) ────────────────────────────
system_log = []

def log_handler(event: Event):
    system_log.append({
        "time": event.timestamp,
        "type": event.data.get("type", "INFO"),
        "msg": event.data.get("msg", ""),
        "source": event.source,
    })
    if len(system_log) > 500:
        system_log.pop(0)

if EVENT_DRIVEN:
    bus.subscribe(EventType.LOG, log_handler)
    bus.emit(EventType.SYSTEM_START, {"msg": "Trading System v12.3 started"}, source="MAIN")

# ═══════════════════════════════════════
# NLP DATA
# ═══════════════════════════════════════
INSTRUMENTS={"nifty 50":"NIFTY","nifty50":"NIFTY","nifty":"NIFTY","nf":"NIFTY","निफ्टी":"NIFTY",
    "bank nifty":"BANKNIFTY","banknifty":"BANKNIFTY","bnf":"BANKNIFTY","बैंकनिफ्टी":"BANKNIFTY",
    "fin nifty":"FINNIFTY","finnifty":"FINNIFTY","fn":"FINNIFTY",
    "midcap nifty":"MIDCPNIFTY","midcap":"MIDCPNIFTY",
    "sensex":"SENSEX","सेंसेक्स":"SENSEX",
    "reliance":"RELIANCE","tcs":"TCS","hdfc":"HDFCBANK","infosys":"INFY","icici":"ICICIBANK",
    "usdinr":"USDINR","crude":"CRUDEOIL","gold":"GOLD",
}
LOT_SIZES={"NIFTY":50,"BANKNIFTY":15,"FINNIFTY":40,"MIDCPNIFTY":75,"SENSEX":10}
BUY_WORDS=["buy","long","bullish","call buy","entry","enter","accumulate","kharido","le lo","lelo","lo","खरीदो","badhega","upar"]
SELL_WORDS=["sell","short","bearish","put buy","exit","close","square off","becho","bech","niklo","nikal","बेचो","girega","neeche"]
OPTION_TYPES={"call":"CE","ce":"CE","कॉल":"CE","put":"PE","pe":"PE","पुट":"PE"}
STRATEGIES={
    "short straddle":"SHORT_STRADDLE","long straddle":"LONG_STRADDLE","atm straddle":"ATM_STRADDLE","straddle":"STRADDLE",
    "short strangle":"SHORT_STRANGLE","long strangle":"LONG_STRANGLE","otm strangle":"OTM_STRANGLE","strangle":"STRANGLE",
    "covered call":"COVERED_CALL","protective put":"PROTECTIVE_PUT","cash secured put":"CSP",
    "bull call spread":"BULL_CALL_SPREAD","bear call spread":"BEAR_CALL_SPREAD",
    "bull put spread":"BULL_PUT_SPREAD","bear put spread":"BEAR_PUT_SPREAD",
    "iron condor":"IRON_CONDOR","iron butterfly":"IRON_BUTTERFLY",
    "broken wing butterfly":"BWB","butterfly":"BUTTERFLY","condor":"CONDOR",
    "calendar spread":"CALENDAR_SPREAD","diagonal spread":"DIAGONAL_SPREAD",
    "ratio spread":"RATIO_SPREAD","collar":"COLLAR","risk reversal":"RISK_REVERSAL",
    "synthetic long":"SYNTH_LONG","synthetic short":"SYNTH_SHORT",
    "delta hedge":"DELTA_HEDGE","gamma scalp":"GAMMA_SCALP",
    "volatility arbitrage":"VOL_ARB","dispersion trade":"DISPERSION",
}
CONDITIONS={
    "rsi oversold":"RSI_OS","rsi overbought":"RSI_OB","rsi divergence":"RSI_DIV","rsi crossover":"RSI_CROSS","rsi":"RSI",
    "macd crossover":"MACD_CROSS","macd bullish":"MACD_BULL","macd bearish":"MACD_BEAR","macd":"MACD",
    "ema crossover":"EMA_CROSS","ema200":"EMA200","ema50":"EMA50","ema":"EMA",
    "golden cross":"GOLDEN_CROSS","death cross":"DEATH_CROSS",
    "supertrend buy":"ST_BUY","supertrend sell":"ST_SELL","supertrend":"SUPERTREND",
    "bb squeeze":"BB_SQ","bb breakout":"BB_BO","bollinger":"BB",
    "vix spike":"VIX_SPK","vix crush":"VIX_CRUSH","india vix":"VIX","vix":"VIX",
    "iv rank":"IV_RANK","iv percentile":"IV_PERC","iv crush":"IV_CRUSH","iv expansion":"IV_EXP","iv":"IV",
    "vwap breakout":"VWAP_BO","vwap bounce":"VWAP_BNC","vwap":"VWAP",
    "volume surge":"VOL_SURGE","volume breakout":"VOL_BO","obv":"OBV",
    "breakout":"BREAKOUT","breakdown":"BREAKDOWN","reversal":"REVERSAL",
    "support":"SUPPORT","resistance":"RESISTANCE","gap up":"GAP_UP","gap down":"GAP_DOWN",
    "order block":"ORDER_BLOCK","fair value gap":"FVG","fvg":"FVG",
    "change of character":"CHOCH","choch":"CHOCH","break of structure":"BOS","bos":"BOS",
    "liquidity sweep":"LIQ_SWEEP","stop hunt":"STOP_HUNT",
    "wyckoff spring":"SPRING","wyckoff upthrust":"UPTHRUST","wyckoff":"WYCKOFF",
    "oi buildup":"OI_BUILD","oi unwinding":"OI_UNWIND","open interest":"OI",
    "pcr high":"PCR_HIGH","pcr low":"PCR_LOW","pcr":"PCR",
    "gamma exposure":"GEX","gamma flip":"GAMMA_FLIP","max pain":"MAX_PAIN",
    "dark pool":"DARK_POOL","unusual activity":"UNUSUAL_ACT","block trade":"BLOCK",
    "fii buying":"FII_BUY","fii selling":"FII_SELL","dii buying":"DII_BUY","dii selling":"DII_SELL",
    "sgx nifty":"SGX_NIFTY","gift nifty":"GIFT_NIFTY","global cues":"GLOBAL",
    "dollar index":"DXY","dxy":"DXY","us market":"US_MKT",
    "sideways":"SIDEWAYS","rangebound":"RANGEBOUND","trending":"TRENDING",
    "overbought":"OVERBOUGHT","oversold":"OVERSOLD","volatile":"VOLATILE",
    "fib 61":"FIB_61","fibonacci":"FIB","mean reversion":"MEAN_REV",
    "hammer":"HAMMER","doji":"DOJI","engulfing":"ENGULF","pin bar":"PIN_BAR",
    "earnings":"EARNINGS","budget":"BUDGET","rbi policy":"RBI","fed meeting":"FED",
    "circuit breaker":"CIRCUIT","upper circuit":"UPPER_CKT","lower circuit":"LOWER_CKT",
}
EXIT_CONDS={
    "stop loss":"STOPLOSS","sl":"STOPLOSS","stoploss":"STOPLOSS",
    "target":"TARGET","tp":"TARGET","take profit":"TARGET",
    "trailing stop":"TRAIL_SL","trailing sl":"TRAIL_SL",
    "break even":"BREAKEVEN","partial exit":"PART_EXIT",
    "eod exit":"EOD_EXIT","time stop":"TIME_SL",
    "50% premium":"HALF_PREM","premium stop":"PREM_SL",
    "daily stop":"DAILY_STOP","3 loss stop":"LOSS_3",
    "nikal lo":"EXIT_NOW","bahar niklo":"EXIT_NOW",
}
STRIKE_SEL={
    "deep itm":"DEEP_ITM","deep otm":"DEEP_OTM",
    "at the money":"ATM","atm":"ATM","out of the money":"OTM","otm":"OTM","in the money":"ITM","itm":"ITM",
    "3 strike otm":"OTM_3","2 strike otm":"OTM_2","1 strike otm":"OTM_1",
    "2 strike itm":"ITM_2","1 strike itm":"ITM_1",
    "50 delta":"D50","25 delta":"D25","16 delta":"D16","10 delta":"D10",
    "equidistant":"EQUIDIST","symmetric":"SYMMETRIC",
}
TIME_MAP={
    "pre market":"09:00","market open":"09:15","opening":"09:15",
    "morning":"09:20","subah":"09:20","सुबह":"09:20",
    "mid day":"12:00","noon":"12:00","dopahar":"12:00",
    "closing":"15:15","market close":"15:15","shaam":"15:00","शाम":"15:00",
    "eod":"15:20","expiry time":"15:25","orb":"09:30","power hour":"14:00",
}
EXPIRY_MAP={
    "next week":"NEXT_WEEKLY","this week":"WEEKLY","weekly expiry":"WEEKLY","weekly":"WEEKLY","week":"WEEKLY",
    "next month":"NEXT_MONTHLY","this month":"MONTHLY","monthly":"MONTHLY","month":"MONTHLY",
    "quarterly":"QUARTERLY","is hafte":"WEEKLY","mahina":"MONTHLY",
}
RISK_CONDS={
    "1% risk":"RISK_1PCT","2% risk":"RISK_2PCT","percent risk":"PCT_RISK",
    "kelly criterion":"KELLY","half kelly":"HALF_KELLY","atr sizing":"ATR_SIZE",
    "fixed fractional":"FIXED_FRAC","volatility sizing":"VOL_SIZE",
    "atr stop":"ATR_SL","swing stop":"SWING_SL","chandelier stop":"CHAND_SL",
    "trailing stop":"TRAIL_SL","structure stop":"STRUCT_SL",
    "1r":"R1","2r":"R2","3r":"R3","5r":"R5",
    "1:2":"RR_1_2","1:3":"RR_1_3","1:1":"RR_1_1","1:5":"RR_1_5",
    "max drawdown":"MAX_DD","daily drawdown":"DAILY_DD","portfolio heat":"PORT_HEAT",
    "daily loss limit":"DAILY_LOSS","3 loss stop":"LOSS_3_STOP","drawdown pause":"DD_PAUSE",
    "delta hedge":"DELTA_HDG","tail hedge":"TAIL_HDG","vix hedge":"VIX_HDG",
    "gamma risk":"GAMMA_RISK","pin risk":"PIN_RISK","sharpe ratio":"SHARPE",
}

# Helpers
def ei(t):
    for k,v in sorted(INSTRUMENTS.items(),key=lambda x:-len(x[0])):
        if k in t: return v
    return "NIFTY"
def ea(t):
    s=sum(1 for w in SELL_WORDS if w in t); b=sum(1 for w in BUY_WORDS if w in t)
    return "SELL" if s>b else "BUY"
def en(t):
    n=re.findall(r'\b(\d{4,6})\b',t)
    return [int(x) for x in n] if len(n)>1 else (int(n[0]) if n else None)
def ef(d,t):
    f={}
    for k,v in sorted(d.items(),key=lambda x:-len(x[0])):
        if k in t:
            m=re.search(rf'{re.escape(k)}\s*([<>=!]+)?\s*(\d+\.?\d*)?',t)
            f[v]={"op":m.group(1) or "=","val":float(m.group(2))} if m and m.group(2) else True
    return f or None
def esl(t):
    r={}
    sl=re.search(r'(?:sl|stop loss|stoploss)\s*[=:@]?\s*(\d+)',t)
    tg=re.search(r'(?:target|tp)\s*[=:@]?\s*(\d+)',t)
    tr=re.search(r'trailing\s*(?:sl|stop)?\s*[=:@]?\s*(\d+)',t)
    rr=re.search(r'(?:rr)\s*[=:@]?\s*(\d+)[:/](\d+)',t)
    if sl: r["stoploss_points"]=int(sl.group(1))
    if tg: r["target_points"]=int(tg.group(1))
    if sl and tg: r["risk_reward"]=f"1:{round(int(tg.group(1))/int(sl.group(1)),1)}"
    if tr: r["trailing_sl"]=int(tr.group(1))
    if rr: r["risk_reward"]=f"{rr.group(1)}:{rr.group(2)}"
    return r or None
def dl(t):
    if len(re.findall(r'[\u0900-\u097F]',t))>3: return "HINDI"
    if any(w in t for w in ["kharido","becho","lo","niklo","subah","shaam","lagao","karo","bachao"]): return "HINGLISH"
    return "ENGLISH"
def cc(r):
    s=0.65
    for k,w in [("option_type",0.05),("strategy",0.05),("strike",0.03),("strike_selection",0.03),
                ("conditions",0.04),("exit",0.03),("risk_management",0.03),
                ("hedge",0.04),("risk_metrics",0.02),("time",0.02)]:
        if r.get(k): s+=w
    return min(round(s,2),0.99)

# ═══════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════
class StrategyPayload(BaseModel):
    text: str

class TradePayload(BaseModel):
    instrument: str="NIFTY"; action: str="BUY"; option_type: Optional[str]="CE"
    strike: Optional[int]=None; expiry: str="WEEKLY"; quantity: int=1
    entry_price: float=100.0; strategy: Optional[str]=None
    confidence: float=0.92; risk_metrics: Optional[dict]=None
    is_hedge: bool=False; hedge_strategy: Optional[str]=None

class ClosePayload(BaseModel):
    position_id: str; exit_price: float; reason: str="MANUAL"

class PriceUpdate(BaseModel):
    prices: Dict[str, float]

class RiskCalcPayload(BaseModel):
    method: str="FIXED_FRACTIONAL"; sl_points: float=100; lot_size: int=50
    win_rate: float=0.5; avg_win: float=200; avg_loss: float=100; atr: float=100

class HedgePayload(BaseModel):
    portfolio_value: float=500000; delta_exposure: float=0
    instrument: str="NIFTY"; hedge_type: str="PROTECTIVE_PUT"
    hedge_pct: float=100; trigger: Optional[str]=None

# ═══════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════
@app.get("/")
def root():
    return {"status":"running","version":"12.3",
            "modules":["nlp","hedge_nlp","paper_engine","risk_manager","event_bus"],
            "event_driven": EVENT_DRIVEN}

@app.post("/strategy")
def parse_strategy(payload: StrategyPayload):
    raw=payload.text; t=raw.lower().strip()
    qty_m=re.search(r'(\d+)\s*(?:lot|lots|लॉट)',t)
    qty=int(qty_m.group(1)) if qty_m else 1
    inst=ei(t); act=ea(t); strike=en(t)
    opt_m={k:v for k,v in OPTION_TYPES.items() if re.search(r'\b'+re.escape(k)+r'\b',t)}
    opt=list(opt_m.values())[0] if opt_m else None
    strat=next((v for k,v in sorted(STRATEGIES.items(),key=lambda x:-len(x[0])) if k in t),None)
    conds=ef(CONDITIONS,t); exit_c=ef(EXIT_CONDS,t)
    risk_c=ef(RISK_CONDS,t); risk_m=esl(t)
    ss=next((v for k,v in sorted(STRIKE_SEL.items(),key=lambda x:-len(x[0])) if k in t),None)
    et=next((v for k,v in sorted(TIME_MAP.items(),key=lambda x:-len(x[0])) if k in t),None)
    expiry=next((v for k,v in sorted(EXPIRY_MAP.items(),key=lambda x:-len(x[0])) if k in t),"WEEKLY")
    lang=dl(t)
    # Hedge detection
    hedge=parse_hedge(t) if "hedge" in t or "bachao" in t or "protect" in t else None

    r={"instrument":inst,"action":act,"language":lang,"expiry":expiry,"quantity":qty}
    if opt: r["option_type"]=opt
    if strike: r["strike"]=strike
    if ss: r["strike_selection"]=ss
    if strat: r["strategy"]=strat
    if conds: r["conditions"]=conds
    if exit_c: r["exit"]=exit_c
    if risk_c: r["risk_management"]=risk_c
    if risk_m: r["risk_metrics"]=risk_m
    if et: r["time"]=et
    if hedge: r["hedge"]=hedge
    r["confidence"]=cc(r)
    r["parsed_at"]=time.strftime("%H:%M:%S")

    if EVENT_DRIVEN:
        bus.emit(EventType.NLP_PARSED, r, source="NLP")
    return r

@app.post("/trade")
def execute_trade(payload: TradePayload):
    order=payload.dict()
    risk_check=risk_manager.check_trade(order)
    if not risk_check["allowed"]:
        if EVENT_DRIVEN:
            bus.emit(EventType.ORDER_REJECTED,{"reason":risk_check.get("reason")},source="RISK")
        return {"status":"REJECTED","reason":risk_check.get("reason","Risk limit")}
    if order.get("confidence",0.92)<0.50:
        return {"status":"REJECTED","reason":"Low confidence"}
    result=paper_engine.open_position(order)
    if result["status"]=="EXECUTED":
        risk_manager.open_positions=len(paper_engine.positions)
        risk_manager.trades_today+=1
        if EVENT_DRIVEN:
            bus.emit(EventType.POSITION_OPEN,{**order,**result},source="PAPER")
    return {**result,"confidence":order.get("confidence",0.92),"mode":"PAPER"}

@app.post("/trade/close")
def close_trade(payload: ClosePayload):
    result=paper_engine.close_position(payload.position_id,payload.exit_price,payload.reason)
    if result["status"]=="CLOSED":
        risk_manager.open_positions=len(paper_engine.positions)
        risk_manager.daily_loss+=min(0,result["net_pnl"])
        if EVENT_DRIVEN:
            bus.emit(EventType.POSITION_CLOSE,result,source="PAPER")
    return result

@app.get("/positions")
def get_positions():
    positions=[{"id":pid,"instrument":p.instrument,"action":p.action,
        "option_type":p.option_type,"strike":p.strike,"quantity":p.quantity,
        "lot_size":p.lot_size,"entry_price":p.entry_price,"current_price":p.current_price,
        "stoploss":p.stoploss,"target":p.target,"pnl":round(p.pnl,0),
        "pnl_pct":p.pnl_pct,"strategy":p.strategy,"entry_time":p.entry_time,"status":p.status}
        for pid,p in paper_engine.positions.items()]
    return {"positions":positions,"count":len(positions)}

@app.get("/trades")
def get_trades():
    return {"trades":[{"id":t.id,"instrument":t.instrument,"action":t.action,
        "strike":t.strike,"quantity":t.quantity,"entry_price":t.entry_price,
        "exit_price":t.exit_price,"entry_time":t.entry_time,"exit_time":t.exit_time,
        "exit_reason":t.exit_reason,"strategy":t.strategy,
        "gross_pnl":round(t.pnl,0),"net_pnl":round(t.net_pnl,0),
        "pnl_pct":round(t.pnl_pct,2),"broker":t.broker}
        for t in paper_engine.trade_log],"count":len(paper_engine.trade_log)}

@app.get("/stats")
def get_stats():
    return {"performance":paper_engine.get_stats(),"risk":risk_manager.get_risk_report()}

@app.post("/prices/update")
def update_prices(payload: PriceUpdate):
    closed=paper_engine.update_prices(payload.prices)
    if EVENT_DRIVEN:
        for inst,price in payload.prices.items():
            market_handler.publish_tick(inst,price)
    return {"updated":True,"auto_closed":len(closed)}

@app.post("/hedge/analyze")
def analyze_hedge(payload: HedgePayload):
    """Calculate hedge requirements"""
    inst=payload.instrument
    lot_size=LOT_SIZES.get(inst,50)
    lots_to_hedge=max(1,round(payload.portfolio_value*payload.hedge_pct/100/(20000*lot_size)))
    delta_hedge_lots=abs(payload.delta_exposure)/lot_size if payload.delta_exposure else 0
    return {
        "instrument":inst,"hedge_type":payload.hedge_type,
        "portfolio_value":payload.portfolio_value,
        "hedge_pct":payload.hedge_pct,
        "lots_required":lots_to_hedge,
        "delta_hedge_lots":round(delta_hedge_lots,1),
        "estimated_hedge_cost":lots_to_hedge*100*lot_size,
        "recommendation":{
            "strategy":"PROTECTIVE_PUT" if payload.delta_exposure>0 else "COVERED_CALL",
            "strike_selection":"OTM_1" if payload.hedge_pct<50 else "ATM",
            "expiry":"MONTHLY",
            "review_trigger":"VIX>15 or portfolio_loss>2%"
        }
    }

@app.post("/risk/calculate")
def calc_risk(payload: RiskCalcPayload):
    return risk_manager.calculate_position_size(
        payload.method.upper(),sl_points=payload.sl_points,lot_size=payload.lot_size,
        win_rate=payload.win_rate,avg_win=payload.avg_win,avg_loss=payload.avg_loss,atr=payload.atr)

@app.get("/risk/calculator")
def risk_calc(sl:float=100,target:float=200,qty:int=1,lot_size:int=50,capital:float=500000):
    ra=sl*qty*lot_size; rw=target*qty*lot_size
    return {"stoploss_points":sl,"target_points":target,"lots":qty,"lot_size":lot_size,
            "risk_rupees":ra,"reward_rupees":rw,"risk_reward":f"1:{round(target/sl,2)}",
            "min_win_rate_needed":f"{round(sl/(sl+target)*100,1)}%",
            "capital_at_risk_pct":f"{round(ra/capital*100,2)}%",
            "expectancy":round((0.5*rw)-(0.5*ra),0)}

@app.get("/risk/report")
def risk_report(): return risk_manager.get_risk_report()

@app.post("/risk/kill_switch")
def kill_switch(active:bool=True):
    risk_manager.kill_switch=active
    if EVENT_DRIVEN: bus.emit(EventType.KILL_SWITCH,{"reason":"Manual","active":active})
    return {"kill_switch":active}

@app.post("/paper/reset")
def reset_paper(capital:float=500000):
    global paper_engine; paper_engine=PaperTradingEngine(capital=capital)
    return {"status":"reset","capital":capital}

@app.get("/events/history")
def event_history(limit:int=50):
    if not EVENT_DRIVEN: return {"events":[],"event_driven":False}
    return {"events":bus.get_history(limit=limit),"stats":bus.get_stats()}

@app.get("/events/log")
def event_log(limit:int=100):
    return {"log":system_log[-limit:],"count":len(system_log)}

@app.post("/events/emit")
def emit_event(event_type:str, data:dict={}):
    if not EVENT_DRIVEN: return {"status":"Event bus not available"}
    bus.emit(getattr(EventType,event_type,EventType.LOG),data,source="API")
    return {"emitted":event_type,"data":data}

@app.get("/nlp/hedge/capabilities")
def hedge_caps():
    from nlp.hedge_nlp import HEDGE_STRATEGIES,HEDGE_TRIGGERS,HEDGE_INSTRUMENTS,HEDGE_SIZING
    return {
        "hedge_strategies":len(HEDGE_STRATEGIES),
        "hedge_triggers":len(HEDGE_TRIGGERS),
        "hedge_instruments":len(HEDGE_INSTRUMENTS),
        "hedge_sizing":len(HEDGE_SIZING),
        "examples":[
            "protective put hedge nifty if portfolio down 2%",
            "delta hedge banknifty if delta exceeds 50",
            "collar hedge nifty before earnings 50% hedge",
            "tail risk hedge if vix above 20 buy otm put",
            "hedge lagao before budget 25% hedge",
            "portfolio hedge nifty futures if fii selling",
            "iron condor hedge if iv rank high and sideways",
            "gamma hedge banknifty before expiry",
            "हेज लगाओ निफ्टी पुट if market falls",
        ]
    }

@app.get("/capabilities")
def caps():
    return {"version":"12.3","architecture":"EVENT_DRIVEN","event_driven":EVENT_DRIVEN,
        "modules":{"nlp":"500+ conditions","hedge_nlp":"100+ hedge strategies",
            "event_bus":"15+ event types","paper_engine":"Full simulation",
            "risk_manager":"Complete risk management"},
        "api_endpoints":["/strategy","/trade","/trade/close","/positions","/trades",
            "/stats","/prices/update","/hedge/analyze","/risk/calculate",
            "/risk/report","/risk/kill_switch","/events/history","/events/log","/paper/reset"]}

# ═══════════════════════════════════════
# NEW MODULES
# ═══════════════════════════════════════
try:
    from backtest.engine import BacktestEngine, backtest_engine
    from engine.strategy_engine import StrategyEngine, strategy_engine, BUILTIN_STRATEGIES, StrategyConfig
    from engine.notifications import NotificationEngine, notifier
    from engine.portfolio import PortfolioTracker, PortfolioPosition, portfolio
    from engine.options_chain import generate_chain
    from brokers import get_broker
    MODULES_LOADED = True
except Exception as e:
    MODULES_LOADED = False
    print(f"Modules: {e}")

# ─── BACKTEST ────────────────────────────────────────
class BacktestPayload(BaseModel):
    strategy: str = "EMA_CROSS"
    instrument: str = "NIFTY"
    bars: int = 252
    quantity: int = 1
    sl_pct: float = 1.0
    target_pct: float = 2.0
    run_monte_carlo: bool = True
    run_walk_forward: bool = True

@app.post("/backtest/run")
def run_backtest(payload: BacktestPayload):
    if not MODULES_LOADED:
        return {"error": "Backtest module not loaded"}
    candles = backtest_engine.generate_sample_data(payload.instrument, payload.bars)
    result = backtest_engine.run_strategy(
        payload.strategy, candles, payload.quantity, payload.sl_pct, payload.target_pct)
    response = {
        "strategy": result.strategy,
        "instrument": payload.instrument,
        "bars_tested": len(candles),
        "total_trades": result.total_trades,
        "winning_trades": result.winning_trades,
        "losing_trades": result.losing_trades,
        "win_rate": result.win_rate,
        "total_pnl": result.total_pnl,
        "profit_factor": result.profit_factor,
        "avg_win": result.avg_win,
        "avg_loss": result.avg_loss,
        "max_drawdown_pct": result.max_drawdown,
        "sharpe_ratio": result.sharpe_ratio,
        "expectancy": result.expectancy,
        "max_consecutive_wins": result.max_consecutive_wins,
        "max_consecutive_losses": result.max_consecutive_losses,
        "equity_curve": result.equity_curve,
        "verdict": "PROFITABLE" if result.total_pnl > 0 else "UNPROFITABLE",
    }
    if payload.run_monte_carlo:
        pnls = [t.pnl for t in result.trades]
        response["monte_carlo"] = backtest_engine.monte_carlo(pnls)
    if payload.run_walk_forward:
        response["walk_forward"] = backtest_engine.walk_forward(payload.strategy, candles)
    return response

@app.get("/backtest/strategies")
def backtest_strategies():
    return {"strategies": ["EMA_CROSS","RSI_MEAN_REVERSION","BOLLINGER_BREAKOUT",
                           "EMA_RSI_COMBO","SUPERTREND_LIKE"]}

# ─── STRATEGY ENGINE ────────────────────────────────
class StrategyPayloadNew(BaseModel):
    name: str; instrument: str = "NIFTY"; quantity: int = 1
    sl_pct: float = 1.0; target_pct: float = 2.0
    auto_execute: bool = False; mode: str = "PAPER"

@app.post("/strategy/add")
def add_strategy(payload: StrategyPayloadNew):
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    config = StrategyConfig(name=payload.name, instrument=payload.instrument,
        quantity=payload.quantity, auto_execute=payload.auto_execute, mode=payload.mode)
    sid = strategy_engine.add_strategy(config)
    return {"status": "added", "strategy_id": sid}

@app.get("/strategy/list")
def list_strategies():
    if not MODULES_LOADED: return {"strategies": [], "builtin": BUILTIN_STRATEGIES}
    return {"active": strategy_engine.get_all_status(),
            "builtin": BUILTIN_STRATEGIES, "count": len(strategy_engine.strategies)}

@app.get("/strategy/signals")
def get_signals(limit: int = 20):
    if not MODULES_LOADED: return {"signals": []}
    return {"signals": strategy_engine.get_recent_signals(limit)}

@app.post("/strategy/{sid}/pause")
def pause_strategy(sid: str):
    if MODULES_LOADED: strategy_engine.pause_strategy(sid)
    return {"status": "paused", "id": sid}

@app.post("/strategy/{sid}/resume")
def resume_strategy(sid: str):
    if MODULES_LOADED: strategy_engine.resume_strategy(sid)
    return {"status": "resumed", "id": sid}

@app.post("/strategy/update_market")
def update_market(prices: dict, indicators: dict = {}):
    if MODULES_LOADED: strategy_engine.update_market_data(prices, indicators)
    return {"updated": True}

# ─── OPTIONS CHAIN ─────────────────────────────────
@app.get("/options/chain")
def options_chain(spot: float = 22450, dte: int = 7, iv: float = 15,
                  instrument: str = "NIFTY"):
    chain = generate_chain(spot, dte, iv/100)
    return chain

@app.get("/options/greeks")
def option_greeks(spot: float, strike: float, dte: int = 7,
                  iv: float = 15, opt_type: str = "CE"):
    from engine.options_chain import black_scholes
    result = black_scholes(spot, strike, dte, 0.065, iv/100, opt_type)
    intrinsic = max(0, spot-strike) if opt_type=="CE" else max(0, strike-spot)
    return {**result, "intrinsic_value": round(intrinsic, 2),
            "time_value": round(result["price"]-intrinsic, 2),
            "moneyness": "ATM" if abs(spot-strike)<25 else ("ITM" if
                (opt_type=="CE" and spot>strike) or (opt_type=="PE" and spot<strike) else "OTM")}

# ─── PORTFOLIO ──────────────────────────────────────
@app.get("/portfolio/summary")
def portfolio_summary():
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    return portfolio.get_summary()

@app.get("/portfolio/positions")
def portfolio_positions():
    if not MODULES_LOADED: return {"positions": []}
    return {"positions": [
        {"id": pid, "instrument": p.instrument, "action": p.action,
         "option_type": p.option_type, "strike": p.strike,
         "quantity": p.quantity, "avg_price": p.avg_price,
         "current_price": p.current_price, "pnl": round(p.pnl, 0),
         "pnl_pct": p.pnl_pct, "is_hedge": p.is_hedge, "delta": p.delta}
        for pid, p in portfolio.positions.items()
    ]}

# ─── NOTIFICATIONS ──────────────────────────────────
class NotifConfig(BaseModel):
    telegram_token: str = ""; telegram_chat_id: str = ""; webhook_url: str = ""

@app.post("/notifications/configure")
def configure_notif(payload: NotifConfig):
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    if payload.telegram_token:
        notifier.configure_telegram(payload.telegram_token, payload.telegram_chat_id)
    if payload.webhook_url:
        notifier.configure_webhook(payload.webhook_url)
    return {"telegram": notifier.enabled["telegram"], "webhook": notifier.enabled["webhook"]}

@app.get("/notifications/history")
def notif_history(limit: int = 20):
    if not MODULES_LOADED: return {"notifications": []}
    return {"notifications": notifier.get_recent(limit)}

@app.post("/notifications/test")
def test_notif():
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    notifier.send(__import__('engine.notifications', fromlist=['Notification']).Notification(
        "SYSTEM","INFO","Test Notification","Trading System v12.3 is running!"))
    return {"sent": True}

# ─── BROKER STATUS ──────────────────────────────────
@app.get("/broker/status")
def broker_status():
    return {"active_broker": "ZERODHA", "mode": "PAPER",
            "brokers": ["ZERODHA","ANGEL","FYERS"],
            "note": "Add API keys in config/settings.py for live trading",
            "live_trading": False}

@app.get("/broker/connect/{broker_name}")
def connect_broker(broker_name: str, api_key: str = "", access_token: str = ""):
    if not MODULES_LOADED: return {"error": "Module not loaded"}
    try:
        broker = get_broker(broker_name, api_key=api_key, access_token=access_token)
        connected = broker.login()
        return {"broker": broker_name, "connected": connected,
                "note": "Add real API keys for live connection"}
    except Exception as e:
        return {"error": str(e)}

# ─── SYSTEM STATUS ──────────────────────────────────
@app.get("/system/status")
def system_status():
    stats = paper_engine.get_stats()
    return {
        "version": "12.3",
        "status": "RUNNING",
        "mode": "PAPER",
        "event_driven": EVENT_DRIVEN,
        "modules_loaded": MODULES_LOADED,
        "uptime": time.strftime("%H:%M:%S"),
        "performance": {
            "capital": stats.get("capital", 500000),
            "total_pnl": stats.get("total_pnl", 0),
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0),
        },
        "risk": risk_manager.get_risk_report(),
        "components": {
            "nlp": "ACTIVE", "paper_engine": "ACTIVE",
            "risk_manager": "ACTIVE", "event_bus": "ACTIVE" if EVENT_DRIVEN else "INACTIVE",
            "backtest": "ACTIVE" if MODULES_LOADED else "INACTIVE",
            "strategy_engine": "ACTIVE" if MODULES_LOADED else "INACTIVE",
            "options_chain": "ACTIVE" if MODULES_LOADED else "INACTIVE",
            "notifications": "CONFIGURED" if MODULES_LOADED and notifier.enabled.get("telegram") else "NOT_CONFIGURED",
            "brokers": "ZERODHA/ANGEL/FYERS (Paper Mode)",
        }
    }

# ═══════════════════════════════════════
# MISSING MODULES INTEGRATION
# ═══════════════════════════════════════
try:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.db import db
    from scanner.market_scanner import scanner, ScanResult
    from scanner.iv_analyzer import iv_analyzer, regime_detector, correlation_tracker
    from indicators.ta_engine import compute_all, pivot_points
    from oms.order_manager import oms
    from reports.report_generator import reporter
    from backend.ws_server import ws_manager
    from fastapi import WebSocket, WebSocketDisconnect
    import asyncio
    FULL_SYSTEM = True
except Exception as e:
    print(f"Full system: {e}")
    FULL_SYSTEM = False

# ── WEBSOCKET ──────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if not FULL_SYSTEM:
        await websocket.accept()
        await websocket.send_json({"type":"INFO","msg":"WebSocket active (limited mode)"})
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data) if data else {}
            if msg.get("type") == "PING":
                await ws_manager.send_one(websocket, {"type":"PONG"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@app.on_event("startup")
async def startup():
    if FULL_SYSTEM:
        asyncio.create_task(ws_manager.tick_loop())
    if EVENT_DRIVEN:
        bus.emit(EventType.SYSTEM_START, {"msg":"System fully started","modules":"ALL"})

# ── DATABASE ───────────────────────────────────────────
@app.get("/db/trades")
def db_trades(limit: int = 100, instrument: str = None):
    if not FULL_SYSTEM: return {"trades":[],"note":"DB not loaded"}
    return {"trades": db.get_trades(limit, instrument), "stats": db.get_stats()}

@app.get("/db/stats")
def db_stats():
    if not FULL_SYSTEM: return {}
    return db.get_stats()

@app.get("/db/equity")
def db_equity(limit: int = 200):
    if not FULL_SYSTEM: return {"curve":[]}
    return {"curve": db.get_equity(limit)}

@app.get("/db/iv_history/{instrument}")
def db_iv(instrument: str, days: int = 30):
    if not FULL_SYSTEM: return {"history":[]}
    return {"history": db.get_iv_history(instrument, days)}

@app.get("/db/alerts")
def db_alerts(unread: bool = False):
    if not FULL_SYSTEM: return {"alerts":[]}
    return {"alerts": db.get_alerts(unread)}

@app.post("/db/alerts/{alert_id}/ack")
def ack_alert(alert_id: int):
    if FULL_SYSTEM: db.ack_alert(alert_id)
    return {"acknowledged": alert_id}

# ── JOURNAL ────────────────────────────────────────────
class JournalEntry(BaseModel):
    trade_id: str = ""; instrument: str = ""; action: str = ""
    pnl: float = 0; emotion: str = ""; mistakes: str = ""
    lessons: str = ""; rating: int = 5; notes: str = ""

@app.post("/journal/add")
def add_journal(entry: JournalEntry):
    if not FULL_SYSTEM: return {"error":"DB not loaded"}
    jid = db.add_journal(entry.dict())
    return {"id": jid, "status": "saved"}

@app.get("/journal")
def get_journal(limit: int = 50):
    if not FULL_SYSTEM: return {"journal":[]}
    return {"journal": db.get_journal(limit)}

# ── SCANNER ────────────────────────────────────────────
@app.get("/scanner/run")
def run_scanner():
    if not FULL_SYSTEM: return {"opportunities":[]}
    results = scanner.scan_all()
    return {
        "opportunities": [{"instrument":r.instrument,"signal":r.signal,"action":r.action,
            "strategy":r.strategy,"price":r.price,"confidence":r.confidence,
            "conditions":r.conditions_met,"strength":r.strength,"time":r.timestamp}
            for r in results],
        "count": len(results), "scan_time": scanner.last_scan,
        "top_5": scanner.get_top_opportunities(5),
    }

@app.get("/scanner/top")
def top_opportunities(limit: int = 5):
    if not FULL_SYSTEM: return {"opportunities":[]}
    return {"opportunities": scanner.get_top_opportunities(limit)}

class ScanConditions(BaseModel):
    rsi_below: Optional[float] = None; rsi_above: Optional[float] = None
    iv_rank_above: Optional[float] = None; volume_surge: Optional[float] = None

@app.post("/scanner/custom")
def custom_scan(conditions: ScanConditions):
    if not FULL_SYSTEM: return {"results":[]}
    results = scanner.scan_custom(conditions.dict(exclude_none=True))
    return {"results": [{"instrument":r.instrument,"signal":r.signal,"action":r.action,
        "price":r.price,"confidence":r.confidence,"conditions":r.conditions_met}
        for r in results]}

# ── IV ANALYSIS ─────────────────────────────────────────
@app.get("/iv/rank/{instrument}")
def iv_rank(instrument: str, current_iv: float = 15.0):
    # Simulate some IV history
    for _ in range(50):
        import random
        iv_analyzer.add_iv(instrument, random.uniform(10, 25))
    iv_analyzer.add_iv(instrument, current_iv)
    return iv_analyzer.get_iv_rank(instrument, current_iv)

@app.get("/iv/history/{instrument}")
def iv_history(instrument: str):
    if not FULL_SYSTEM: return {"history":[]}
    return {"history": db.get_iv_history(instrument)}

# ── MARKET REGIME ──────────────────────────────────────
@app.get("/regime/{instrument}")
def market_regime(instrument: str, vix: float = 15.0):
    # Use simulated prices for demo
    import random
    base = {"NIFTY":22450,"BANKNIFTY":48300}.get(instrument,22450)
    prices = [base*(1+random.gauss(0,0.01)) for _ in range(30)]
    return regime_detector.detect(prices, vix)

# ── CORRELATION ────────────────────────────────────────
@app.get("/correlation/matrix")
def correlation_matrix():
    # Add sample data
    import random
    instruments = ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX"]
    for inst in instruments:
        base = {"NIFTY":22450,"BANKNIFTY":48300,"FINNIFTY":21100,"SENSEX":73800}.get(inst,22000)
        for _ in range(30):
            correlation_tracker.add_price(inst, base*(1+random.gauss(0,0.005)))
    return {"matrix": correlation_tracker.get_matrix(), "instruments": instruments}

# ── TECHNICAL INDICATORS ───────────────────────────────
@app.get("/indicators/{instrument}")
def get_indicators(instrument: str):
    import random
    base = {"NIFTY":22450,"BANKNIFTY":48300,"FINNIFTY":21100}.get(instrument,22450)
    highs=[]; lows=[]; opens=[]; closes=[]; volumes=[]
    p=base
    for _ in range(60):
        o=p*(1+random.gauss(0,0.003)); h=o*(1+abs(random.gauss(0,0.005)))
        l=o*(1-abs(random.gauss(0,0.005))); c=random.uniform(l,h)
        opens.append(o); highs.append(h); lows.append(l); closes.append(c)
        volumes.append(random.randint(500000,2000000)); p=c
    return compute_all(highs,lows,opens,closes,volumes)

@app.get("/indicators/pivot/{instrument}")
def pivot_points_api(instrument: str):
    import random
    base = {"NIFTY":22450,"BANKNIFTY":48300}.get(instrument,22450)
    h=base*1.01; l=base*0.99; c=base
    pp = pivot_points(h,l,c)
    return {**pp, "instrument":instrument, "timeframe":"DAILY"}

# ── OMS ─────────────────────────────────────────────────
@app.get("/oms/orders")
def oms_orders(status: str = None): return oms.get_all(status)

@app.post("/oms/cancel/{order_id}")
def cancel_order(order_id: str):
    return {"cancelled": oms.cancel(order_id)}

@app.post("/oms/cancel_all")
def cancel_all():
    return {"cancelled_count": oms.cancel_all()}

@app.get("/oms/stats")
def oms_stats(): return oms.get_stats()

# ── REPORTS ────────────────────────────────────────────
@app.get("/reports/daily")
def daily_report():
    trades = paper_engine.trade_log
    trade_dicts = [{"instrument":t.instrument,"action":t.action,"strategy":t.strategy,
        "gross_pnl":t.pnl,"net_pnl":t.net_pnl,"pnl_pct":t.pnl_pct,
        "brokerage":t.brokerage,"exit_time":t.exit_time} for t in trades]
    return reporter.daily_pnl_report(trade_dicts)

@app.get("/reports/performance")
def performance_report():
    trades = paper_engine.trade_log
    trade_dicts = [{"net_pnl":t.net_pnl,"gross_pnl":t.pnl} for t in trades]
    return reporter.performance_report(trade_dicts, paper_engine.initial_capital)

@app.get("/reports/weekly")
def weekly_report():
    trades = paper_engine.trade_log
    trade_dicts = [{"instrument":t.instrument,"strategy":t.strategy,
        "net_pnl":t.net_pnl,"brokerage":t.brokerage} for t in trades]
    return reporter.weekly_report(trade_dicts)

@app.get("/reports/expiry_calendar")
def expiry_cal(): return reporter.expiry_calendar()

# ── MARGIN CALCULATOR ──────────────────────────────────
@app.get("/margin/calculate")
def calc_margin(instrument: str="NIFTY", quantity: int=1,
                position_type: str="OPTIONS", price: float=100):
    lot_size = {"NIFTY":50,"BANKNIFTY":15,"FINNIFTY":40,"MIDCPNIFTY":75}.get(instrument,50)
    lots_val = quantity*lot_size
    span = {"NIFTY":1.0,"BANKNIFTY":1.2,"FINNIFTY":0.8}.get(instrument,1.0)
    if position_type=="OPTIONS":
        premium_margin = price*lots_val
        exposure_margin = premium_margin*0.10
        total = premium_margin+exposure_margin
    elif position_type=="FUTURES":
        contract_val = price*lots_val
        span_margin = contract_val*0.08*span
        exposure = contract_val*0.05
        total = span_margin+exposure
    else:
        total = price*lots_val*0.15
    return {
        "instrument":instrument,"quantity":quantity,"lot_size":lot_size,
        "position_type":position_type,"price":price,
        "total_lots_value":round(price*lots_val,0),
        "margin_required":round(total,0),
        "margin_pct":round(total/(price*lots_val)*100,1) if price>0 else 0,
        "max_lots_with_5L":int(500000/total) if total>0 else 0,
    }

# ── VOLATILITY SURFACE ─────────────────────────────────
@app.get("/volatility/surface")
def vol_surface(instrument: str="NIFTY", spot: float=22450):
    import random, math
    dtes = [7, 14, 30, 45, 90]
    strikes = [-3,-2,-1,0,1,2,3]  # relative to ATM
    atm = round(spot/50)*50
    step = 50
    surface = []
    for dte in dtes:
        row = {"dte":dte,"strikes":{}}
        base_iv = 14+random.uniform(-1,1)+math.sqrt(30/dte)*2
        for k in strikes:
            strike = atm+k*step
            skew = abs(k)*0.5+random.uniform(-0.2,0.2)
            iv = base_iv+skew if k<0 else base_iv+skew*0.5
            row["strikes"][str(strike)] = round(iv,1)
        surface.append(row)
    return {"instrument":instrument,"spot":spot,"atm":atm,
            "surface":surface,"skew":"PUT_SKEW","term_structure":"NORMAL"}

# ── ROLLOVER TRACKER ───────────────────────────────────
@app.get("/rollover/{instrument}")
def rollover_data(instrument: str="NIFTY"):
    import random
    current_oi = random.randint(8000000,15000000)
    prev_oi = random.randint(8000000,15000000)
    rollover_pct = random.uniform(60,85)
    cost = random.uniform(20,80)
    return {
        "instrument":instrument,
        "current_month_oi":current_oi,
        "next_month_oi":prev_oi,
        "rollover_pct":round(rollover_pct,1),
        "rollover_cost_pts":round(cost,2),
        "rollover_status":"NORMAL" if rollover_pct>65 else "LOW",
        "last_3_months_avg":round(random.uniform(60,80),1),
        "signal":"BULLISH" if rollover_cost<50 else "NEUTRAL",
    }

# ── FII/DII DATA ───────────────────────────────────────
@app.get("/fii_dii")
def fii_dii_data():
    import random
    fii_buy = random.uniform(1000,8000)*random.choice([1,-1])*100
    dii_buy = random.uniform(500,5000)*random.choice([1,-1])*100
    return {
        "date": time.strftime("%Y-%m-%d"),
        "fii":{"buy":round(fii_buy,0),"sell":round(abs(fii_buy)*0.9,0),
               "net":round(fii_buy*0.1,0),"activity":"BUYING" if fii_buy>0 else "SELLING"},
        "dii":{"buy":round(abs(dii_buy),0),"sell":round(abs(dii_buy)*0.85,0),
               "net":round(dii_buy*0.15,0),"activity":"BUYING" if dii_buy>0 else "SELLING"},
        "combined_net":round(fii_buy*0.1+dii_buy*0.15,0),
        "market_impact":"POSITIVE" if fii_buy>0 else "NEGATIVE",
        "note":"Simulated data — connect NSE data feed for real data",
    }

# ── UPDATED SYSTEM STATUS ──────────────────────────────
@app.get("/system/complete_status")
def complete_status():
    stats = paper_engine.get_stats()
    return {
        "version":"12.3","status":"FULLY_OPERATIONAL",
        "architecture":"EVENT_DRIVEN + FULL_STACK",
        "modules":{
            "nlp":"ACTIVE (500+ conditions, 100+ hedge strategies)",
            "paper_engine":"ACTIVE (Full P&L simulation)",
            "risk_manager":"ACTIVE (Institutional grade)",
            "event_bus":"ACTIVE (30+ event types)",
            "backtest":"ACTIVE (Monte Carlo + Walk-Forward)",
            "strategy_engine":"ACTIVE (10 built-in strategies)",
            "options_chain":"ACTIVE (Black-Scholes + Greeks)",
            "scanner":"ACTIVE (Multi-strategy scanner)",
            "iv_analyzer":"ACTIVE (IV Rank + Percentile)",
            "regime_detector":"ACTIVE (5 market regimes)",
            "correlation":"ACTIVE (Cross-asset correlation)",
            "ta_engine":"ACTIVE (20+ indicators)",
            "oms":"ACTIVE (Full order lifecycle)",
            "portfolio":"ACTIVE (Multi-position tracking)",
            "database":"ACTIVE (SQLite persistence)",
            "reports":"ACTIVE (Daily/Weekly/Performance)",
            "scheduler":"ACTIVE (Time-based execution)",
            "notifications":"CONFIGURED" if MODULES_LOADED else "PENDING",
            "brokers":"ZERODHA/ANGEL/FYERS (Paper Mode)",
            "websocket":"ACTIVE (Real-time data push)",
            "margin_calculator":"ACTIVE",
            "vol_surface":"ACTIVE (Volatility surface)",
            "rollover_tracker":"ACTIVE",
            "fii_dii":"ACTIVE",
            "expiry_calendar":"ACTIVE",
            "pivot_points":"ACTIVE",
            "journal":"ACTIVE (Trade journaling)",
        },
        "api_endpoints":"25+ endpoints",
        "performance":{"capital":stats.get("capital",500000),
                       "trades":stats.get("total_trades",0)},
        "ready_for":"PAPER_TRADING (7 day minimum before LIVE)",
    }

# ═══════════════════════════════════════
# REAL MARKET DATA ENDPOINTS
# ═══════════════════════════════════════
try:
    from engine.market_data_feed import (
        fetch_yahoo_quote, fetch_all_indices,
        fetch_historical, get_quote_cached
    )
    REAL_DATA = True
except Exception as e:
    REAL_DATA = False
    print(f"Real data: {e}")

@app.get("/market/quote/{symbol}")
def live_quote(symbol: str):
    """Real-time quote from Yahoo Finance"""
    data = get_quote_cached(symbol.upper())
    if data:
        return data
    return {
        "symbol": symbol, "error": "Data not available",
        "note": "Market may be closed or symbol invalid",
        "hint": "Try: NIFTY, BANKNIFTY, SENSEX, RELIANCE, TCS"
    }

@app.get("/market/all")
def all_market_data():
    """All major indices — real data"""
    results = {}
    symbols = ["NIFTY","BANKNIFTY","SENSEX","FINNIFTY","VIX","USDINR"]
    for sym in symbols:
        d = get_quote_cached(sym)
        if d:
            results[sym] = {
                "price": d.get("last",0),
                "change": d.get("change",0),
                "pChange": d.get("pChange",0),
                "high": d.get("high",0),
                "low": d.get("low",0),
                "source": d.get("source",""),
            }
    return {
        "data": results,
        "timestamp": time.strftime("%H:%M:%S"),
        "source": "Yahoo Finance (Free)",
        "note": "60 second cache — real market data",
    }

@app.get("/market/historical/{symbol}")
def historical_data(symbol: str, period: str = "1mo", interval: str = "1d"):
    """Historical OHLCV data"""
    candles = fetch_historical(symbol.upper(), period, interval)
    if not candles:
        return {"symbol": symbol, "candles": [], "error": "No data"}

    # Auto-compute indicators on historical data
    if len(candles) >= 20:
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        opens = [c["open"] for c in candles]
        try:
            from indicators.ta_engine import ema, rsi, atr, bollinger
            ema9 = ema(closes, 9)
            ema21 = ema(closes, 21)
            rsi14 = rsi(closes, 14)
            bb_u, bb_m, bb_l = bollinger(closes, 20, 2)
            for i, c in enumerate(candles):
                c["ema9"] = ema9[i]
                c["ema21"] = ema21[i]
                c["rsi"] = rsi14[i]
                c["bb_upper"] = bb_u[i]
                c["bb_lower"] = bb_l[i]
        except: pass

    return {
        "symbol": symbol, "period": period, "interval": interval,
        "candles": candles, "count": len(candles),
        "latest": candles[-1] if candles else {},
        "source": "Yahoo Finance",
    }

@app.get("/market/nifty")
def nifty_live():
    """NIFTY live with full details"""
    d = get_quote_cached("NIFTY")
    if not d:
        return {"error": "Market data unavailable", "note": "Market may be closed"}
    return {
        **d,
        "lot_size": 50,
        "margin_est": round(d.get("last",22000)*50*0.08, 0),
        "atm_strike": round(d.get("last",22000)/50)*50,
        "market_status": "OPEN" if 9 <= int(time.strftime("%H")) < 16 else "CLOSED",
    }

@app.get("/market/banknifty")
def banknifty_live():
    d = get_quote_cached("BANKNIFTY")
    if not d:
        return {"error": "Market data unavailable"}
    return {
        **d,
        "lot_size": 15,
        "atm_strike": round(d.get("last",48000)/100)*100,
        "margin_est": round(d.get("last",48000)*15*0.10, 0),
    }

@app.get("/market/watchlist")
def watchlist():
    """Full watchlist with real data"""
    symbols = ["NIFTY","BANKNIFTY","FINNIFTY","SENSEX","VIX","USDINR",
               "RELIANCE","TCS","HDFC","INFOSYS","ICICI","SBI"]
    result = []
    for sym in symbols:
        d = get_quote_cached(sym)
        if d:
            result.append({
                "symbol": sym,
                "price": d.get("last",0),
                "change": d.get("change",0),
                "pChange": round(d.get("pChange",0),2),
                "high": d.get("high",0),
                "low": d.get("low",0),
                "volume": d.get("volume",0),
            })
    return {"watchlist": result, "count": len(result), "timestamp": time.strftime("%H:%M:%S")}

@app.get("/market/options_chain_live/{symbol}")
def live_options_chain(symbol: str, dte: int = 7):
    """Options chain with real spot price"""
    spot_data = get_quote_cached(symbol)
    spot = spot_data.get("last", 22450) if spot_data else 22450
    # Use real spot, simulated IV (replace with NSE data for real IV)
    import random
    iv = random.uniform(12, 18) / 100
    from engine.options_chain import generate_chain
    chain = generate_chain(spot, dte, iv)
    return {
        **chain,
        "spot_source": spot_data.get("source","") if spot_data else "",
        "spot_timestamp": time.strftime("%H:%M:%S"),
        "note": "Spot price: REAL | IV: Simulated (add NSE API for real IV)"
    }

# ═══════════════════════════════════════
# USER PROFILES + STRATEGIES + ADVANCED BACKTEST
# ═══════════════════════════════════════
try:
    from database.user_db import user_db, UserDB
    from backtest.strategies import BUILTIN_STRATEGIES_V2
    from backtest.advanced_backtest import run_advanced_backtest
    USER_SYSTEM = True
except Exception as e:
    print(f"User system: {e}")
    USER_SYSTEM = False

# ── USER MANAGEMENT ────────────────────────────────────
class UserCreate(BaseModel):
    username: str; email: str = ""; password: str = "demo123"
    full_name: str = ""; capital: float = 500000

class UserLogin(BaseModel):
    username: str; password: str

class UserUpdate(BaseModel):
    full_name: str = None; email: str = None; phone: str = None
    broker: str = None; capital: float = None; risk_per_trade: float = None
    max_daily_loss: float = None; preferred_instruments: str = None
    theme: str = None; telegram_chat_id: str = None

@app.post("/users/register")
def register(payload: UserCreate):
    if not USER_SYSTEM: return {"error":"User system not loaded"}
    result = user_db.create_user(
        payload.username, payload.email, payload.password,
        payload.full_name, payload.capital)
    return result

@app.post("/users/login")
def login(payload: UserLogin):
    if not USER_SYSTEM: return {"error":"User system not loaded"}
    result = user_db.login(payload.username, payload.password)
    if not result:
        return {"error": "Invalid username or password"}
    return result

@app.get("/users/{user_id}")
def get_user(user_id: str):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    user = user_db.get_user(user_id)
    return user if user else {"error":"User not found"}

@app.put("/users/{user_id}")
def update_user(user_id: str, payload: UserUpdate):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    updates = {k:v for k,v in payload.dict().items() if v is not None}
    user_db.update_profile(user_id, updates)
    return {"updated": True, "fields": list(updates.keys())}

@app.get("/users")
def list_users():
    if not USER_SYSTEM: return {"users":[]}
    return {"users": user_db.get_all_users()}

# ── USER STRATEGIES ────────────────────────────────────
class StrategySave(BaseModel):
    user_id: str; name: str; description: str = ""
    instrument: str = "NIFTY"; timeframe: str = "15MIN"
    entry_conditions: List[str] = []; exit_conditions: List[str] = []
    sl_type: str = "FIXED"; sl_value: float = 100
    target_type: str = "FIXED"; target_value: float = 200
    quantity: int = 1; risk_per_trade: float = 1.0
    tags: List[str] = []; is_public: bool = False

@app.post("/strategies/save")
def save_user_strategy(payload: StrategySave):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    sid = user_db.save_strategy(payload.user_id, payload.dict())
    return {"strategy_id": sid, "status": "saved", "name": payload.name}

@app.get("/strategies/user/{user_id}")
def get_user_strategies(user_id: str):
    if not USER_SYSTEM: return {"strategies":[], "builtin": BUILTIN_STRATEGIES_V2 if USER_SYSTEM else []}
    return {
        "user_strategies": user_db.get_strategies(user_id),
        "builtin": BUILTIN_STRATEGIES_V2,
        "total": len(user_db.get_strategies(user_id)),
    }

@app.get("/strategies/public")
def get_public_strategies():
    if not USER_SYSTEM: return {"strategies": BUILTIN_STRATEGIES_V2}
    custom = user_db.get_strategies(public_only=True)
    return {"builtin": BUILTIN_STRATEGIES_V2, "community": custom,
            "total_builtin": len(BUILTIN_STRATEGIES_V2)}

@app.delete("/strategies/{strategy_id}")
def delete_strategy(strategy_id: str, user_id: str):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    user_db.delete_strategy(strategy_id, user_id)
    return {"deleted": strategy_id}

@app.get("/strategies/builtin")
def builtin_strategies():
    strategies = BUILTIN_STRATEGIES_V2 if USER_SYSTEM else []
    return {"strategies": strategies, "count": len(strategies)}

# ── ADVANCED BACKTEST ──────────────────────────────────
class AdvancedBacktestPayload(BaseModel):
    strategy: str = "STR_ORB"
    capital: float = 100000
    months: int = 3
    quantity: int = 1
    sl_pct: float = 1.0
    target_pct: float = 2.0

@app.post("/backtest/advanced")
def advanced_backtest(payload: AdvancedBacktestPayload):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    result = run_advanced_backtest(
        payload.strategy, payload.capital, payload.months,
        payload.quantity, payload.sl_pct, payload.target_pct)
    return result

@app.get("/backtest/strategies/all")
def all_backtest_strategies():
    builtin = ["EMA_CROSS","RSI_MEAN_REVERSION","BOLLINGER_BREAKOUT","EMA_RSI_COMBO","SUPERTREND_LIKE"]
    advanced = [s["id"] for s in (BUILTIN_STRATEGIES_V2 if USER_SYSTEM else [])]
    return {"classic": builtin, "advanced": advanced,
            "all": builtin + advanced, "details": BUILTIN_STRATEGIES_V2 if USER_SYSTEM else []}

@app.get("/backtest/compare")
def compare_strategies(capital: float = 100000, months: int = 3):
    """Compare all strategies side by side"""
    if not USER_SYSTEM: return {"error":"Not loaded"}
    results = []
    key_strategies = ["STR_THETA_DECAY","STR_ORB","STR_IRON_CONDOR_WEEKLY",
                      "STR_VWAP_PULLBACK","STR_GAP_FADE","STR_MAX_PAIN_EXPIRY"]
    for strat in key_strategies:
        r = run_advanced_backtest(strat, capital, months, 1, 1.0, 2.0)
        results.append({
            "strategy": strat,
            "total_pnl": r["total_pnl"],
            "total_pnl_pct": r["total_pnl_pct"],
            "win_rate": r["win_rate"],
            "max_drawdown": r["max_drawdown_pct"],
            "sharpe": r["sharpe_ratio"],
            "profit_factor": r["profit_factor"],
            "profitable_days": r["profitable_days"],
            "loss_days": r["loss_days"],
        })
    results.sort(key=lambda x: -x["total_pnl"])
    return {"capital": capital, "months": months,
            "comparison": results, "best_strategy": results[0]["strategy"]}

# ═══════════════════════════════════════
# SUBSCRIPTIONS + PAPER STRATEGY + EMAIL
# ═══════════════════════════════════════
class SubscribePayload(BaseModel):
    user_id: str; plan: str; payment_id: str = ""

class PaperTradePayload(BaseModel):
    user_id: str; strategy_id: str
    instrument: str = "NIFTY"; action: str = "BUY"
    option_type: str = "CE"; strike: int = 0
    quantity: int = 1; lot_size: int = 50
    entry_price: float = 100; stoploss: float = 0; target: float = 0

class ClosePaperTrade(BaseModel):
    trade_id: str; exit_price: float; reason: str = "MANUAL"

class StrategyNLPPayload(BaseModel):
    user_id: str; nlp_text: str
    name: str = ""; description: str = ""
    tags: List[str] = []; is_public: bool = False

@app.get("/subscriptions/plans")
def get_plans():
    if not USER_SYSTEM: return {"plans":{}}
    return {"plans": user_db.PLANS,
            "recommended": "PRO",
            "note": "All prices in INR/month"}

@app.post("/subscriptions/upgrade")
def upgrade_plan(payload: SubscribePayload):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    return user_db.upgrade_subscription(payload.user_id, payload.plan, payload.payment_id)

@app.get("/subscriptions/{user_id}")
def get_user_subscription(user_id: str):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    return user_db.get_subscription(user_id)

@app.get("/users/verify/{token}")
def verify_email(token: str):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    ok = user_db.verify_email(token)
    return {"verified": ok, "message": "Email verified! You can now login." if ok else "Invalid token"}

@app.post("/strategies/from_nlp")
def strategy_from_nlp(payload: StrategyNLPPayload):
    """Parse NLP and auto-create strategy"""
    # 1. Parse NLP
    import re
    t = payload.nlp_text.lower().strip()
    qty_m = re.search(r'(\d+)\s*(?:lot|lots)',t)
    qty = int(qty_m.group(1)) if qty_m else 1
    # Reuse existing NLP parser
    instr = ei(t)
    action = ea(t)
    strat = next((v for k,v in sorted(STRATEGIES.items(),key=lambda x:-len(x[0])) if k in t), None)
    conds = ef(CONDITIONS,t)
    exit_c = ef(EXIT_CONDS,t)
    risk_m = esl(t)
    opt_m = {k:v for k,v in OPTION_TYPES.items() if re.search(r'\b'+re.escape(k)+r'\b',t)}
    opt = list(opt_m.values())[0] if opt_m else "CE"
    expiry = next((v for k,v in sorted(EXPIRY_MAP.items(),key=lambda x:-len(x[0])) if k in t),"WEEKLY")
    ss = next((v for k,v in sorted(STRIKE_SEL.items(),key=lambda x:-len(x[0])) if k in t),None)
    et = next((v for k,v in sorted(TIME_MAP.items(),key=lambda x:-len(x[0])) if k in t),None)

    parsed = {
        "instrument": instr, "action": action, "option_type": opt,
        "expiry": expiry, "quantity": qty,
        "strategy": strat, "strike_selection": ss, "execution_time": et,
        "conditions": conds, "exit": exit_c, "risk_metrics": risk_m,
    }

    # 2. Build entry/exit condition arrays
    entry_conditions = []
    exit_conditions = []
    if conds:
        for k,v in list(conds.items())[:5]:
            if isinstance(v, dict): entry_conditions.append(f"{k} {v.get('op','>')} {v.get('val','')}")
            else: entry_conditions.append(k)
    if exit_c:
        for k,v in exit_c.items():
            if isinstance(v, dict): exit_conditions.append(f"{k} {v.get('op','>')} {v.get('val','')}")
            else: exit_conditions.append(k)
    if risk_m:
        if risk_m.get("stoploss_points"): exit_conditions.append(f"stop loss {risk_m['stoploss_points']} pts")
        if risk_m.get("target_points"): exit_conditions.append(f"target {risk_m['target_points']} pts")

    # 3. Auto-fill strategy fields
    strategy_data = {
        "name": payload.name or f"{action} {instr} {opt} - {strat or 'Custom'}",
        "description": payload.description or f"Auto-generated from: {payload.nlp_text[:100]}",
        "instrument": instr,
        "option_type": opt,
        "timeframe": "15MIN",
        "entry_conditions": entry_conditions,
        "exit_conditions": exit_conditions,
        "sl_value": risk_m.get("stoploss_points",100) if risk_m else 100,
        "target_value": risk_m.get("target_points",200) if risk_m else 200,
        "trailing_sl": risk_m.get("trailing_sl",0) if risk_m else 0,
        "quantity": qty,
        "tags": payload.tags or [instr.lower(), action.lower(), (strat or "custom").lower()],
        "is_public": payload.is_public,
        "nlp_input": payload.nlp_text,
        "parsed_nlp": parsed,
    }

    # 4. Save if user provided
    sid = None
    if payload.user_id and USER_SYSTEM:
        sid = user_db.save_strategy(payload.user_id, strategy_data)

    return {
        "parsed": parsed,
        "strategy": strategy_data,
        "strategy_id": sid,
        "message": f"Strategy auto-created from NLP input",
    }

# ── PAPER STRATEGY TRADING ──────────────────────────────
@app.post("/paper_strategy/open")
def open_paper_strategy_trade(payload: PaperTradePayload):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    tid = user_db.open_paper_trade(payload.user_id, payload.strategy_id, payload.dict())
    return {"trade_id": tid, "status": "OPEN", "strategy_id": payload.strategy_id}

@app.post("/paper_strategy/close")
def close_paper_strategy_trade(payload: ClosePaperTrade):
    if not USER_SYSTEM: return {"error":"Not loaded"}
    result = user_db.close_paper_trade(payload.trade_id, payload.exit_price, payload.reason)
    return result

@app.get("/paper_strategy/trades/{user_id}")
def get_paper_strategy_trades(user_id: str, strategy_id: str = None):
    if not USER_SYSTEM: return {"trades":[]}
    trades = user_db.get_paper_trades(user_id, strategy_id)
    return {"trades": trades, "count": len(trades)}

@app.get("/paper_strategy/performance/{strategy_id}")
def strategy_performance(strategy_id: str):
    if not USER_SYSTEM: return {}
    return user_db.get_strategy_performance(strategy_id)

# ── NOTIFICATIONS ───────────────────────────────────────
@app.get("/users/{user_id}/notifications")
def get_user_notifs(user_id: str, unread: bool = False):
    if not USER_SYSTEM: return {"notifications":[]}
    return {"notifications": user_db.get_notifications(user_id, unread)}

@app.post("/users/{user_id}/notifications/read")
def mark_read(user_id: str):
    if USER_SYSTEM: user_db.mark_notifications_read(user_id)
    return {"marked_read": True}

# ═══════════════════════════════════════════════
# ENTERPRISE MODULES: Security, Billing, AI, Legal, Admin
# ═══════════════════════════════════════════════
try:
    import sys; sys.path.insert(0, '/root/trading-server')
    from security.security_module import security, ROLES
    from billing.billing_engine import billing, PLANS
    from ai_engine.ai_strategy_engine import ai_engine
    from legal.legal_module import legal
    from admin.admin_panel import admin
    ENTERPRISE = True
    print("✅ Enterprise modules loaded")
except Exception as e:
    ENTERPRISE = False
    print(f"⚠️ Enterprise modules: {e}")

# ── SECURITY / RBAC ─────────────────────────────────────
@app.get("/security/audit/{user_id}")
def get_audit(user_id: str, limit: int = 50):
    if not ENTERPRISE: return {"logs":[]}
    return {"logs": security.get_audit(user_id, limit), "total": len(security.get_audit(user_id, limit))}

@app.get("/security/audit")
def get_all_audit(limit: int = 100):
    if not ENTERPRISE: return {"logs":[]}
    return {"logs": security.get_audit(None, limit)}

@app.post("/security/role/{user_id}")
def assign_role(user_id: str, role: str, by: str = "ADMIN"):
    if not ENTERPRISE: return {"error":"Not loaded"}
    ok = security.assign_role(user_id, role, by)
    return {"assigned": ok, "role": role}

@app.get("/security/role/{user_id}")
def get_role(user_id: str):
    if not ENTERPRISE: return {"role":"FREE_USER"}
    return {"user_id": user_id, "role": security.get_role(user_id), "available_roles": list(ROLES.keys())}

@app.get("/security/stats")
def security_stats():
    if not ENTERPRISE: return {}
    return security.admin_stats()

@app.get("/security/mfa/{user_id}")
def setup_mfa(user_id: str):
    if not ENTERPRISE: return {}
    secret = security.gen_mfa_secret(user_id)
    return {"totp_secret": secret, "qr_url": f"otpauth://totp/TRD:{user_id}?secret={secret}&issuer=TRD_v12"}

# ── BILLING ──────────────────────────────────────────────
@app.get("/billing/plans")
def get_billing_plans():
    return {"plans": PLANS if ENTERPRISE else {}, "recommended": "PRO"}

@app.post("/billing/upgrade")
def billing_upgrade(user_id: str, plan: str, payment_id: str = "", order_id: str = ""):
    if not ENTERPRISE: return {"error":"Not loaded"}
    result = billing.upgrade(user_id, plan, payment_id, order_id)
    if ENTERPRISE: security.audit(user_id, "PLAN_UPGRADED", f"plan:{plan}", details={"plan":plan,"payment":payment_id})
    return result

@app.get("/billing/subscription/{user_id}")
def get_billing_sub(user_id: str):
    if not ENTERPRISE: return {}
    return billing.get_subscription(user_id)

@app.get("/billing/invoices/{user_id}")
def get_invoices(user_id: str):
    if not ENTERPRISE: return {"invoices":[]}
    return {"invoices": billing.get_invoices(user_id)}

@app.post("/billing/razorpay/order")
def create_razorpay_order(user_id: str, plan: str):
    if not ENTERPRISE: return {}
    return billing.create_razorpay_order(user_id, plan)

@app.get("/billing/revenue")
def revenue_stats():
    if not ENTERPRISE: return {}
    return billing.admin_revenue_stats()

# ── AI ENGINE ────────────────────────────────────────────
@app.get("/ai/status")
def ai_status():
    if not ENTERPRISE: return {"status":"NOT_LOADED"}
    return ai_engine.engine_status()

@app.post("/ai/evolve")
def ai_evolve(generations: int = 5):
    if not ENTERPRISE: return {"error":"Not loaded"}
    strategies = ai_engine.evolve_strategies(generations)
    return {"evolved": len(strategies), "strategies": strategies[:5], "message": f"Evolved {len(strategies)} strategies in {generations} generations"}

@app.get("/ai/strategies")
def ai_get_strategies(status: str = None, min_wr: float = 0):
    if not ENTERPRISE: return {"strategies":[]}
    return {"strategies": ai_engine.get_strategies(status, min_wr)}

@app.get("/ai/strategies/approved")
def ai_approved():
    if not ENTERPRISE: return {"strategies":[]}
    return {"strategies": ai_engine.get_approved_strategies()}

@app.get("/ai/signal/{instrument}")
def ai_signal(instrument: str = "NIFTY"):
    if not ENTERPRISE: return {}
    return ai_engine.generate_signal(instrument)

@app.get("/ai/regime")
def ai_regime(vix: float = 19.5):
    if not ENTERPRISE: return {}
    return ai_engine.detect_regime(vix)

@app.post("/ai/paper_test/{strategy_id}")
def advance_paper_test(strategy_id: str, days: int = 1):
    if not ENTERPRISE: return {}
    return ai_engine.advance_paper_test(strategy_id, days)

# ── LEGAL ────────────────────────────────────────────────
@app.get("/legal/{doc_type}")
def get_legal_doc(doc_type: str):
    if not ENTERPRISE: return {}
    return legal.get_doc(doc_type)

@app.post("/legal/consent")
def record_consent(user_id: str, consent_type: str, version: str = "1.0"):
    if not ENTERPRISE: return {}
    result = legal.record_consent(user_id, consent_type, version)
    if ENTERPRISE: security.audit(user_id, "CONSENT_GIVEN", consent_type, details={"version":version})
    return result

@app.get("/legal/consents/{user_id}")
def get_consents(user_id: str):
    if not ENTERPRISE: return {"consents":[]}
    return {"consents": legal.get_consents(user_id), "risk_signed": legal.has_signed_risk_disclosure(user_id)}

# ── ADMIN ────────────────────────────────────────────────
@app.get("/admin/dashboard")
def admin_dashboard():
    if not ENTERPRISE: return {}
    return admin.get_dashboard()

@app.get("/admin/users")
def admin_users(limit: int = 50):
    if not ENTERPRISE: return {"users":[]}
    return {"users": admin.get_user_list(limit)}

@app.get("/admin/health")
def admin_health():
    if not ENTERPRISE: return {}
    return admin.system_health()

# ═══════════════════════════════════════════════
# NOTIFICATIONS + AI CARE + PWA
# ═══════════════════════════════════════════════
try:
    from notifications.notification_engine import notif_engine
    from ai_care.ai_care import ai_care
    CARE_SYSTEM = True
    print("✅ Care system loaded")
except Exception as e:
    CARE_SYSTEM = False
    print(f"⚠️ Care system: {e}")

# NOTIFICATIONS
@app.get("/notifications/{user_id}")
def get_notifications(user_id: str, unread_only: bool = False, limit: int = 30):
    if not CARE_SYSTEM: return {"notifications": [], "unread": 0}
    notifs = notif_engine.get_all(user_id, unread_only, limit)
    return {"notifications": notifs, "unread": notif_engine.unread_count(user_id)}

@app.post("/notifications/{user_id}/read")
def mark_notifications_read(user_id: str, notif_id: int = None):
    if CARE_SYSTEM: notif_engine.mark_read(user_id, notif_id)
    return {"marked": True}

@app.get("/notifications/{user_id}/prefs")
def get_notif_prefs(user_id: str):
    if not CARE_SYSTEM: return {}
    return notif_engine.get_prefs(user_id)

@app.post("/notifications/{user_id}/prefs")
def save_notif_prefs(user_id: str, prefs: dict):
    if CARE_SYSTEM: notif_engine.save_prefs(user_id, prefs)
    return {"saved": True}

@app.post("/notifications/send")
def send_notification(user_id: str, notif_type: str, title: str, message: str):
    if not CARE_SYSTEM: return {"id": 0}
    nid = notif_engine.send(user_id, notif_type, title, message)
    return {"id": nid, "sent": True}

# AI CUSTOMER CARE
class ChatMessage(BaseModel):
    user_id: str; message: str

@app.post("/care/chat")
def ai_chat(payload: ChatMessage):
    if not CARE_SYSTEM: return {"response": "Support system loading..."}
    return ai_care.chat(payload.user_id, payload.message)

@app.get("/care/history/{user_id}")
def chat_history(user_id: str, limit: int = 30):
    if not CARE_SYSTEM: return {"history": []}
    return {"history": ai_care.get_history(user_id, limit)}

@app.post("/care/feedback")
def care_feedback(user_id: str, message_id: int, helpful: bool):
    if CARE_SYSTEM: ai_care.save_feedback(user_id, message_id, helpful)
    return {"saved": True}

# PWA manifest
@app.get("/manifest.json")
def pwa_manifest():
    return {
        "name": "TRD v12.3 — Institutional Trading",
        "short_name": "TRD",
        "description": "Professional Derivative Trading Platform",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#060608",
        "theme_color": "#00ff88",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ],
        "categories": ["finance", "trading"],
        "screenshots": []
    }

# ═══════════════════════════════════════════════════════
# AI CUSTOMER CARE + NOTIFICATIONS
# ═══════════════════════════════════════════════════════
try:
    from ai_engine.customer_care import care
    CARE_LOADED = True
except Exception as e:
    CARE_LOADED = False
    print(f"Customer care: {e}")

class ChatMessage(BaseModel):
    user_id: str = "guest"
    message: str
    user_name: str = "Friend"

@app.post("/support/chat")
def customer_care_chat(payload: ChatMessage):
    """AI Customer Care — Hybrid KB + NLP"""
    if not CARE_LOADED:
        return {
            "response": "Support temporarily unavailable. Please try again shortly. 🙏",
            "kb_hit": False,
            "suggestions": ["Email: support@trd.app"]
        }
    result = care.chat(payload.user_id, payload.message, payload.user_name)
    return result

@app.get("/support/suggestions")
def get_suggestions():
    """Pre-loaded quick questions"""
    return {
        "categories": [
            {
                "name": "🚀 Getting Started",
                "questions": ["How to place first trade?", "NLP trading kaise karein?", "Paper trading guide"]
            },
            {
                "name": "💳 Subscription",
                "questions": ["FREE vs PRO difference?", "Plan upgrade kaise karein?", "Refund policy?"]
            },
            {
                "name": "🤖 AI Engine",
                "questions": ["AI signals kaise kaam karte hain?", "Strategy evolve kaise karein?", "Circuit breaker kya hai?"]
            },
            {
                "name": "⚡ Risk & Safety",
                "questions": ["Kill switch kya hai?", "Position size calculator", "Daily loss limit set karna"]
            },
            {
                "name": "📊 Strategies",
                "questions": ["Best high win-rate strategy?", "NLP strategy builder guide", "Backtest kaise interpret karein?"]
            },
            {
                "name": "🔧 Technical",
                "questions": ["App offline hai?", "Login nahi ho raha", "Data refresh kaise karein?"]
            }
        ]
    }

# Notification endpoints
class NotificationPayload(BaseModel):
    user_id: str
    title: str
    body: str
    type: str = "INFO"
    url: str = "/"

@app.post("/notifications/send")
def send_notification(payload: NotificationPayload):
    """Send push notification to user"""
    # In production: integrate with FCM/APNs
    return {
        "sent": True,
        "channel": "push",
        "title": payload.title,
        "body": payload.body,
        "note": "FCM integration required for actual push delivery"
    }

@app.get("/notifications/config")
def notification_config():
    return {
        "vapid_public_key": "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U",
        "fcm_sender_id": "123456789",
        "note": "Replace with actual VAPID keys for production push notifications"
    }


# CF BYPASS MIDDLEWARE
@app.middleware("http")  
async def cf_bypass_mw(request, call_next):
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        return Response(headers={
            "Access-Control-Allow-Origin":"*",
            "Access-Control-Allow-Methods":"*",
            "Access-Control-Allow-Headers":"*",
        })
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
