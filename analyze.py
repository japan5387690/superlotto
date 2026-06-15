#!/usr/bin/env python3
"""威力彩開獎統計分析 + 機率計算。

產出 stats.json 供前端網站使用，內容包含:
  - 第一區 (1-38) 每個號碼的出現次數、機率、最近開出期數間隔
  - 第二區 (1-8) 每個號碼的出現次數、機率、最近開出期數間隔
  - 冷熱號分析
  - 基於頻率的下期推薦號碼
  - 整體統計 (奇偶比、大小比、和值分布等)
"""
import json
from collections import Counter

with open("draws.json", encoding="utf-8") as f:
    draws = json.load(f)

N = len(draws)  # 總期數
ZONE1_MAX = 38
ZONE2_MAX = 8

# ---------- 第一區統計 ----------
z1_counter = Counter()
for d in draws:
    for n in d["zone1"]:
        z1_counter[n] += 1

# 理論機率: 每期開 6 個球, 每個號碼理論機率 = 6/38 = 15.79%
z1_theory = 6 / ZONE1_MAX

# 計算每個號碼最近一次開出後經過幾期 (遺漏值/間隔)
def last_gap(num, zone_key):
    """從最新一期往回找，該號碼最近一次出現距今幾期 (0=最新一期就有)。"""
    for i, d in enumerate(reversed(draws)):
        vals = d["zone1"] if zone_key == "zone1" else [d["zone2"]]
        if num in vals:
            return i
    return N  # 從未出現

zone1 = []
for n in range(1, ZONE1_MAX + 1):
    cnt = z1_counter.get(n, 0)
    gap = last_gap(n, "zone1")
    zone1.append({
        "num": n,
        "count": cnt,
        "prob": round(cnt / N * 100, 2),          # 出現在某一期的機率 (%)
        "ballProb": round(cnt / (N * 6) * 100, 2),  # 佔所有開出球的比例 (%)
        "lastGap": gap,                             # 最近遺漏期數
    })

# ---------- 第二區統計 ----------
z2_counter = Counter(d["zone2"] for d in draws)
z2_theory = 1 / ZONE2_MAX

zone2 = []
for n in range(1, ZONE2_MAX + 1):
    cnt = z2_counter.get(n, 0)
    gap = last_gap(n, "zone2")
    zone2.append({
        "num": n,
        "count": cnt,
        "prob": round(cnt / N * 100, 2),
        "lastGap": gap,
    })

# ---------- 冷熱號 ----------
z1_sorted = sorted(zone1, key=lambda x: x["count"], reverse=True)
z2_sorted = sorted(zone2, key=lambda x: x["count"], reverse=True)

hot_zone1 = [x["num"] for x in z1_sorted[:6]]   # 最常開出 6 個
cold_zone1 = [x["num"] for x in z1_sorted[-6:]]  # 最少開出 6 個
hot_zone2 = z2_sorted[0]["num"]
cold_zone2 = z2_sorted[-1]["num"]

# 遺漏最久 (最久沒開出)
z1_by_gap = sorted(zone1, key=lambda x: x["lastGap"], reverse=True)
z2_by_gap = sorted(zone2, key=lambda x: x["lastGap"], reverse=True)
overdue_zone1 = [x["num"] for x in z1_by_gap[:6]]
overdue_zone2 = z2_by_gap[0]["num"]

# ---------- 近期趨勢 (最近 50 期) ----------
recent = draws[-50:]
r1_counter = Counter()
for d in recent:
    for n in d["zone1"]:
        r1_counter[n] += 1
r2_counter = Counter(d["zone2"] for d in recent)
recent_hot_z1 = [n for n, _ in r1_counter.most_common(6)]
recent_hot_z2 = r2_counter.most_common(1)[0][0] if r2_counter else None

# ---------- 整體型態統計 ----------
odd_even = Counter()    # 第一區奇數個數分布
big_small = Counter()   # 第一區大數(>=20)個數分布
sum_dist = []           # 第一區和值
for d in draws:
    z = d["zone1"]
    odd = sum(1 for x in z if x % 2 == 1)
    big = sum(1 for x in z if x >= 20)
    odd_even[odd] += 1
    big_small[big] += 1
    sum_dist.append(sum(z))

avg_sum = round(sum(sum_dist) / len(sum_dist), 1)

