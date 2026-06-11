#!/usr/bin/env python3
"""歷史回測 (walk-forward backtest)。

對每一期 i（從第 START 期開始），只用「第 0 ~ i-1 期」的資料預測第 i 期，
再跟第 i 期實際開獎比對。這是最嚴謹的驗證方式——完全沒有用到未來資訊，
模擬「如果你當時就照這個策略買，結果會怎樣」。

產出 backtest.json：每種策略的命中率、各獎項中獎次數、平均對中號碼數，
並與「隨機亂猜」基準比較。
"""
import json
from collections import Counter, defaultdict

from lottery_lib import (
    predict_strategies, evaluate, STRATEGY_NAMES, STRATEGY_DESC, PRIZE_RANK,
)

START = 100  # 前 100 期當「暖身」資料，從第 101 期開始回測

with open("draws.json", encoding="utf-8") as f:
    draws = json.load(f)

N = len(draws)
print(f"回測範圍：第 {START+1} 期 ~ 第 {N} 期，共 {N - START} 期")

# 每種策略累計統計
stats = {k: {
    "tested": 0,
    "anyPrize": 0,              # 中任一獎的次數
    "prizeCounts": Counter(),   # 各獎項次數
    "sumM1": 0,                 # 第一區對中總數
    "sumM2": 0,                 # 第二區對中總數
    "z1HitDist": Counter(),     # 第一區對中 0-6 的分布
} for k in STRATEGY_NAMES}

# 隨機基準：理論期望（不需模擬，用機率算）
# 第一區 6 選 6 命中 k 個服從超幾何分布；第二區命中機率 1/8
# 但我們也跑一個「真隨機」對照，用固定種子確保可重現
import random
rng = random.Random(42)
random_stats = {"tested": 0, "anyPrize": 0, "prizeCounts": Counter(), "sumM1": 0, "sumM2": 0, "z1HitDist": Counter()}

for i in range(START, N):
    history = draws[:i]
    actual = draws[i]
    preds = predict_strategies(history)

    for k, pred in preds.items():
        r = evaluate(pred, actual)
        s = stats[k]
        s["tested"] += 1
        s["sumM1"] += r["m1"]
        s["sumM2"] += r["m2"]
        s["z1HitDist"][r["m1"]] += 1
        if r["prize"]:
            s["anyPrize"] += 1
            s["prizeCounts"][r["prize"]] += 1

    # 隨機對照：隨機選 6+1
    rz1 = rng.sample(range(1, 39), 6)
    rz2 = rng.randint(1, 8)
    rr = evaluate({"zone1": rz1, "zone2": rz2}, actual)
    random_stats["tested"] += 1
    random_stats["sumM1"] += rr["m1"]
    random_stats["sumM2"] += rr["m2"]
    random_stats["z1HitDist"][rr["m1"]] += 1
    if rr["prize"]:
        random_stats["anyPrize"] += 1
        random_stats["prizeCounts"][rr["prize"]] += 1


def summarize(s, key=None):
    t = s["tested"]
    return {
        "strategy": key,
        "name": STRATEGY_NAMES.get(key, "隨機亂猜") if key else "隨機亂猜",
        "desc": STRATEGY_DESC.get(key, "每期隨機選號（對照基準）") if key else "每期隨機選號（對照基準）",
        "tested": t,
        "anyPrizeCount": s["anyPrize"],
        "anyPrizeRate": round(s["anyPrize"] / t * 100, 2),
        "avgZone1Hit": round(s["sumM1"] / t, 3),
        "zone2HitRate": round(s["sumM2"] / t * 100, 2),
        "prizeCounts": dict(sorted(s["prizeCounts"].items(), key=lambda x: PRIZE_RANK.get(x[0], 99))),
        "z1HitDist": {str(k): v for k, v in sorted(s["z1HitDist"].items())},
    }


results = [summarize(stats[k], k) for k in STRATEGY_NAMES]
random_summary = summarize(random_stats, None)

# 依「中獎率」排名
results_sorted = sorted(results, key=lambda x: x["anyPrizeRate"], reverse=True)

output = {
    "meta": {
        "backtestPeriods": N - START,
        "startPeriod": draws[START]["period"],
        "endPeriod": draws[-1]["period"],
        "method": "Walk-forward：每期僅用該期之前的資料預測，無未來資訊洩漏",
    },
    "strategies": results_sorted,
    "randomBaseline": random_summary,
}

with open("backtest.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 終端摘要
print(f"\n{'策略':<12}{'中獎率':>8}{'中獎次數':>9}{'第一區平均對中':>14}{'第二區命中率':>12}")
print("-" * 60)
for r in results_sorted:
    print(f"{r['name']:<12}{r['anyPrizeRate']:>7}%{r['anyPrizeCount']:>8}次{r['avgZone1Hit']:>13}{r['zone2HitRate']:>11}%")
print(f"{'隨機亂猜':<12}{random_summary['anyPrizeRate']:>7}%{random_summary['anyPrizeCount']:>8}次{random_summary['avgZone1Hit']:>13}{random_summary['zone2HitRate']:>11}%")
print("\n各策略中獎獎項分布：")
for r in results_sorted:
    if r["prizeCounts"]:
        print(f"  {r['name']}: {r['prizeCounts']}")
print("\n已儲存 backtest.json")
