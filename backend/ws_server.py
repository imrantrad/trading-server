"""WebSocket Server v12.3 — Real-time data push to frontend"""
import json, time, asyncio, random
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()
        self.prices = {"NIFTY":22450,"BANKNIFTY":48300,"FINNIFTY":21100,
                       "SENSEX":73800,"USDINR":83.4,"VIX":14.2}

    async def connect(self, ws: WebSocket):
        await ws.accept(); self.active.add(ws)
        await self.send_one(ws, {"type":"CONNECTED","msg":"WebSocket connected","ts":time.strftime("%H:%M:%S")})

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def send_one(self, ws: WebSocket, data: dict):
        try: await ws.send_json(data)
        except: self.active.discard(ws)

    async def broadcast(self, data: dict):
        disconnected = set()
        for ws in list(self.active):
            try: await ws.send_json(data)
            except: disconnected.add(ws)
        self.active -= disconnected

    async def tick_loop(self):
        """Send price ticks every 2 seconds"""
        while True:
            for k in self.prices:
                self.prices[k] = round(self.prices[k]*(1+(random.random()-0.5)*0.0003),2)
            await self.broadcast({
                "type":"TICK","prices":self.prices,"ts":time.strftime("%H:%M:%S")
            })
            await asyncio.sleep(2)

    async def push_trade(self, trade: dict):
        await self.broadcast({"type":"TRADE","data":trade,"ts":time.strftime("%H:%M:%S")})

    async def push_signal(self, signal: dict):
        await self.broadcast({"type":"SIGNAL","data":signal,"ts":time.strftime("%H:%M:%S")})

    async def push_alert(self, alert: dict):
        await self.broadcast({"type":"ALERT","data":alert,"ts":time.strftime("%H:%M:%S")})

    async def push_pnl(self, pnl_data: dict):
        await self.broadcast({"type":"PNL","data":pnl_data,"ts":time.strftime("%H:%M:%S")})


ws_manager = ConnectionManager()
