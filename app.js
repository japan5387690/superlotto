// 威力彩機率分析 — 前端渲染
const S = window.STATS;
const RECENT = window.RECENT_DRAWS;
const $ = (id) => document.getElementById(id);

// ---------- meta ----------
$("m-first").textContent = S.meta.firstDate;
$("m-last").textContent = S.meta.lastDate;
$("m-total").textContent = S.meta.totalDraws + " 期";
$("m-period").textContent = "第 " + S.meta.lastPeriod + " 期";
$("f-date").textContent = S.meta.lastDate;

const app = $("app");

function ball(n, zone, sm) {
  const pad = String(n).padStart(2, "0");
  return `<span class="ball ${zone}${sm ? " sm" : ""}">${pad}</span>`;
}

// ---------- 最新開獎 ----------
function sectionLatest() {
  const d = S.meta.lastDraw;
  const z1 = d.zone1.map((n) => ball(n, "z1")).join("");
  return `<section>
    <h2><span class="bar"></span>最新開獎結果</h2>
    <div class="hint">第 ${d.period} 期 · ${S.meta.lastDate}</div>
    <div class="latest">
      ${z1}<span class="plus">+</span>${ball(d.zone2, "z2")}
    </div>
    <div style="text-align:center;margin-top:14px;color:var(--muted);font-size:.85rem">
      第一區（紅）1–38 選 6　·　第二區（金）1–8 選 1
    </div>
  </section>`;
}

// ---------- 機率長條圖 ----------
function sectionProb() {
  const maxZ1 = Math.max(...S.zone1.map((x) => x.ballProb));
  const z1rows = S.zone1
    .map((x) => {
      const w = (x.ballProb / maxZ1) * 100;
      return `<div class="row" data-num="${x.num}">
        <span class="lbl">${String(x.num).padStart(2, "0")}</span>
        <div class="track"><div class="fill" style="width:${w}%"></div>
          <span class="val">${x.count} 次</span></div>
        <span class="pct">${x.ballProb}%</span>
      </div>`;
    })
    .join("");

  const maxZ2 = Math.max(...S.zone2.map((x) => x.prob));
  const z2rows = S.zone2
    .map((x) => {
      const w = (x.prob / maxZ2) * 100;
      return `<div class="row z2" data-num="${x.num}">
        <span class="lbl">${String(x.num).padStart(2, "0")}</span>
        <div class="track"><div class="fill" style="width:${w}%"></div>
          <span class="val">${x.count} 次</span></div>
        <span class="pct">${x.prob}%</span>
      </div>`;
    })
    .join("");

  return `<section>
    <h2><span class="bar"></span>號碼出現機率</h2>
    <div class="hint">每個號碼在歷史開獎中出現的次數與機率。長條越長代表越常開出。</div>
    <div class="tabs">
      <div class="tab active" data-zone="z1">第一區 (1–38)</div>
      <div class="tab" data-zone="z2">第二區 (1–8)</div>
    </div>
    <div id="chart-z1">
      <div class="theory-line">▸ 理論機率：每個號碼佔開出球數約 ${(100/38).toFixed(2)}%（6/38）· 實際數值越接近代表越公正隨機</div>
      <div class="chart">${z1rows}</div>
    </div>
    <div id="chart-z2" style="display:none">
      <div class="theory-line">▸ 理論機率：每個號碼 ${S.meta.zone2Theory}%（1/8）</div>
      <div class="chart">${z2rows}</div>
    </div>
  </section>`;
}

