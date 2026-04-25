"""Job Scheduler v12.3 — Time-based strategy execution"""
import time, threading
from typing import List, Dict, Callable
from dataclasses import dataclass, field


@dataclass
class ScheduledJob:
    id: str; name: str; schedule_time: str  # "09:20", "15:15"
    func: Callable; args: dict = field(default_factory=dict)
    days: List[str] = field(default_factory=lambda: ["MON","TUE","WED","THU","FRI"])
    enabled: bool = True; last_run: str = ""; run_count: int = 0
    one_time: bool = False


class JobScheduler:
    def __init__(self):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self._thread: threading.Thread = None
        self.log: List[dict] = []

    def add_job(self, job_id: str, name: str, schedule_time: str,
                func: Callable, args: dict = None, one_time: bool = False) -> str:
        job = ScheduledJob(id=job_id, name=name, schedule_time=schedule_time,
                           func=func, args=args or {}, one_time=one_time)
        self.jobs[job_id] = job
        return job_id

    def remove_job(self, job_id: str): self.jobs.pop(job_id, None)
    def enable(self, job_id: str): self.jobs[job_id].enabled = True if job_id in self.jobs else None
    def disable(self, job_id: str): self.jobs[job_id].enabled = False if job_id in self.jobs else None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self): self.running = False

    def _run(self):
        while self.running:
            now = time.strftime("%H:%M")
            day = time.strftime("%a").upper()[:3]
            for job in list(self.jobs.values()):
                if not job.enabled: continue
                if day not in job.days: continue
                if now == job.schedule_time and job.last_run != now:
                    try:
                        job.func(**job.args)
                        job.last_run = now; job.run_count += 1
                        self.log.append({"job":job.name,"time":now,"status":"SUCCESS"})
                        if job.one_time: job.enabled = False
                    except Exception as e:
                        self.log.append({"job":job.name,"time":now,"status":"ERROR","error":str(e)})
            time.sleep(30)

    def get_jobs(self) -> List[dict]:
        return [{"id":j.id,"name":j.name,"schedule":j.schedule_time,
                 "enabled":j.enabled,"last_run":j.last_run,"run_count":j.run_count}
                for j in self.jobs.values()]

    def get_log(self, limit=50) -> List[dict]:
        return self.log[-limit:]

    # Built-in jobs
    def add_default_jobs(self, scanner_fn, eod_fn, report_fn):
        self.add_job("scan_open","Morning Scan","09:20",scanner_fn)
        self.add_job("scan_mid","Mid-day Scan","12:00",scanner_fn)
        self.add_job("eod_close","EOD Auto-Close","15:15",eod_fn)
        self.add_job("eod_report","EOD Report","15:30",report_fn)


scheduler = JobScheduler()
