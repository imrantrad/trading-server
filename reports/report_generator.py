"""P&L Report Generator v12.3"""
import time
from typing import List, Dict


class ReportGenerator:
    def __init__(self): self.reports: List[dict] = []

    def daily_pnl_report(self, trades: List[dict], capital: float = 500000) -> dict:
        today = time.strftime("%Y-%m-%d")
        today_trades = [t for t in trades if t.get("exit_time","").startswith(today[:10]) or True][:20]
        total_pnl = sum(t.get("net_pnl",0) for t in today_trades)
        wins = [t for t in today_trades if t.get("net_pnl",0)>0]
        losses = [t for t in today_trades if t.get("net_pnl",0)<0]
        brokerage = sum(t.get("brokerage",40) for t in today_trades)
        report = {
            "report_type":"DAILY_PNL","date":today,
            "summary":{
                "total_trades":len(today_trades),"wins":len(wins),"losses":len(losses),
                "win_rate":round(len(wins)/len(today_trades)*100 if today_trades else 0,1),
                "gross_pnl":round(sum(t.get("gross_pnl",0) for t in today_trades),0),
                "brokerage":round(brokerage,0),
                "net_pnl":round(total_pnl,0),
                "pnl_pct":round(total_pnl/capital*100,2),
                "best_trade":round(max((t.get("net_pnl",0) for t in today_trades),default=0),0),
                "worst_trade":round(min((t.get("net_pnl",0) for t in today_trades),default=0),0),
            },
            "by_instrument": self._group_by(today_trades,"instrument"),
            "by_strategy": self._group_by(today_trades,"strategy"),
            "trades":today_trades[:10],
            "generated_at":time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.reports.append(report)
        return report

    def weekly_report(self, trades: List[dict]) -> dict:
        wins = [t for t in trades if t.get("net_pnl",0)>0]
        losses = [t for t in trades if t.get("net_pnl",0)<0]
        total = sum(t.get("net_pnl",0) for t in trades)
        aw = sum(t.get("net_pnl",0) for t in wins)/len(wins) if wins else 0
        al = sum(t.get("net_pnl",0) for t in losses)/len(losses) if losses else 0
        return {
            "report_type":"WEEKLY","period":"Last 7 days",
            "total_trades":len(trades),"wins":len(wins),"losses":len(losses),
            "win_rate":round(len(wins)/len(trades)*100 if trades else 0,1),
            "net_pnl":round(total,0),
            "avg_win":round(aw,0),"avg_loss":round(al,0),
            "profit_factor":round(abs(aw*len(wins))/(abs(al)*len(losses)+1),2),
            "expectancy":round((len(wins)/len(trades)*aw)+(len(losses)/len(trades)*al) if trades else 0,0),
            "by_instrument":self._group_by(trades,"instrument"),
            "by_strategy":self._group_by(trades,"strategy"),
            "generated_at":time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def performance_report(self, trades: List[dict], capital: float = 500000) -> dict:
        if not trades: return {"error":"No trades found"}
        pnls = [t.get("net_pnl",0) for t in trades]
        cumulative = []
        running = capital
        for p in pnls:
            running += p; cumulative.append(running)
        peak = capital; max_dd = 0; max_dd_pct = 0
        for c in cumulative:
            peak = max(peak,c)
            dd = (peak-c)/peak*100; max_dd_pct = max(max_dd_pct,dd)
        wins = [p for p in pnls if p>0]; losses = [p for p in pnls if p<0]
        aw = sum(wins)/len(wins) if wins else 0
        al = sum(losses)/len(losses) if losses else 0
        wr = len(wins)/len(pnls)
        expectancy = wr*aw + (1-wr)*al
        returns = [p/capital for p in pnls]
        avg_r = sum(returns)/len(returns) if returns else 0
        std_r = (sum((r-avg_r)**2 for r in returns)/len(returns))**0.5 if returns else 1
        sharpe = avg_r/std_r*(252**0.5) if std_r else 0
        return {
            "report_type":"PERFORMANCE","total_trades":len(trades),
            "winning_trades":len(wins),"losing_trades":len(losses),
            "win_rate":round(wr*100,1),
            "total_pnl":round(sum(pnls),0),
            "total_pnl_pct":round(sum(pnls)/capital*100,2),
            "avg_win":round(aw,0),"avg_loss":round(al,0),
            "profit_factor":round(abs(aw*len(wins))/(abs(al)*len(losses)+1),2),
            "expectancy_per_trade":round(expectancy,0),
            "max_drawdown_pct":round(max_dd_pct,2),
            "sharpe_ratio":round(sharpe,2),
            "best_trade":round(max(pnls),0),"worst_trade":round(min(pnls),0),
            "avg_trade":round(sum(pnls)/len(pnls),0),
            "equity_curve":cumulative[-20:],
            "generated_at":time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _group_by(self, trades, key) -> dict:
        groups = {}
        for t in trades:
            k = t.get(key,"OTHER")
            if k not in groups: groups[k] = {"count":0,"pnl":0}
            groups[k]["count"] += 1; groups[k]["pnl"] += t.get("net_pnl",0)
        return {k:{"count":v["count"],"pnl":round(v["pnl"],0)} for k,v in groups.items()}

    def expiry_calendar(self) -> dict:
        """Next expiry dates"""
        import calendar
        from datetime import datetime, timedelta
        now = datetime.now()
        def next_thursday(d):
            days = (3-d.weekday())%7
            if days == 0: days = 7
            return d + timedelta(days=days)
        def last_thursday(year, month):
            last_day = calendar.monthrange(year, month)[1]
            d = datetime(year, month, last_day)
            while d.weekday() != 3: d -= timedelta(days=1)
            return d
        weekly = next_thursday(now)
        monthly = last_thursday(now.year, now.month)
        if monthly <= now: monthly = last_thursday(now.year if now.month<12 else now.year+1,
                                                    now.month%12+1)
        return {
            "today": now.strftime("%Y-%m-%d"),
            "nifty_weekly_expiry": weekly.strftime("%Y-%m-%d"),
            "banknifty_weekly_expiry": weekly.strftime("%Y-%m-%d"),
            "nifty_monthly_expiry": monthly.strftime("%Y-%m-%d"),
            "days_to_weekly": (weekly-now).days,
            "days_to_monthly": (monthly-now).days,
            "theta_warning": "HIGH THETA DECAY" if (weekly-now).days <= 2 else "NORMAL",
        }


reporter = ReportGenerator()