// ---------- 冷熱號分析 ----------
function sectionAnalysis() {
  const a = S.analysis;
  const gapMap = {};
  S.zone1.forEach((x) => (gapMap[x.num] = x.lastGap));
  const cntMap = {};
  S.zone1.forEach((x) => (cntMap[x.num] = x.count));

  function numbox(n, sub) {
    return `<div class="numbox">
      <span class="n">${String(n).padStart(2, "0")}</span>
      <span class="c">${sub}</span></div>`;
  }
  const hot = a.hotZone1.map((n) => numbox(n, cntMap[n] + " 次")).join("");
  const cold = a.coldZone1.map((n) => numbox(n, cntMap[n] + " 次")).join("");
  const overdue = a.overdueZone1.map((n) => numbox(n, gapMap[n] + " 期未開")).join("");
  const recent = a.recentHotZone1.map((n) => numbox(n, "近期熱")).join("");

  return `<section>
    <h2><span class="bar" style="background:var(--red)"></span>冷熱號分析（第一區）</h2>
    <div class="hint">熱號＝歷史開出最多；冷號＝開出最少；遺漏＝最久沒開出的號碼。</div>
    <h3 style="font-size:.95rem;color:var(--red);margin:14px 0 6px">🔥 熱號 — 開出最頻繁</h3>
    <div class="grid-nums">${hot}</div>
    <h3 style="font-size:.95rem;color:var(--blue);margin:18px 0 6px">❄️ 冷號 — 開出最少</h3>
    <div class="grid-nums">${cold}</div>
    <h3 style="font-size:.95rem;color:var(--gold);margin:18px 0 6px">⏳ 遺漏最久 — 最久未開出</h3>
    <div class="grid-nums">${overdue}</div>
    <h3 style="font-size:.95rem;color:var(--purple);margin:18px 0 6px">📈 近期熱門（最近 50 期）</h3>
    <div class="grid-nums">${recent}</div>
    <div style="margin-top:18px;padding:12px 16px;background:var(--panel2);border-radius:10px;font-size:.85rem;color:var(--muted)">
      第二區　🔥 熱號 <b style="color:var(--gold)">${String(a.hotZone2).padStart(2,"0")}</b>
      　❄️ 冷號 <b style="color:var(--blue)">${String(a.coldZone2).padStart(2,"0")}</b>
      　⏳ 遺漏最久 <b style="color:var(--gold)">${String(a.overdueZone2).padStart(2,"0")}</b>
    </div>
  </section>`;
}

// ---------- 下期預測 ----------
function sectionPredict() {
  const P = S.predictions;
  function card(key, name, data, opts = {}) {
    const z1 = data.zone1.map((n) => ball(n, "z1", true)).join("");
    const z2 = ball(data.zone2, "z2", true);
    const extra = opts.extra || "";
    return `<div class="pred-card${opts.featured ? " featured" : ""}">
      ${opts.badge ? `<span class="badge">${opts.badge}</span>` : ""}
      <div class="tag">策略 ${key}</div>
      <div class="name">${name}</div>
      <div class="balls">${z1}<span class="plus" style="font-size:1.1rem">+</span>${z2}</div>
      <div class="desc">${data.desc}</div>
      ${extra}
    </div>`;
  }
  const ev = P.ev_optimized;
  const evExtra = ev
    ? `<div style="margin-top:10px;padding:8px 10px;background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.3);border-radius:8px;font-size:.74rem;color:#7ee787">
        🧮 熱門度指數 <b>${ev.popPenalty}</b>（越低越少人選）· 和值 <b>${ev.zone1.reduce((a, b) => a + b, 0)}</b>
        <br>命中率與其他策略相同，但中大獎時<b>分的人最少</b>，獨得期望獎金最高。</div>`
    : "";
  return `<section>
    <h2><span class="bar" style="background:var(--green)"></span>下期號碼預測</h2>
    <div class="hint">五種統計策略推算的參考號碼。⚠️ 樂透為獨立隨機事件，前四種「預測」僅供娛樂；
      第五種「期望值最佳化」是唯一<b>數學上站得住腳</b>的策略——它不提高命中率（不可能），而是降低分獎風險。</div>
    <div class="pred-grid">
      ${card("A", "頻率法", P.frequency)}
      ${card("B", "冷號回補法", P.overdue)}
      ${card("C", "近期趨勢法", P.recent)}
      ${card("D", "加權混合法", P.mixed)}
      ${ev ? card("E", "期望值最佳化", ev, { featured: true, badge: "★ 唯一合法優化", extra: evExtra }) : ""}
    </div>
  </section>`;
}

// ---------- 型態統計 ----------
function sectionStats() {
  const a = S.analysis;
  return `<section>
    <h2><span class="bar" style="background:var(--blue)"></span>整體型態統計</h2>
    <div class="hint">第一區 6 個號碼的整體分布特徵，可作為選號型態參考。</div>
    <div class="stat-grid">
      <div class="stat-box"><div class="v">${a.avgSum}</div><div class="k">平均和值<br>(理論約 117)</div></div>
      <div class="stat-box"><div class="v">${S.meta.zone1Theory}%</div><div class="k">第一區<br>單號理論機率</div></div>
      <div class="stat-box"><div class="v">${S.meta.zone2Theory}%</div><div class="k">第二區<br>單號理論機率</div></div>
      <div class="stat-box"><div class="v">${S.meta.totalDraws}</div><div class="k">統計總期數</div></div>
    </div>
  </section>`;
}

