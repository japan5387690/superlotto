#!/usr/bin/env python3
"""撈取台灣彩券威力彩 (SuperLotto 638) 全部開獎資料 (2008-01 至今)。

威力彩規則:
  第一區: 1-38 選 6 個
  第二區: 1-8 選 1 個
  每週一、週四開獎 (2008-01-28 首期)

資料來源: 台灣彩券官方 API
  https://api.taiwanlottery.com/TLCAPIWeB/Lottery/SuperLotto638Result
  必要 header: Origin + Referer (否則回傳空)
"""
import json
import time
import urllib.request
import urllib.parse
from datetime import date

API = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/SuperLotto638Result"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Origin": "https://www.taiwanlottery.com",
    "Referer": "https://www.taiwanlottery.com/",
    "Accept": "application/json",
}


def fetch_month(month_str):
    """抓單一月份的開獎資料。month_str 格式 'YYYY-MM'。"""
    qs = urllib.parse.urlencode({
        "period": "",
        "month": month_str,
        "pageNum": 1,
        "pageSize": 50,
    })
    url = f"{API}?{qs}"
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("rtCode") != 0:
                print(f"  [warn] {month_str} rtCode={data.get('rtCode')}")
                return []
            return data["content"]["superLotto638Res"]
        except Exception as e:
            print(f"  [retry {attempt+1}] {month_str}: {e}")
            time.sleep(2)
    print(f"  [fail] {month_str} 放棄")
    return []


def month_iter(start_year, start_month, end_year, end_month):
    y, m = start_year, start_month
    while (y, m) <= (end_year, end_month):
        yield f"{y:04d}-{m:02d}"
        m += 1
        if m > 12:
            m = 1
            y += 1


def main():
    today = date.today()
    all_draws = {}  # period -> record (去重)

    months = list(month_iter(2008, 1, today.year, today.month))
    print(f"準備抓取 {len(months)} 個月份: {months[0]} ~ {months[-1]}")

    for i, ms in enumerate(months):
        rows = fetch_month(ms)
        for r in rows:
            period = r["period"]
            nums = r["drawNumberSize"]  # 已按大小排序: 前6第一區, 第7第二區
            all_draws[period] = {
                "period": period,
                "date": r["lotteryDate"][:10],
                "zone1": nums[:6],        # 第一區 6 個 (1-38)
                "zone2": nums[6],          # 第二區 1 個 (1-8)
                "appear": r["drawNumberAppear"],  # 開出順序
                "sellAmount": r.get("sellAmount"),
                "totalAmount": r.get("totalAmount"),
            }
        if rows:
            print(f"[{i+1}/{len(months)}] {ms}: {len(rows)} 期 (累計 {len(all_draws)})")
        time.sleep(0.3)  # 禮貌延遲

    # 依期數排序
    draws = sorted(all_draws.values(), key=lambda x: x["period"])
    print(f"\n總計 {len(draws)} 期")
    print(f"最早: {draws[0]['period']} ({draws[0]['date']})")
    print(f"最新: {draws[-1]['period']} ({draws[-1]['date']})")

    with open("draws.json", "w", encoding="utf-8") as f:
        json.dump(draws, f, ensure_ascii=False, indent=2)
    print("已儲存 draws.json")


if __name__ == "__main__":
    main()
