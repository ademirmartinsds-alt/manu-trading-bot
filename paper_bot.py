#!/usr/bin/env python3
"""MANU Trading Bot V3: public Binance Spot data + paper trading ONLY.
No account access, credentials, signed requests, or order endpoints.
"""
import json, os, sqlite3, time, urllib.request
from datetime import datetime, timezone

SYMBOLS = ("FETUSDT", "VIRTUALUSDT", "RENDERUSDT", "TAOUSDT", "ARKMUSDT")
DB = os.getenv("MANU_DB", "manu_paper.sqlite3")
INTERVAL = int(os.getenv("MANU_POLL_SECONDS", "60"))
FEE = 0.001
SLIPPAGE = 0.001
MAX_POSITION_BRL = 10.0
START_BRL = 50.0
DAILY_LOSS_LIMIT_BRL = 2.0
STOP_PCT = 0.02
TARGET_PCT = 0.03

def public_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"MANU-PaperBot/0.3"})
    with urllib.request.urlopen(req, timeout=12) as response:
        return json.load(response)

def candles(symbol):
    url = "https://api.binance.com/api/v3/klines?symbol="+symbol+"&interval=1m&limit=40"
    data = public_json(url)
    # Last candle may still be forming. Only use closed candles.
    return [(int(row[0]),float(row[4]),float(row[7])) for row in data[:-1]]

def brl_per_usdt():
    data = public_json("https://api.binance.com/api/v3/ticker/price?symbol=USDTBRL")
    return float(data["price"])

def init(db):
    db.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS positions (symbol TEXT PRIMARY KEY, entry REAL,qty REAL,cost_brl REAL,opened INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT,ts TEXT,symbol TEXT,side TEXT,price REAL,amount_brl REAL,pnl_brl REAL,reason TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS seen (symbol TEXT PRIMARY KEY,candle INTEGER)")
    db.execute("INSERT OR IGNORE INTO meta VALUES ('cash','50')")
    db.commit()

def cash(db):
    return float(db.execute("SELECT value FROM meta WHERE key='cash'").fetchone()[0])

def set_cash(db,value):
    db.execute("UPDATE meta SET value=? WHERE key='cash'",(str(value),))

def daily_pnl(db):
    today=datetime.now(timezone.utc).date().isoformat()
    return float(db.execute("SELECT COALESCE(SUM(pnl_brl),0) FROM trades WHERE side='SELL' AND substr(ts,1,10)=?",(today,)).fetchone()[0])

def log(db,symbol,side,price,amount,pnl,reason):
    db.execute("INSERT INTO trades(ts,symbol,side,price,amount_brl,pnl_brl,reason) VALUES(?,?,?,?,?,?,?)",
               (datetime.now(timezone.utc).isoformat(),symbol,side,price,amount,pnl,reason))

def cycle(db):
    fx=brl_per_usdt()
    if not (1<fx<100):
        raise ValueError("Invalid USDTBRL quote")
    for symbol in SYMBOLS:
        try:
            rows=candles(symbol)
            if len(rows)<25: continue
            stamp,price,_=rows[-1]
            seen=db.execute("SELECT candle FROM seen WHERE symbol=?",(symbol,)).fetchone()
            if seen and stamp<=seen[0]: continue
            db.execute("INSERT OR REPLACE INTO seen VALUES (?,?)",(symbol,stamp))
            pos=db.execute("SELECT entry,qty,cost_brl FROM positions WHERE symbol=?",(symbol,)).fetchone()
            short=sum(x[1] for x in rows[-5:])/5
            long=sum(x[1] for x in rows[-20:])/20
            if pos:
                entry,qty,cost=pos
                move=price/entry-1
                reason=("STOP" if move<=-STOP_PCT else "TARGET" if move>=TARGET_PCT else "MA_CROSS" if short<long else None)
                if reason:
                    proceeds=qty*price*fx*(1-FEE)*(1-SLIPPAGE)
                    pnl=proceeds-cost
                    set_cash(db,cash(db)+proceeds)
                    db.execute("DELETE FROM positions WHERE symbol=?",(symbol,))
                    log(db,symbol,"SELL",price,proceeds,pnl,reason)
                    print(symbol,"PAPER SELL",reason,round(pnl,3),flush=True)
            elif daily_pnl(db)>-DAILY_LOSS_LIMIT_BRL and short>long and cash(db)>=MAX_POSITION_BRL:
                # Simplified paper fills; never places an exchange order.
                cost=MAX_POSITION_BRL
                qty=(cost/fx)/price*(1-FEE)*(1-SLIPPAGE)
                set_cash(db,cash(db)-cost)
                db.execute("INSERT INTO positions VALUES (?,?,?,?,?)",(symbol,price,qty,cost,stamp))
                log(db,symbol,"BUY",price,cost,None,"MA_CROSS")
                print(symbol,"PAPER BUY",flush=True)
            db.commit()
        except Exception as exc:
            print("Symbol error",symbol,str(exc),flush=True)

def main():
    db=sqlite3.connect(DB)
    init(db)
    print("PAPER MODE ONLY; no Binance trading API, no real orders",flush=True)
    while True:
        try: cycle(db)
        except Exception as exc: print("Cycle error",str(exc),flush=True)
        time.sleep(max(30,INTERVAL))

if __name__=="__main__": main()
