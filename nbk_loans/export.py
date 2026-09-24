"""Выгружает данные Нацбанка в data.json для статической страницы (GitHub Pages)."""
import json
from datetime import datetime, timezone
from pathlib import Path

import nbk

OUT = Path(__file__).with_name("data.json")


def main():
    df = nbk.load_all()
    data = {}
    for (sheet, period), grp in df.groupby(["sheet", "period"]):
        data.setdefault(sheet, {})[period.strftime("%Y-%m")] = {
            r.region: round(r.value, 3) for r in grp.itertuples()
        }
    if OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        if old.get("data") == json.loads(json.dumps(data)):
            print(f"{OUT.name}: без изменений")
            return
    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "sheets": nbk.SHEETS,
        "data": data,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{OUT.name}: {sum(len(v) for v in data.values())} периодов")


if __name__ == "__main__":
    main()
