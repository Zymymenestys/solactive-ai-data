#!/usr/bin/env python3
"""Download and validate Solactive DE000SL0K4X5 daily history."""
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen

ISIN = "DE000SL0K4X5"
URL = "https://www.solactive.com/_actions/getDayHistoryChartData/"
TZ = ZoneInfo("Europe/Berlin")
OUT = Path("data")

def get_data():
    body = json.dumps({"dayDate": int(time.time() * 1000),
                       "indexCreatingTimeStamp": 0, "isin": ISIN}).encode()
    req = Request(URL, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://www.solactive.com",
        "Referer": f"https://www.solactive.com/index/{ISIN}/",
        "User-Agent": "Mozilla/5.0"}, method="POST")
    with urlopen(req, timeout=60) as res:
        assert res.status == 200
        return json.load(res)

def decode(data):
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        data = data["data"]
    if not isinstance(data, list) or not isinstance(data[0], list):
        raise ValueError("Unrecognized Solactive format")
    result = {}
    for idx in data[0]:
        row = data[idx]
        if data[row["indexId"]] != ISIN:
            continue
        day = datetime.fromtimestamp(data[row["timestamp"]] / 1000, TZ).date().isoformat()
        value = round(float(data[row["value"]]), 2)
        if not (0 < value < 10000000):
            raise ValueError("Invalid value")
        if day in result and result[day] != value:
            raise ValueError("Conflicting values")
        result[day] = value
    points = [{"date": d, "value": v} for d, v in sorted(result.items())]
    if len(points) < 250:
        raise ValueError("Too few records")
    last_day = date.fromisoformat(points[-1]["date"])
    if last_day > datetime.now(TZ).date() or (datetime.now(TZ).date()-last_day).days > 7:
        raise ValueError("Latest quote outside expected date range")
    return points

def year_ago(d):
    try:
        return d.replace(year=d.year-1)
    except ValueError:
        return d.replace(year=d.year-1, day=28)

def save(name, payload):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))+"\n")

def main():
    error = None
    for trial in range(3):
        try:
            points = decode(get_data())
            break
        except Exception as e:
            error = e
            print(f"Attempt {trial+1}/3: {e}")
            if trial < 2:
                time.sleep(5*(trial+1))
    else:
        raise RuntimeError(f"Cannot retrieve current Solactive history: {error}")
    last = points[-1]
    last_date = date.fromisoformat(last["date"])
    meta = {"isin": ISIN, "observed_through": last["date"],
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": f"https://www.solactive.com/index/{ISIN}/"}
    periods = {"solactive-history.json": points,
               "solactive-30d.json": points[-30:],
               "solactive-12m.json": [p for p in points if p["date"] >= year_ago(last_date).isoformat()]}
    for file, rows in periods.items():
        save(file, {**meta, "count": len(rows), "points": rows})
    def compare(reference):
        return {"date": reference["date"], "value": reference["value"],
                "change_pct": round((last["value"]/reference["value"]-1)*100, 2)}
    def at_or_before(d):
        return next((p for p in reversed(points) if p["date"] <= d.isoformat()), None)
    comparisons = {"previous_trading_day": compare(points[-2])}
    for key, target in [("7_calendar_days", last_date-timedelta(days=7)),
                        ("30_calendar_days", last_date-timedelta(days=30)),
                        ("12_months", year_ago(last_date))]:
        item = at_or_before(target)
        comparisons[key] = compare(item) if item else None
    save("solactive-summary.json", {**meta, "latest": last,
                                  "total_history_records": len(points),
                                  "comparisons": comparisons})
    print(f"SUCCESS {len(points)} records through {last['date']}: {last['value']}")

if __name__ == "__main__":
    main()