// ---------- 近期開獎歷史 ----------
function sectionHistory() {
  const rows = [...RECENT].reverse().slice(0, 30).map((d) => {
    const z1 = d.zone1.map((n) => ball(n, "z1", true)).join("");
    return `<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 0;border-bottom:1px solid var(--border)">
      <span style="width:92px;color:var(--muted);font-size:.8rem">${d.date}</span>
      ${z1}<span class="plus" style="font-size:1rem">+</span>${ball(d.zone2,"z2",true)}
    </div>`;
  }).join("");
  return `<section>
    <h2><span class="bar" style="background:var(--purple)"></span>近期開獎紀錄</h2>
    <div class="hint">最近 30 期開獎號碼。</div>
    <div>${rows}</div>
  </section>`;
}

// ========== 預測驗證系統 ==========

// ---------- 本期鎖定預測 (尚未開獎) ----------
function sectionLockedPrediction() {
  const log = window.PREDICTIONS_LOG || [];
  const pending = log.filter((e) => !e.verified);
  if (!pending.length) return "";
  const e = pending[pending.length - 1];
  const cards = Object.entries(e.predictions)
    .map(([k, p]) => {
      const z1 = p.zone1.map((n) => ball(n, "z1", true)).join("");
      const z2 = ball(p.zone2, "z2", true);
      return `<div class="pred-card">
        <div class="tag">${p.name}</div>
        <div class="balls" style="margin-top:8px">${z1}<span class="plus" style="font-size:1.1rem">+</span>${z2}</div>
      </div>`;
    })
    .join("");
  return `<section style="border-color:var(--green);box-shadow:0 0 0 1px rgba(63,185,80,.3)">
    <h2><span class="bar" style="background:var(--green)"></span>🔒 本期鎖定預測（待開獎驗證）</h2>
    <div class="hint">第 <b style="color:var(--green)">${e.targetPeriod}</b> 期 · 預計 ${e.expectedDrawDate} 開獎 ·
      已於 <b>${e.lockedAt.replace("T", " ").slice(0, 16)}</b> 鎖定（基於前 ${e.basedOnPeriods} 期資料）</div>
    <div style="background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.3);border-radius:8px;padding:10px 14px;margin-bottom:16px;font-size:.82rem;color:#7ee787">
      ⏱️ 此預測在開獎<b>前</b>就已鎖定時間戳記，開獎後將自動比對——這是<b>誠實驗證</b>，非事後諸葛。
    </div>
    <div class="pred-grid">${cards}</div>
  </section>`;
}

// ---------- 回測排行榜 (策略真實命中率 vs 隨機) ----------
function sectionBacktest() {
  const bt = window.BACKTEST;
  if (!bt || !bt.strategies) return "";
  const rnd = bt.randomBaseline;
  const maxRate = Math.max(...bt.strategies.map((s) => s.anyPrizeRate), rnd.anyPrizeRate);

  function barRow(s, isRandom) {
    const w = (s.anyPrizeRate / maxRate) * 100;
    const color = isRandom ? "var(--muted)" : "var(--green)";
    const prizeStr = Object.entries(s.prizeCounts || {})
      .map(([k, v]) => `${k}×${v}`)
      .join("、") || "—";
    return `<div style="margin:10px 0">
      <div style="display:flex;justify-content:space-between;font-size:.88rem;margin-bottom:3px">
        <span style="font-weight:700;color:${isRandom ? "var(--muted)" : "var(--text)"}">${isRandom ? "🎲 " : ""}${s.name}</span>
        <span style="color:${color};font-weight:700">${s.anyPrizeRate}%</span>
      </div>
      <div class="track" style="height:18px"><div class="fill" style="width:${w}%;background:linear-gradient(90deg,${isRandom ? "#555,#777" : "#2a8a3f,var(--green)"})"></div></div>
      <div style="font-size:.72rem;color:var(--muted);margin-top:3px">中獎 ${s.anyPrizeCount} 次 · 第一區平均對中 ${s.avgZone1Hit} 個 · 獎項：${prizeStr}</div>
    </div>`;
  }

  const rows = bt.strategies.map((s) => barRow(s, false)).join("") + barRow(rnd, true);

  return `<section>
    <h2><span class="bar" style="background:var(--blue)"></span>📊 策略回測：到底準不準？</h2>
    <div class="hint">${bt.meta.method}。回測 ${bt.meta.backtestPeriods} 期（第 ${bt.meta.startPeriod}～${bt.meta.endPeriod} 期），
      統計每種策略<b>實際</b>會中獎幾次。</div>
    ${rows}
    <div class="disclaimer" style="margin-top:18px">
      <b>🔬 統計真相：</b>四種策略的中獎率與「隨機亂猜」幾乎相同（差距在統計雜訊內）。
      這用 ${bt.meta.backtestPeriods} 期實證了 —— <b>樂透是獨立隨機事件，任何基於歷史頻率的策略都無法穩定打敗亂猜</b>。
      所謂「預測」僅供娛樂，請勿當真。
    </div>
  </section>`;
}

