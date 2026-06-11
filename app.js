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
  function card(key, name, data, featured) {
    const z1 = data.zone1.map((n) => ball(n, "z1", true)).join("");
    const z2 = ball(data.zone2, "z2", true);
    return `<div class="pred-card${featured ? " featured" : ""}">
      ${featured ? '<span class="badge">★ 綜合推薦</span>' : ""}
      <div class="tag">策略 ${key}</div>
      <div class="name">${name}</div>
      <div class="balls">${z1}<span class="plus" style="font-size:1.1rem">+</span>${z2}</div>
      <div class="desc">${data.desc}</div>
    </div>`;
  }
  return `<section>
    <h2><span class="bar" style="background:var(--green)"></span>下期號碼預測</h2>
    <div class="hint">以下為四種不同統計策略推算的參考號碼。⚠️ 樂透為獨立隨機事件，僅供參考娛樂。</div>
    <div class="pred-grid">
      ${card("A", "頻率法", P.frequency, false)}
      ${card("B", "冷號回補法", P.overdue, false)}
      ${card("C", "近期趨勢法", P.recent, false)}
      ${card("D", "加權混合法", P.mixed, true)}
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
