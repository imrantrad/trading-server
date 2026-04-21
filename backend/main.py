from fastapi import FastAPI
from nlp.parser import parse_strategy
from risk.risk_engine import RiskEngine
from live.execution_router import ExecutionRouter

app = FastAPI()

risk_engine = RiskEngine()
router = ExecutionRouter()

@app.post('/strategy')
def strategy(payload: dict):
    return parse_strategy(payload['text'])

@app.post('/trade')
def trade(strategy: dict):
    if not risk_engine.validate(strategy):
        return {'status': 'REJECTED'}
    return router.execute(strategy)