// ---------- 深度學習回測 (LSTM / Transformer vs 隨機) ----------
function sectionDeepBacktest() {
  const bt = window.BACKTEST_DEEP;
  if (!bt || !bt.results || !bt.results.length) return "";
  const m = bt.meta;
  // 以「第一區平均對中數」為主軸，因為它最能看出貼著理論線
  const theory = m.theoryAvgZone1Hit;
  const vals = bt.results.map((r) => r.avgZone1Hit).concat(theory);
  const lo = Math.min(...vals) - 0.05;
  const hi = Math.max(...vals) + 0.05;
  const span = hi - lo;
  const colorOf = (k) =>
    k === "random" ? "#8b949e" : k === "frequency" ? "#4493f8" : "var(--purple)";
  const iconOf = (k) =>
    k === "lstm" ? "🧠" : k === "transformer" ? "🤖" : k === "frequency" ? "📊" : "🎲";

  const rows = bt.results
    .map((r) => {
      const w = ((r.avgZone1Hit - lo) / span) * 100;
      return `<div style="margin:12px 0">
        <div style="display:flex;justify-content:space-between;font-size:.88rem;margin-bottom:4px">
          <span style="font-weight:700">${iconOf(r.key)} ${r.name}</span>
          <span style="font-weight:700;color:${colorOf(r.key)}">對中 ${r.avgZone1Hit} 個</span>
        </div>
        <div class="track" style="height:20px;position:relative">
          <div class="fill" style="width:${w}%;background:linear-gradient(90deg,${colorOf(r.key)}88,${colorOf(r.key)})"></div>
        </div>
        <div style="font-size:.72rem;color:var(--muted);margin-top:3px">
          中獎率 ${r.anyPrizeRate}% · 中獎 ${r.anyPrizeCount} 次</div>
      </div>`;
    })
    .join("");

  // 理論線位置
  const theoryPct = ((theory - lo) / span) * 100;

  return `<section style="border-color:var(--purple);box-shadow:0 0 0 1px rgba(188,140,255,.25)">
    <h2><span class="bar" style="background:var(--purple)"></span>🧠 深度學習實測：神經網路能預測樂透嗎？</h2>
    <div class="hint">我們真的把最強的深度學習模型丟下去：在 <b>${m.device.toUpperCase()}</b> 上跑
      <b>LSTM</b> 與 <b>Transformer</b> 神經網路，每 ${m.retrainEvery} 期用當下歷史重新訓練
      （共重訓約 ${Math.round(m.backtestPeriods / m.retrainEvery)} 次、每次 ${m.epochs} epochs），
      逐期 walk-forward 預測。回測 ${m.backtestPeriods} 期（第 ${m.startPeriod}～${m.endPeriod} 期）。</div>

    <div style="position:relative;padding:8px 0">
      ${rows}
      <div style="position:absolute;top:0;bottom:0;left:calc(${theoryPct}% );width:2px;
        background:repeating-linear-gradient(var(--gold) 0 6px,transparent 6px 12px);pointer-events:none">
        <span style="position:absolute;top:-2px;left:6px;font-size:.68rem;color:var(--gold);white-space:nowrap">
          ◀ 純隨機理論值 ${theory}</span>
      </div>
    </div>

    <div class="disclaimer" style="background:rgba(188,140,255,.08);border-color:rgba(188,140,255,.3);margin-top:20px">
      <b style="color:var(--purple)">🔬 鐵證：</b>LSTM、Transformer、頻率法、隨機亂猜——四者的成績全部
      <b>擠在同一條線上</b>，第一區平均對中數全部貼著純隨機理論值
      <b style="color:var(--gold)">${theory}</b>（±0.05 內）。
      用 GPU 重訓 ${Math.round(m.backtestPeriods / m.retrainEvery)} 次的深度神經網路，
      <b>依然打不贏亂猜</b>。
      <br><br>
      原因是數學必然：樂透每期獨立同分布，過去與未來的<b>互資訊為 0</b>。
      序列裡沒有可學的結構，再強的模型也只能去 fit 雜訊。
      這不是模型不夠好，而是<b>理論上就不存在能預測樂透的模型</b>。
    </div>
  </section>`;
}

