#!/usr/bin/env python3
"""MANU scheduled paper bot. PUBLIC market data; NEVER submits orders."""
import datetime as dt, json, os, urllib.request
from pathlib import Path
SYMBOLS=("FETUSDT","VIRTUALUSDT","RENDERUSDT","TAOUSDT","ARKMUSDT")
PATH=Path("paper_state.json")
FEE=0.001
SLIP=0.001
def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"MANU-Paper-Simulator/1.0"})
    with urllib.request.urlopen(req,timeout=15) as r: return json.load(r)
def initial():
    return {"mode":"PAPER_ONLY","cash_brl":50.0,"positions":{},"trades":[],"last_candles":{},"updated_at":None,"quotes":{},"status":"awaiting_first_run"}
def run():
    state=json.loads(PATH.read_text()) if PATH.exists() else initial()
    if state.get("mode")!="PAPER_ONLY": raise RuntimeError("Invalid mode")
    now=dt.datetime.now(dt.timezone.utc)
    fx=float(fetch("https://api.binance.com/api/v3/ticker/price?symbol=USDTBRL")["price"])
    if not 1<fx<100: raise ValueError("Bad FX quote")
    # Fail closed if ANY feed fails; do not partially update state.
    feeds={}
    for symbol in SYMBOLS:
        rows=fetch("https://api.binance.com/api/v3/klines?symbol="+symbol+"&interval=15m&limit=25")
        if len(rows)<22: raise ValueError("Insufficient history "+symbol)
        closed=rows[:-1]
        ts=int(closed[-1][0])
        if now.timestamp()*1000-int(closed[-1][6])>45*60*1000: raise ValueError("Stale candles "+symbol)
        feeds[symbol]=(ts,[float(r[4]) for r in closed],float(closed[-1][4]))
    today=now.date().isoformat()
    realized_today=sum(t.get("pnl_brl",0) for t in state["trades"] if t["side"]=="SELL" and t["at"].startswith(today))
    for symbol,(ts,closes,price) in feeds.items():
        state["quotes"][symbol]={"price_usdt":price,"closed_candle_ms":ts}
        if ts<=state["last_candles"].get(symbol,0): continue
        state["last_candles"][symbol]=ts
        sma5=sum(closes[-5:])/5
        sma20=sum(closes[-20:])/20
        p=state["positions"].get(symbol)
        if p:
            move=price/p["entry_usdt"]-1
            reason="STOP" if move<=-0.02 else "TARGET" if move>=0.03 else "SMA_EXIT" if sma5<sma20 else None
            if reason:
                proceeds=p["qty"]*price*fx*(1-FEE)*(1-SLIP)
                pnl=proceeds-p["cost_brl"]
                state["cash_brl"]+=proceeds
                del state["positions"][symbol]
                state["trades"].append({"at":now.isoformat(),"symbol":symbol,"side":"SELL","price_usdt":price,"pnl_brl":round(pnl,5),"reason":reason})
                realized_today+=pnl
        elif sma5>sma20 and state["cash_brl"]>=10 and realized_today>-2:
            # A maximum of five independent simulated positions, one per symbol.
            qty=(10/fx)/price*(1-FEE)*(1-SLIP)
            state["cash_brl"]-=10
            state["positions"][symbol]={"entry_usdt":price,"qty":qty,"cost_brl":10,"opened_at":now.isoformat()}
            state["trades"].append({"at":now.isoformat(),"symbol":symbol,"side":"BUY","price_usdt":price,"pnl_brl":0,"reason":"SMA_ENTRY"})
    equity=state["cash_brl"]+sum(p["qty"]*feeds[s][2]*fx*(1-FEE)*(1-SLIP) for s,p in state["positions"].items())
    state["equity_brl"]=round(equity,5)
    state["cash_brl"]=round(state["cash_brl"],5)
    state["updated_at"]=now.isoformat()
    state["status"]="ok"
    state["trades"]=state["trades"][-100:]
    PATH.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n")
    print("PAPER ONLY",state["updated_at"],"equity",state["equity_brl"],"positions",len(state["positions"]))
if __name__=="__main__": run()
