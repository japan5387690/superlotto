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

// ---------- render ----------
app.innerHTML =
  sectionLatest() +
  sectionPredict() +
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
