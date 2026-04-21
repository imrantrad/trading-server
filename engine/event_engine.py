class EventEngine:
    def __init__(self):
        self.subs = []
    def register(self, s):
        self.subs.append(s)
    def on_tick(self, tick):
        for s in self.subs:
            s.process(tick)