# ---------- 下期推薦號碼 (多策略) ----------
# 策略 A: 純頻率法 (選歷史最常開出)
strategy_freq = {
    "zone1": sorted(hot_zone1),
    "zone2": hot_zone2,
    "desc": "歷史出現頻率最高的號碼",
}
# 策略 B: 冷號回補法 (選遺漏最久, 賭它該開了)
strategy_overdue = {
    "zone1": sorted(overdue_zone1),
    "zone2": overdue_zone2,
    "desc": "遺漏期數最久、理論上「該開」的號碼",
}
# 策略 C: 近期熱號法 (跟最近 50 期趨勢)
strategy_recent = {
    "zone1": sorted(recent_hot_z1),
    "zone2": recent_hot_z2,
    "desc": "最近 50 期最常開出的號碼",
}
# 策略 D: 加權混合 (頻率 60% + 近期 40%, 第二區同理)
score1 = {}
for n in range(1, ZONE1_MAX + 1):
    overall = z1_counter.get(n, 0) / (N * 6)
    rec = r1_counter.get(n, 0) / (len(recent) * 6)
    score1[n] = overall * 0.6 + rec * 0.4
mix_z1 = sorted(sorted(score1, key=score1.get, reverse=True)[:6])
score2 = {}
for n in range(1, ZONE2_MAX + 1):
    overall = z2_counter.get(n, 0) / N
    rec = r2_counter.get(n, 0) / len(recent)
    score2[n] = overall * 0.6 + rec * 0.4
mix_z2 = max(score2, key=score2.get)
strategy_mix = {
    "zone1": mix_z1,
    "zone2": mix_z2,
    "desc": "歷史頻率(60%) + 近期趨勢(40%) 加權混合",
}
# 策略 E: 期望值最佳化 (避開大眾熱門組合, 降低分獎人數, 提高獨得期望獎金)
from lottery_lib import ev_optimized_pick, popularity_penalty
_ev = ev_optimized_pick(draws)
strategy_ev = {
    "zone1": _ev["zone1"],
    "zone2": _ev["zone2"],
    "desc": "避開大眾愛選的生日數/連號/低和值，中獎時分的人最少",
    "popPenalty": round(popularity_penalty(_ev["zone1"]), 2),
}

result = {
    "meta": {
        "totalDraws": N,
        "firstPeriod": draws[0]["period"],
        "firstDate": draws[0]["date"],
        "lastPeriod": draws[-1]["period"],
        "lastDate": draws[-1]["date"],
        "zone1Theory": round(z1_theory * 100, 2),
        "zone2Theory": round(z2_theory * 100, 2),
        "lastDraw": {
            "period": draws[-1]["period"],
            "zone1": draws[-1]["zone1"],
            "zone2": draws[-1]["zone2"],
        },
    },
    "zone1": zone1,
    "zone2": zone2,
    "analysis": {
        "hotZone1": sorted(hot_zone1),
        "coldZone1": sorted(cold_zone1),
        "hotZone2": hot_zone2,
        "coldZone2": cold_zone2,
        "overdueZone1": sorted(overdue_zone1),
        "overdueZone2": overdue_zone2,
        "recentHotZone1": sorted(recent_hot_z1),
        "recentHotZone2": recent_hot_z2,
        "avgSum": avg_sum,
        "oddEvenDist": dict(sorted(odd_even.items())),
        "bigSmallDist": dict(sorted(big_small.items())),
    },
    "predictions": {
        "frequency": strategy_freq,
        "overdue": strategy_overdue,
        "recent": strategy_recent,
        "mixed": strategy_mix,
        "ev_optimized": strategy_ev,
    },
}

with open("stats.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

# ---------- 終端摘要 ----------
print(f"=== 威力彩統計分析 ({N} 期) ===")
print(f"期間: {draws[0]['date']} ~ {draws[-1]['date']}")
print(f"\n第一區理論機率: {z1_theory*100:.2f}% / 號")
print("熱號 (最常開出):", sorted(hot_zone1))
print("冷號 (最少開出):", sorted(cold_zone1))
print("遺漏最久:", sorted(overdue_zone1))
print(f"\n第二區理論機率: {z2_theory*100:.2f}% / 號")
print("熱號:", hot_zone2, " 冷號:", cold_zone2, " 遺漏最久:", overdue_zone2)
print(f"\n第一區平均和值: {avg_sum}")
print("\n=== 下期推薦 ===")
for k, v in result["predictions"].items():
    print(f"[{k}] 第一區 {v['zone1']} + 第二區 {v['zone2']}  ({v['desc']})")
print("\n已儲存 stats.json")
