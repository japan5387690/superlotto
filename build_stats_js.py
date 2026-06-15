#!/usr/bin/env python3
"""將 stats/draws/backtest/predictions 打包成前端用的 stats.js (嵌入式資料)。
這樣網站在 GitHub Pages 或 file:// 都能運作，無需額外 fetch。"""
import json
import os


def load(path, default=None):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


stats = load("stats.json")
draws = load("draws.json")
backtest = load("backtest.json", {})
backtest_deep = load("backtest_deep.json", {})
predictions = load("predictions_log.json", [])

recent = draws[-100:]  # 前端歷史紀錄只需最近 100 期

with open("stats.js", "w", encoding="utf-8") as f:
    f.write("window.STATS = " + json.dumps(stats, ensure_ascii=False) + ";\n")
    f.write("window.RECENT_DRAWS = " + json.dumps(recent, ensure_ascii=False) + ";\n")
    f.write("window.BACKTEST = " + json.dumps(backtest, ensure_ascii=False) + ";\n")
    f.write("window.BACKTEST_DEEP = " + json.dumps(backtest_deep, ensure_ascii=False) + ";\n")
    f.write("window.PREDICTIONS_LOG = " + json.dumps(predictions, ensure_ascii=False) + ";\n")

print(f"stats.js 生成完成 {round(os.path.getsize('stats.js')/1024,1)} KB")
