#!/usr/bin/env python3
"""將 stats.json + draws.json 打包成前端用的 stats.js (嵌入式資料)。
這樣網站在 GitHub Pages 或 file:// 都能運作，無需額外 fetch。"""
import json
import os

stats = json.load(open("stats.json", encoding="utf-8"))
draws = json.load(open("draws.json", encoding="utf-8"))
recent = draws[-100:]  # 前端歷史紀錄只需最近 100 期

with open("stats.js", "w", encoding="utf-8") as f:
    f.write("window.STATS = " + json.dumps(stats, ensure_ascii=False) + ";\n")
    f.write("window.RECENT_DRAWS = " + json.dumps(recent, ensure_ascii=False) + ";\n")

print(f"stats.js 生成完成 {round(os.path.getsize('stats.js')/1024,1)} KB")
