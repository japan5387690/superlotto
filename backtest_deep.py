#!/usr/bin/env python3
"""深度學習模型的 walk-forward 回測。

對 LSTM 與 Transformer 做嚴謹的「無未來資訊」回測：
  - 從 backtest 起點開始，每 RETRAIN_EVERY 期用「當下所有歷史」重新訓練模型
    （模擬真實情境：你不會每一期都重訓，而是定期更新模型）
  - 用訓練好的模型逐期預測，預測第 i 期時只用第 i 期之前的開獎做輸入窗格
  - 完全沒有未來資訊洩漏

★ 為了「蘋果對蘋果」的公平對比，在『完全相同的期數窗格』上同時跑：
    頻率法（傳統統計策略）與 隨機亂猜（理論基準）。
  這樣三者站在同一條起跑線，深度學習有沒有比較強一目了然。

產出 backtest_deep.json 供前端繪圖。

用法：
    python3 backtest_deep.py [--periods N] [--retrain K] [--epochs E]
"""
import argparse
import json
import time
from collections import Counter

import numpy as np
import torch

from lottery_lib import predict_strategies, evaluate, PRIZE_RANK
from deep_models import (
    MODEL_FACTORY, DEEP_NAMES, DEEP_DESC, train_model, predict,
    SEQ_LEN, DEVICE,
)

ap = argparse.ArgumentParser()
ap.add_argument("--periods", type=int, default=700, help="回測最近 N 期")
ap.add_argument("--retrain", type=int, default=35, help="每 K 期重訓一次")
ap.add_argument("--epochs", type=int, default=30, help="每次訓練 epoch 數")
args = ap.parse_args()

torch.manual_seed(42)
np.random.seed(42)

with open("draws.json", encoding="utf-8") as f:
    draws = json.load(f)

N = len(draws)
BACKTEST_PERIODS = min(args.periods, N - 200)  # 至少保留 200 期暖身
START = N - BACKTEST_PERIODS
print(f"裝置：{DEVICE} · 總資料 {N} 期")
print(f"深度回測範圍：第 {draws[START]['period']} ~ {draws[-1]['period']} 期"
      f"（{BACKTEST_PERIODS} 期）")
print(f"每 {args.retrain} 期重訓、每次 {args.epochs} epochs\n")


def blank():
    return {"tested": 0, "anyPrize": 0, "prizeCounts": Counter(),
            "sumM1": 0, "sumM2": 0, "z1HitDist": Counter()}


def record(s, r):
    s["tested"] += 1
    s["sumM1"] += r["m1"]
    s["sumM2"] += r["m2"]
    s["z1HitDist"][r["m1"]] += 1
    if r["prize"]:
        s["anyPrize"] += 1
        s["prizeCounts"][r["prize"]] += 1


# 各方法統計（深度模型 + 頻率 + 隨機，跑在同一窗格）
stats = {k: blank() for k in MODEL_FACTORY}
stats["frequency"] = blank()
stats["random"] = blank()

rng = np.random.RandomState(42)

# ---- 深度模型：定期重訓 walk-forward ----
for mkey in MODEL_FACTORY:
    t0 = time.time()
    print(f"▶ 回測 {DEEP_NAMES[mkey]} …")
    model = None
    for i in range(START, N):
        # 每 RETRAIN_EVERY 期（或第一次）重訓，只用 draws[:i]
        if model is None or (i - START) % args.retrain == 0:
            model = train_model(MODEL_FACTORY[mkey](), draws[:i],
                                epochs=args.epochs)
        pred = predict(model, draws[:i])      # 只用過去資料當輸入
        record(stats[mkey], evaluate(pred, draws[i]))
    print(f"  完成，用時 {time.time()-t0:.1f}s\n")

# ---- 頻率法 + 隨機：同一窗格 ----
print("▶ 同窗格對照：頻率法 + 隨機亂猜 …")
for i in range(START, N):
    history = draws[:i]
    actual = draws[i]
    freq_pred = predict_strategies(history)["frequency"]
    record(stats["frequency"], evaluate(freq_pred, actual))
    rz1 = sorted(rng.choice(range(1, 39), 6, replace=False).tolist())
    rz2 = int(rng.randint(1, 9))
    record(stats["random"], evaluate({"zone1": rz1, "zone2": rz2}, actual))
print("  完成\n")

NAME_MAP = dict(DEEP_NAMES)
NAME_MAP["frequency"] = "頻率法（傳統統計）"
NAME_MAP["random"] = "隨機亂猜（理論基準）"
DESC_MAP = dict(DEEP_DESC)
DESC_MAP["frequency"] = "歷史出現頻率最高的號碼（對照組）"
DESC_MAP["random"] = "每期完全隨機選號（理論下限基準）"


def summarize(key, s):
    t = max(s["tested"], 1)
    return {
        "key": key,
        "name": NAME_MAP[key],
        "desc": DESC_MAP[key],
        "tested": s["tested"],
        "anyPrizeCount": s["anyPrize"],
        "anyPrizeRate": round(s["anyPrize"] / t * 100, 2),
        "avgZone1Hit": round(s["sumM1"] / t, 3),
        "zone2HitRate": round(s["sumM2"] / t * 100, 2),
        "prizeCounts": dict(sorted(s["prizeCounts"].items(),
                                   key=lambda x: PRIZE_RANK.get(x[0], 99))),
        "z1HitDist": {str(k): v for k, v in sorted(s["z1HitDist"].items())},
    }


order = ["lstm", "transformer", "frequency", "random"]
results = [summarize(k, stats[k]) for k in order]

# 第一區理論期望對中數 = 6 * 6/38 ≈ 0.947；中任一獎理論機率 ≈ 15.5%
theory_avg_z1 = round(6 * 6 / 38, 3)

output = {
    "meta": {
        "backtestPeriods": BACKTEST_PERIODS,
        "startPeriod": draws[START]["period"],
        "endPeriod": draws[-1]["period"],
        "seqLen": SEQ_LEN,
        "retrainEvery": args.retrain,
        "epochs": args.epochs,
        "device": str(DEVICE),
        "theoryAvgZone1Hit": theory_avg_z1,
        "method": (f"Walk-forward：每 {args.retrain} 期用當下歷史重訓神經網路，"
                   f"逐期預測無未來資訊洩漏。頻率法與隨機亂猜跑在完全相同窗格。"),
    },
    "results": results,
}

with open("backtest_deep.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# 終端摘要
print(f"{'方法':<22}{'中獎率':>9}{'中獎次數':>9}{'第一區平均對中':>15}")
print("-" * 60)
for r in results:
    print(f"{r['name']:<22}{r['anyPrizeRate']:>8}%{r['anyPrizeCount']:>8}次"
          f"{r['avgZone1Hit']:>14}")
print(f"\n理論值：第一區平均對中 {theory_avg_z1}（純隨機期望）")
print("已儲存 backtest_deep.json")
