#!/usr/bin/env python3
"""開獎前鎖定下期預測。

在每期開獎『之前』執行：用目前所有已開獎資料預測「下一期」，
把 4 種策略的預測號碼 + 鎖定時間戳記寫入 predictions_log.json。

關鍵：predictions_log.json 是「不可竄改」的歷史紀錄——預測一旦鎖定就不再改動，
開獎後由 verify.py 填入實際結果。這樣才是誠實的驗證（先預測、後開獎）。

下期期別推算：威力彩期別格式 = 民國年(3碼) + 流水號(6碼)，如 115000047。
每週一、四開獎。下期 = 最新期 + 1（跨年時流水號歸 1，由實際開獎修正）。
"""
import json
import os
from datetime import datetime, timedelta, timezone

from lottery_lib import predict_strategies, STRATEGY_NAMES, STRATEGY_DESC

TPE = timezone(timedelta(hours=8))  # 台北時區
LOG_FILE = "predictions_log.json"


def next_period_guess(last_period, last_date):
    """推算下期期別與預計開獎日。"""
    roc_year = last_period // 1000000
    serial = last_period % 1000000
    # 預計下次開獎日：威力彩週一、四開獎
    d = datetime.strptime(last_date, "%Y-%m-%d").date()
    # 找下一個週一(0)或週四(3)
    nxt = d
    for _ in range(1, 8):
        nxt = nxt + timedelta(days=1)
        if nxt.weekday() in (0, 3):
            break
    # 跨年：若下次開獎年份 > 民國年對應西元年，流水號歸 1
    next_roc = nxt.year - 1911
    if next_roc > roc_year:
        guessed = next_roc * 1000000 + 1
    else:
        guessed = last_period + 1
    return guessed, nxt.isoformat()


def main():
    with open("draws.json", encoding="utf-8") as f:
        draws = json.load(f)

    last = draws[-1]
    next_period, next_date = next_period_guess(last["period"], last["date"])

    # 載入既有 log
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, encoding="utf-8") as f:
            log = json.load(f)
    else:
        log = []

    # 若該期預測已存在，不重複鎖定（保持原始時間戳，避免事後竄改）
    existing = next((e for e in log if e["targetPeriod"] == next_period), None)
    if existing:
        print(f"第 {next_period} 期預測已鎖定於 {existing['lockedAt']}，跳過。")
        print(f"（如需重新預測，請先確認該期尚未開獎）")
        return

    # 用目前所有資料預測下期
    preds = predict_strategies(draws)

    entry = {
        "targetPeriod": next_period,
        "expectedDrawDate": next_date,
        "lockedAt": datetime.now(TPE).isoformat(timespec="seconds"),
        "basedOnPeriods": len(draws),
        "basedOnLastPeriod": last["period"],
        "predictions": {
            k: {
                "zone1": v["zone1"],
                "zone2": v["zone2"],
                "name": STRATEGY_NAMES[k],
                "desc": STRATEGY_DESC[k],
            }
            for k, v in preds.items()
        },
        "actual": None,      # 開獎後由 verify.py 填入
        "results": None,     # 開獎後由 verify.py 填入
        "verified": False,
    }
    log.append(entry)
    log.sort(key=lambda e: e["targetPeriod"])

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"✅ 已鎖定第 {next_period} 期預測（預計 {next_date} 開獎）")
    print(f"   基於前 {len(draws)} 期資料，鎖定時間 {entry['lockedAt']}")
    for k, v in preds.items():
        print(f"   [{STRATEGY_NAMES[k]}] {v['zone1']} + {v['zone2']}")


if __name__ == "__main__":
    main()
