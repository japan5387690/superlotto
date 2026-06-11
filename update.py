#!/usr/bin/env python3
"""威力彩資料更新與部署完整管線。

執行順序（每期開獎後跑）：
  1. fetch_data.py    — 抓最新開獎，更新 draws.json
  2. analyze.py       — 重算 stats.json
  3. verify.py        — 比對剛開獎的期數 vs 事前鎖定的預測，填入中獎結果
  4. backtest.py      — 重跑回測（資料多一期）
  5. predict_next.py  — 鎖定『下一期』預測（時間戳記）
  6. build_stats_js   — 打包前端資料 stats.js
  7. git commit & push — 部署到 GitHub Pages

注意順序：先 fetch（draws.json 含剛開的獎）→ 再 verify（比對上期鎖定預測）
→ 最後 predict_next（鎖定下一期）。這樣才是誠實的「先預測、後開獎、再驗證」閉環。

可用 --no-push 跳過部署（本地測試用）。
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
NO_PUSH = "--no-push" in sys.argv


def run(cmd, desc):
    print(f"\n{'='*50}\n▶ {desc}\n{'='*50}")
    r = subprocess.run(cmd, shell=True)
    if r.returncode != 0:
        print(f"⚠️ 步驟失敗（exit {r.returncode}）：{desc}")
        return False
    return True


def main():
    # 1. 抓最新開獎資料
    if not run("python3 fetch_data.py", "抓取最新開獎資料"):
        print("資料抓取失敗，中止。")
        return

    # 2. 重算統計
    run("python3 analyze.py", "重算號碼機率統計")

    # 3. 驗證上期鎖定預測（draws.json 已含最新期）
    run("python3 verify.py", "驗證已鎖定預測 vs 實際開獎")

    # 4. 重跑歷史回測
    run("python3 backtest.py", "重跑歷史回測")

    # 5. 鎖定下一期預測
    run("python3 predict_next.py", "鎖定下期預測")

    # 6. 打包前端資料
    run("python3 build_stats_js.py", "打包前端 stats.js")

    # 7. 部署
    if NO_PUSH:
        print("\n--no-push：跳過 git 部署。")
        return
    changed = subprocess.run(
        "git status --porcelain", shell=True, capture_output=True, text=True
    ).stdout.strip()
    if not changed:
        print("\n沒有變更，無需部署。")
        return
    from datetime import datetime, timezone, timedelta
    ts = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M")
    run("git add -A", "git add")
    run(f'git commit -m "資料更新 {ts}"', "git commit")
    if run("git push", "git push 部署到 GitHub Pages"):
        print("\n✅ 部署完成，GitHub Pages 約 1 分鐘後更新。")


if __name__ == "__main__":
    main()