// ---------- 已驗證歷史 ----------
function sectionVerifiedHistory() {
  const log = window.PREDICTIONS_LOG || [];
  const done = log.filter((e) => e.verified && e.results).reverse();
  if (!done.length) {
    return `<section>
      <h2><span class="bar" style="background:var(--gold)"></span>✅ 預測驗證紀錄</h2>
      <div class="hint">每期開獎後，系統會自動比對鎖定的預測與實際號碼。</div>
      <div style="text-align:center;padding:30px;color:var(--muted)">
        尚無已驗證紀錄。本期預測鎖定後，開獎即會自動比對並顯示於此。
      </div>
    </section>`;
  }
  const items = done
    .map((e) => {
      const a = e.actual;
      const actualBalls =
        a.zone1.map((n) => ball(n, "z1", true)).join("") +
        `<span class="plus" style="font-size:1rem">+</span>` +
        ball(a.zone2, "z2", true);
      const rows = Object.entries(e.predictions)
        .map(([k, p]) => {
          const r = e.results[k];
          const hit = r.prize
            ? `<span style="color:var(--green);font-weight:700">🎉 ${r.prize}</span>`
            : `<span style="color:var(--muted)">未中獎</span>`;
          return `<div style="display:flex;justify-content:space-between;font-size:.82rem;padding:4px 0">
            <span>${p.name}</span>
            <span>第一區中 <b>${r.m1}</b>、第二區${r.m2 ? "✓" : "✗"} ${hit}</span>
          </div>`;
        })
        .join("");
      return `<div style="background:var(--panel2);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:12px">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px">
          <span style="font-weight:700">第 ${e.targetPeriod} 期</span>
          <span style="color:var(--muted);font-size:.8rem">${a.date} 開獎</span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:10px">
          <span style="font-size:.8rem;color:var(--muted);width:60px">實際：</span>${actualBalls}
        </div>
        ${rows}
      </div>`;
    })
    .join("");
  return `<section>
    <h2><span class="bar" style="background:var(--gold)"></span>✅ 預測驗證紀錄</h2>
    <div class="hint">開獎後自動比對「事前鎖定」的預測與實際號碼，共 ${done.length} 期已驗證。</div>
    ${items}
  </section>`;
}

// ---------- render ----------
app.innerHTML =
  sectionLatest() +
  sectionLockedPrediction() +
  sectionPredict() +
  sectionBacktest() +
  sectionDeepBacktest() +
  sectionVerifiedHistory() +
  sectionProb() +
  sectionAnalysis() +
  sectionStats() +
  sectionHistory();

// 機率分頁切換
document.querySelectorAll(".tab[data-zone]").forEach((t) => {
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab[data-zone]").forEach((x) => x.classList.remove("active"));
    t.classList.add("active");
    const z = t.dataset.zone;
    $("chart-z1").style.display = z === "z1" ? "" : "none";
    $("chart-z2").style.display = z === "z2" ? "" : "none";
  });
});

// 長條動畫: 進場時重新觸發 width
requestAnimationFrame(() => {
  document.querySelectorAll(".fill").forEach((f) => {
    const w = f.style.width;
    f.style.width = "0";
    requestAnimationFrame(() => (f.style.width = w));
  });
});
