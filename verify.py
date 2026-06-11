#!/usr/bin/env python3
"""開獎後驗證預測。

在每期開獎『之後』執行（draws.json 已更新為含最新一期）：
掃描 predictions_log.json 中尚未驗證(verified=False)的預測，
若該期已在 draws.json 出現（代表已開獎），就填入實際號碼與中獎結果。

這完成了誠實驗證的閉環：predict_next.py 先鎖定 → 開獎 → verify.py 比對。
"""
import json
import os

from lottery_lib import evaluate, STRATEGY_NAMES

LOG_FILE = "predictions_log.json"


def main():
    if not os.path.exists(LOG_FILE):
        print("尚無 predictions_log.json，沒有需要驗證的預測。")
        return

    with open("draws.json", encoding="utf-8") as f:
        draws = json.load(f)
    draw_map = {d["period"]: d for d in draws}

    with open(LOG_FILE, encoding="utf-8") as f:
        log = json.load(f)

    verified_count = 0
    for entry in log:
        if entry.get("verified"):
            continue
        period = entry["targetPeriod"]
        actual = draw_map.get(period)
        if not actual:
            print(f"第 {period} 期尚未開獎，繼續等待。")
            continue

        # 填入實際開獎
        entry["actual"] = {"zone1": actual["zone1"], "zone2": actual["zone2"], "date": actual["date"]}
        results = {}
        for k, pred in entry["predictions"].items():
            r = evaluate({"zone1": pred["zone1"], "zone2": pred["zone2"]}, actual)
            results[k] = r
        entry["results"] = results
        entry["verified"] = True
        verified_count += 1

        print(f"\n=== 第 {period} 期驗證結果（{actual['date']}）===")
        print(f"實際開獎：{actual['zone1']} + {actual['zone2']}")
        for k, pred in entry["predictions"].items():
            r = results[k]
            mark = f"🎉 {r['prize']}" if r["prize"] else "未中獎"
            print(f"  [{STRATEGY_NAMES[k]}] {pred['zone1']}+{pred['zone2']} "
                  f"→ 第一區中 {r['m1']}、第二區{'中' if r['m2'] else '未中'} {mark}")

    if verified_count:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 完成 {verified_count} 期驗證，已更新 {LOG_FILE}")
    else:
        print("沒有新的可驗證期數。")


if __name__ == "__main__":
    main()
