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

    draw_map = {d["period"]: d for d in draws}
    now_ts = datetime.now(TPE).isoformat(timespec="seconds")

    def build_predictions(preds_dict):
        """把策略結果包成 predictions 區塊（含名稱、說明）。"""
        return {
            k: {
                "zone1": v["zone1"],
                "zone2": v["zone2"],
                "name": STRATEGY_NAMES[k],
                "desc": STRATEGY_DESC[k],
            }
            for k, v in preds_dict.items()
        }

    # 用目前所有資料預測（基準＝截至最後一期，與原鎖定同一份資料）
    preds = predict_strategies(draws)

    # ============================================================
    # 補鎖規則（誠實性核心）
    # ------------------------------------------------------------
    # 對「尚未開獎」的待驗證期數，若系統新增了策略（例如 EV 期望值最佳化），
    # 自動補上缺漏的策略，蓋上『獨立的補鎖時間戳』並標記 _backfilledAt。
    # 嚴格條件：
    #   1) entry 必須 verified=False（未驗證）
    #   2) 該期『尚未』出現在 draws.json（亦即尚未開獎）
    # 只要該期已開獎，一律凍結、絕不竄改——維持「先鎖定、後開獎」的誠實閉環。
    # ============================================================
    backfilled_total = 0
    for entry in log:
        if entry.get("verified"):
            continue  # 已驗證（已開獎）→ 凍結
        if entry["targetPeriod"] in draw_map:
            continue  # 已開獎、待 verify → 視為凍結，交給 verify.py，不補鎖
        existing_preds = entry.get("predictions", {})
        missing = [k for k in preds if k not in existing_preds]
        if not missing:
            continue
        new_block = build_predictions({k: preds[k] for k in missing})
        for k, v in new_block.items():
            v["_backfilledAt"] = now_ts                       # 後補時間戳（與原鎖定區隔）
            v["_backfilledBasedOnLastPeriod"] = last["period"]
        existing_preds.update(new_block)
        entry["predictions"] = existing_preds
        entry.setdefault("backfillLog", []).append({
            "at": now_ts,
            "addedStrategies": missing,
            "basedOnLastPeriod": last["period"],
        })
        backfilled_total += len(missing)
        names = "、".join(STRATEGY_NAMES[k] for k in missing)
        print(f"🔁 第 {entry['targetPeriod']} 期補鎖 {len(missing)} 個新策略：{names}"
              f"（該期尚未開獎，誠實補鎖，蓋獨立時間戳 {now_ts}）")
        for k in missing:
            print(f"   [{STRATEGY_NAMES[k]}] {preds[k]['zone1']} + {preds[k]['zone2']}")

    # ============================================================
    # 新鎖規則：若『下一期』尚無任何鎖定紀錄，建立完整 entry
    # ============================================================
    existing = next((e for e in log if e["targetPeriod"] == next_period), None)
    if existing:
        if backfilled_total:
            log.sort(key=lambda e: e["targetPeriod"])
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 已補鎖 {backfilled_total} 筆策略並更新 {LOG_FILE}")
        else:
            print(f"第 {next_period} 期預測已鎖定於 {existing['lockedAt']}，"
                  f"且策略完整、無缺漏，跳過。")
        return

    entry = {
        "targetPeriod": next_period,
        "expectedDrawDate": next_date,
        "lockedAt": now_ts,
        "basedOnPeriods": len(draws),
        "basedOnLastPeriod": last["period"],
        "predictions": build_predictions(preds),
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
