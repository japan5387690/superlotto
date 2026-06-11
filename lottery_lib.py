#!/usr/bin/env python3
"""威力彩共用函式庫：預測策略、中獎判定、命中評估。

被 analyze.py / predict_next.py / verify.py / backtest.py 共用，
確保「鎖定預測」與「歷史回測」用完全相同的策略邏輯，避免前後不一致。

威力彩規則：第一區 1-38 選 6，第二區 1-8 選 1。
"""
from collections import Counter

ZONE1_MAX = 38
ZONE2_MAX = 8
RECENT_WINDOW = 50  # 近期趨勢視窗

STRATEGY_NAMES = {
    "frequency": "頻率法",
    "overdue": "冷號回補法",
    "recent": "近期趨勢法",
    "mixed": "加權混合法",
}
STRATEGY_DESC = {
    "frequency": "歷史出現頻率最高的號碼",
    "overdue": "遺漏期數最久、理論上「該開」的號碼",
    "recent": f"最近 {RECENT_WINDOW} 期最常開出的號碼",
    "mixed": "歷史頻率(60%) + 近期趨勢(40%) 加權混合",
}


def _zone1_counter(history):
    c = Counter()
    for d in history:
        for n in d["zone1"]:
            c[n] += 1
    return c


def _zone2_counter(history):
    return Counter(d["zone2"] for d in history)


def _last_gap(history, num, zone):
    """從最新一期往回，num 最近一次出現距今幾期（0=最新一期）。沒出現過回傳 len。"""
    for i, d in enumerate(reversed(history)):
        vals = d["zone1"] if zone == "zone1" else [d["zone2"]]
        if num in vals:
            return i
    return len(history)


def predict_strategies(history):
    """根據 history（該期之前的所有開獎）計算 4 種策略的預測號碼。

    回傳 dict：{strategy_key: {"zone1": [6 個], "zone2": int}}
    history 必須非空。
    """
    n = len(history)
    z1c = _zone1_counter(history)
    z2c = _zone2_counter(history)

    # 策略 A：頻率法 — 歷史最常開出
    freq_z1 = sorted([num for num, _ in z1c.most_common(6)])
    freq_z2 = z2c.most_common(1)[0][0] if z2c else 1

    # 策略 B：冷號回補 — 遺漏最久
    gaps1 = {num: _last_gap(history, num, "zone1") for num in range(1, ZONE1_MAX + 1)}
    overdue_z1 = sorted(sorted(gaps1, key=gaps1.get, reverse=True)[:6])
    gaps2 = {num: _last_gap(history, num, "zone2") for num in range(1, ZONE2_MAX + 1)}
    overdue_z2 = max(gaps2, key=gaps2.get)

    # 策略 C：近期趨勢 — 最近 N 期最熱
    recent = history[-RECENT_WINDOW:]
    r1c = _zone1_counter(recent)
    r2c = _zone2_counter(recent)
    # 近期可能不足 6 種號碼，補足用整體頻率
    rec_z1 = [num for num, _ in r1c.most_common(6)]
    if len(rec_z1) < 6:
        for num, _ in z1c.most_common():
            if num not in rec_z1:
                rec_z1.append(num)
            if len(rec_z1) == 6:
                break
    recent_z1 = sorted(rec_z1[:6])
    recent_z2 = r2c.most_common(1)[0][0] if r2c else freq_z2

    # 策略 D：加權混合 — 頻率 60% + 近期 40%
    score1 = {}
    rn = max(len(recent), 1)
    for num in range(1, ZONE1_MAX + 1):
        overall = z1c.get(num, 0) / (n * 6)
        rec = r1c.get(num, 0) / (rn * 6)
        score1[num] = overall * 0.6 + rec * 0.4
    mix_z1 = sorted(sorted(score1, key=score1.get, reverse=True)[:6])
    score2 = {}
    for num in range(1, ZONE2_MAX + 1):
        overall = z2c.get(num, 0) / n
        rec = r2c.get(num, 0) / rn
        score2[num] = overall * 0.6 + rec * 0.4
    mix_z2 = max(score2, key=score2.get)

    return {
        "frequency": {"zone1": freq_z1, "zone2": freq_z2},
        "overdue": {"zone1": overdue_z1, "zone2": overdue_z2},
        "recent": {"zone1": recent_z1, "zone2": recent_z2},
        "mixed": {"zone1": mix_z1, "zone2": mix_z2},
    }


def count_matches(pred, actual):
    """計算預測對中幾個。回傳 (第一區對中數 0-6, 第二區是否對中 0/1)。"""
    m1 = len(set(pred["zone1"]) & set(actual["zone1"]))
    m2 = 1 if pred["zone2"] == actual["zone2"] else 0
    return m1, m2


def prize_tier(m1, m2):
    """依對中數判定威力彩獎項。回傳中文獎項名稱，未中獎回傳 None。"""
    table = {
        (6, 1): "頭獎", (6, 0): "貳獎",
        (5, 1): "參獎", (5, 0): "肆獎",
        (4, 1): "伍獎", (4, 0): "陸獎",
        (3, 1): "柒獎",
        (2, 1): "捌獎",
        (3, 0): "玖獎", (1, 1): "玖獎", (0, 1): "玖獎",
    }
    return table.get((m1, m2))


def evaluate(pred, actual):
    """完整評估單筆預測 vs 實際開獎。"""
    m1, m2 = count_matches(pred, actual)
    return {
        "m1": m1,
        "m2": m2,
        "prize": prize_tier(m1, m2),
        "hit": prize_tier(m1, m2) is not None,
    }


# 獎項排序（用於統計，數字越小越大獎）
PRIZE_RANK = {
    "頭獎": 1, "貳獎": 2, "參獎": 3, "肆獎": 4, "伍獎": 5,
    "陸獎": 6, "柒獎": 7, "捌獎": 8, "玖獎": 9,
}
