"""
Notification System v12.3
Telegram, Email, Webhook alerts
"""
import time
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Notification:
    type: str        # TRADE, SIGNAL, RISK, SYSTEM, ALERT
    level: str       # INFO, SUCCESS, WARNING, CRITICAL
    title: str
    message: str
    timestamp: str = ""
    sent: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%H:%M:%S")


class NotificationEngine:
    def __init__(self):
        self.telegram_token = ""
        self.telegram_chat_id = ""
        self.webhook_url = ""
        self.notifications: List[Notification] = []
        self.enabled = {"telegram": False, "webhook": False, "log": True}
        self.filters = {"min_level": "INFO"}  # INFO/WARNING/CRITICAL

    def configure_telegram(self, token: str, chat_id: str):
        self.telegram_token = token
        self.telegram_chat_id = chat_id
        self.enabled["telegram"] = bool(token and chat_id)

    def configure_webhook(self, url: str):
        self.webhook_url = url
        self.enabled["webhook"] = bool(url)

    def send(self, notif: Notification) -> bool:
        self.notifications.append(notif)
        success = True

        if self.enabled["telegram"]:
            success &= self._send_telegram(notif)

        if self.enabled["webhook"]:
            success &= self._send_webhook(notif)

        notif.sent = success
        return success

    def _send_telegram(self, notif: Notification) -> bool:
        try:
            import urllib.request, json
            emoji = {"INFO":"ℹ️","SUCCESS":"✅","WARNING":"⚠️","CRITICAL":"🚨"}.get(notif.level,"📢")
            msg = f"{emoji} *{notif.title}*\n{notif.message}\n_{notif.timestamp}_"
            data = json.dumps({"chat_id":self.telegram_chat_id,"text":msg,"parse_mode":"Markdown"}).encode()
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception as e:
            print(f"Telegram error: {e}")
            return False

    def _send_webhook(self, notif: Notification) -> bool:
        try:
            import urllib.request, json
            data = json.dumps({"type":notif.type,"level":notif.level,
                "title":notif.title,"message":notif.message,"ts":notif.timestamp}).encode()
            req = urllib.request.Request(self.webhook_url, data=data,
                headers={"Content-Type":"application/json"})
            urllib.request.urlopen(req, timeout=5)
            return True
        except:
            return False

    # Shortcuts
    def trade_executed(self, instrument, action, price, pnl=None):
        msg = f"{action} {instrument} @ ₹{price}"
        if pnl: msg += f" | P&L: ₹{pnl:+.0f}"
        self.send(Notification("TRADE","SUCCESS","Trade Executed",msg))

    def sl_hit(self, instrument, price, pnl):
        self.send(Notification("TRADE","WARNING","Stop Loss Hit",
            f"{instrument} SL @ ₹{price} | Loss: ₹{pnl:.0f}"))

    def target_hit(self, instrument, price, pnl):
        self.send(Notification("TRADE","SUCCESS","Target Hit",
            f"{instrument} Target @ ₹{price} | Profit: ₹{pnl:.0f}"))

    def risk_alert(self, msg):
        self.send(Notification("RISK","CRITICAL","Risk Alert",msg))

    def daily_loss_limit(self, loss, limit):
        self.send(Notification("RISK","CRITICAL","Daily Loss Limit",
            f"Loss ₹{loss:.0f} hit limit ₹{limit:.0f}"))

    def kill_switch(self, reason):
        self.send(Notification("SYSTEM","CRITICAL","KILL SWITCH ACTIVATED",
            f"All trading halted: {reason}"))

    def signal_generated(self, instrument, signal, confidence):
        self.send(Notification("SIGNAL","INFO","New Signal",
            f"{signal} {instrument} | Confidence: {confidence:.0%}"))

    def get_recent(self, limit=20):
        return [{"type":n.type,"level":n.level,"title":n.title,
                 "message":n.message,"timestamp":n.timestamp,"sent":n.sent}
                for n in self.notifications[-limit:]]


notifier = NotificationEngine()
