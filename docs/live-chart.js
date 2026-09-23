/* Graphique live partagé (tableau de bord et simulation de compte), dessiné avec TradingView
 * Lightweight Charts (copie locale dans docs/vendor, licence Apache 2.0).
 *
 * Données : docs/live/<actif>.json, publié par le bot à chaque passage (≈ 5 min) : 24 h de bougies
 * 5 min, niveaux des signaux ouverts et trades clôturés de la période. Les vues 15 min et 1 h sont
 * reconstruites ici à partir des bougies 5 min.
 *
 * Utilisation :
 *   const live = LiveChart.mount(conteneur, { assets: [["bitcoin", "Bitcoin (BTC/USD)", essai?], …] });
 *   live.setAssets(liste); live.select("bitcoin"); live.refresh();
 *   LiveChart.snapshot("bitcoin") → promesse des dernières données (mise en cache 1 min)
 *   Mode halal : LiveChart.mount(conteneur, { base: "halal/", tf: "60", assets: … }) lit docs/halal/live/,
 *   avec ses propres choix mémorisés (actif, unité de temps), séparés de ceux du bot principal.
 *
 * Le choix d'actif et d'unité de temps est mémorisé dans le navigateur et partagé entre les pages.
 * Si la bibliothèque ne se charge pas, un graphique SVG simple prend le relais.
 */
(function () {
  "use strict";
  const STORE_KEY = "tb-live-asset", TF_KEY = "tb-live-tf";
  const DEFAULT_ASSETS = [["nasdaq", "Nasdaq 100 (NQ)"], ["sp500", "S&P 500 (ES)"], ["bitcoin", "Bitcoin (BTC/USD)"],
                          ["ethereum", "Ethereum (ETH/USD)", true], ["gold", "Or (XAU/USD)"],
                          ["oil", "Pétrole WTI (CL)", true], ["euro", "Euro / dollar (6E)", true]];
  const TF = { "5": 300, "15": 900, "60": 3600 };
  const TF_LABEL = { "5": "5 min", "15": "15 min", "60": "1 h" };
  const NB = " ", MINUS = "−";

  const STYLE = `
  .lc-head { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px 16px; margin-bottom: 14px; }
  .lc-title { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .lc-title h3 { margin: 0; font-size: 18px; }
  .lc-chips { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; margin-bottom: 14px; padding-bottom: 2px; }
  .lc-chips::-webkit-scrollbar { display: none; }
  .lc-chip { flex: none; display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 10px; border: 1px solid var(--line);
             background: var(--card); color: var(--text); font-size: 13px; font-weight: 600; cursor: pointer; }
  .lc-chip:hover { background: var(--soft); filter: none; }
  .lc-chip .ch { font-weight: 500; font-size: 12px; }
  .lc-chip .es { font-weight: 500; font-size: 11px; padding: 1px 6px; border-radius: 999px; background: var(--brand-soft); color: var(--brand-text); }
  .lc-chip[aria-pressed="true"] { background: var(--text); color: var(--card); border-color: var(--text); }
  .lc-chip[aria-pressed="true"] .ch, .lc-chip[aria-pressed="true"] .es { color: var(--card); background: transparent; }
  .lc-sig { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 14px; padding: 10px 12px; border-radius: 12px; background: var(--brand-soft);
            font-size: 13px; margin-bottom: 12px; }
  .lc-sig b { font-weight: 600; } .lc-sig .mono { font-size: 12px; color: var(--muted); }
  .lc-box { position: relative; height: 440px; }
  .lc-box.lc-svgmode { height: auto; }
  .lc-ov { position: absolute; left: 8px; top: 6px; z-index: 3; pointer-events: none; display: grid; gap: 1px; }
  .lc-ov .n { font-weight: 600; font-size: 14px; } .lc-ov .n span { font-weight: 500; font-size: 12px; color: var(--muted); margin-left: 6px; }
  .lc-ov .o { font: 11px "Geist Mono", ui-monospace, monospace; color: var(--muted); display: flex; gap: 10px; flex-wrap: wrap; }
  .lc-ov .a { font-size: 11px; color: var(--faint); }
  .lc-zone { position: absolute; z-index: 2; pointer-events: none; background: color-mix(in srgb, var(--up) 12%, transparent);
             border-top: 1px solid color-mix(in srgb, var(--up) 35%, transparent); border-bottom: 1px solid color-mix(in srgb, var(--up) 35%, transparent); }
  .lc-zone.short { background: color-mix(in srgb, var(--dn) 12%, transparent); border-color: color-mix(in srgb, var(--dn) 35%, transparent); }
  .lc-foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 16px; margin-top: 12px; font-size: 12px; color: var(--muted); }
  .lc-leg { display: flex; flex-wrap: wrap; gap: 4px 16px; align-items: center; }
  .lc-leg span { display: inline-flex; align-items: center; gap: 6px; }
  .lc-leg .tri { width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-bottom: 8px solid var(--up); }
  .lc-leg .ring { width: 9px; height: 9px; border-radius: 50%; border: 2px solid var(--up); }
  .lc-leg .zn { width: 14px; height: 8px; border-radius: 2px; background: color-mix(in srgb, var(--up) 18%, transparent); }
  .lc-leg .ln { width: 14px; height: 0; border-top: 2px dashed var(--up); } .lc-leg .ln.sl { border-top-color: var(--dn); }
  .lc-hint { color: var(--faint); }
  .lc-how { margin-top: 6px; font-size: 12px; color: var(--muted); }
  .lc-empty { display: grid; place-items: center; height: 100%; color: var(--muted); font-size: 13px; text-align: center; padding: 20px; }
  .lc-svg svg { display: block; width: 100%; height: auto; font: 11px "Geist Mono", ui-monospace, monospace; }
  .lc-svg svg text { fill: var(--muted); }
  @media (max-width: 760px) { .lc-box { height: 320px; } .lc-hint { display: none; } .lc-ov .o { display: none; } }`;

  function injectStyle() {
    if (document.getElementById("lc-style")) return;
    const st = document.createElement("style"); st.id = "lc-style"; st.textContent = STYLE; document.head.appendChild(st);
  }
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* stockage indisponible */ } },
  };
  const css = (n, d) => (getComputedStyle(document.documentElement).getPropertyValue(n).trim() || d);
  const fmt = (v, digits) => {
    if (v === null || v === undefined || !Number.isFinite(Number(v))) return "n/a";
    const s = Math.abs(v).toLocaleString("fr-FR", { minimumFractionDigits: digits, maximumFractionDigits: digits }).replace(/[\s ]/g, NB);
    return (v < 0 ? MINUS : "") + s;
  };
  const sgnPct = (v) => (v > 0 ? "+" : v < 0 ? MINUS : "") + Math.abs(v).toFixed(2).replace(".", ",") + NB + "%";
  const hhmm = (ts) => new Date(ts * 1000).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  const shortLabel = (l) => String(l || "").replace(/ \(.*\)$/, "");
  function ago(iso) {
    const min = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
    if (min < 1) return "à l'instant";
    if (min < 60) return `il y a ${min} min`;
    return `il y a ${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")}`;
  }

  // ------------------------------------------------------------------ données
  const cache = new Map();   // actif → { t, p }
  function snapshot(key, maxAgeMs = 55000, base = "") {
    const c = cache.get(base + key);
    if (c && Date.now() - c.t < maxAgeMs) return c.p;
    const p = (async () => {
      for (const u of [`${base}live/${key}.json`, `../data/${base}live/${key}.json`, `/data/${base}live/${key}.json`]) {
        try { const r = await fetch(u + "?t=" + Date.now(), { cache: "no-store" }); if (r.ok) return await r.json(); } catch (e) { /* suivant */ }
      }
      return null;
    })();
    cache.set(base + key, { t: Date.now(), p });
    return p;
  }
  function digitsOf(d) {
    if (Number.isInteger(d.digits)) return Math.max(2, d.digits);
    const s = String(d.last || ""); return Math.max(2, s.includes(".") ? s.split(".")[1].length : 2);
  }
  function aggregate(candles, step) {
    if (step === 300) return candles.map(([t, o, h, l, c]) => ({ time: t, open: o, high: h, low: l, close: c }));
    const out = [];
    for (const [t, o, h, l, c] of candles) {
      const b = Math.floor(t / step) * step, last = out[out.length - 1];
      if (last && last.time === b) { last.high = Math.max(last.high, h); last.low = Math.min(last.low, l); last.close = c; }
      else out.push({ time: b, open: o, high: h, low: l, close: c });
    }
    return out;
  }
  // variation sur les 288 dernières bougies 5 min (24 h de cotation), même si l'instantané en contient plus
  const change = (d) => { const c = d && d.candles && d.candles.slice(-288); return c && c.length > 1 ? (c[c.length - 1][4] / c[0][1] - 1) * 100 : null; };
  // Zone d'entrée : même règle que les messages Telegram (signals.entry_guidance)
  function zoneOf(s) {
    const e = s.entry, t = s.take_profit, sl = s.stop_loss;
    if ([e, t, sl].some((v) => v == null)) return null;
    const limit = (t + sl) / 2, against = e - 0.5 * (e - sl);
    const rr = Math.abs(t - e) / Math.abs(e - sl || 1);
    if (rr < 1) return null;
    return { lo: Math.min(limit, against), hi: Math.max(limit, against) };
  }

  // ------------------------------------------------------------------ montage
  function mount(root, opts) {
    injectStyle();
    opts = opts || {};
    root.replaceChildren();
    root.classList.add("lc");
    root.innerHTML = `
      <div class="lc-head">
        <div class="lc-title"><h3>Graphique live</h3><span class="pill">Actualisé toutes les 5 min</span></div>
        <div class="seg" role="group" aria-label="Unité de temps">${Object.keys(TF).map((k) => `<button type="button" data-tf="${k}">${TF_LABEL[k]}</button>`).join("")}</div>
      </div>
      <div class="lc-chips" role="group" aria-label="Actif affiché"></div>
      <div class="lc-sig" hidden></div>
      <div class="lc-box"><div class="lc-ov"></div><div class="lc-zones"></div></div>
      <div class="lc-foot">
        <div class="lc-leg"><span><i class="tri"></i>Entrée d'un signal</span><span><i class="ring"></i>Sortie (TP ou SL)</span><span><i class="zn"></i>Zone d'entrée</span><span><i class="ln"></i>TP</span><span><i class="ln sl"></i>SL</span></div>
        <div class="lc-hint">Molette ou pincement pour zoomer · glisser pour se déplacer · double-clic pour recentrer</div>
      </div>
      ${opts.how ? `<div class="lc-how"></div>` : ""}`;
    if (opts.how) root.querySelector(".lc-how").textContent = opts.how;
    const chipsEl = root.querySelector(".lc-chips"), sigEl = root.querySelector(".lc-sig"), box = root.querySelector(".lc-box");
    const ov = root.querySelector(".lc-ov"), zonesEl = root.querySelector(".lc-zones");
    const tfBtns = [...root.querySelectorAll("[data-tf]")];

    const base = opts.base || "", suffix = base ? "-" + base.replace(/[^a-z0-9]/gi, "") : "";
    const assetKey = STORE_KEY + suffix, tfKey = TF_KEY + suffix;
    let assets = [], current = null, tf = TF[store.get(tfKey)] ? store.get(tfKey) : (TF[opts.tf] ? opts.tf : "5"), seq = 0;
    let data = null, bars = [], digits = 2, chart = null, series = null, priceLines = [], lastKey = "", svgMode = false;
    const saved = () => store.get(assetKey);
    const paintTf = () => tfBtns.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.tf === tf)));
    paintTf();

    function colors() {
      return { up: css("--up", "#2a78d6"), dn: css("--dn", "#eb6834"), neu: css("--neu", "#898781"), text: css("--text", "#18181b"),
               muted: css("--muted", "#6b6a65"), faint: css("--faint", "#a3a19b"), grid: css("--grid", "#ecebe6"), line: css("--line", "#e6e4de"),
               card: css("--card", "#ffffff") };
    }
    function chartOptions() {
      const c = colors();
      return {
        layout: { background: { type: "solid", color: c.card }, textColor: c.muted, fontFamily: '"Geist Mono", ui-monospace, monospace', fontSize: 11, attributionLogo: true },
        grid: { vertLines: { color: c.grid }, horzLines: { color: c.grid } },
        rightPriceScale: { borderColor: c.line, scaleMargins: { top: 0.14, bottom: 0.1 } },
        timeScale: { borderColor: c.line, timeVisible: true, secondsVisible: false, rightOffset: 6, barSpacing: 9,
                     tickMarkFormatter: (t, type) => type <= 2 ? new Date(t * 1000).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" }) : hhmm(t) },
        crosshair: { mode: 0, vertLine: { color: c.muted, labelBackgroundColor: c.muted, style: 3 }, horzLine: { color: c.muted, labelBackgroundColor: c.muted, style: 3 } },
        localization: { locale: "fr-FR", priceFormatter: (p) => fmt(p, digits),
                        timeFormatter: (t) => new Date(t * 1000).toLocaleString("fr-FR", { weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) },
      };
    }
    function ensureChart() {
      if (chart || svgMode) return !!chart;
      const L = window.LightweightCharts;
      if (!L || typeof L.createChart !== "function") { svgMode = true; box.classList.add("lc-svgmode"); return false; }
      chart = L.createChart(box, { ...chartOptions(), autoSize: true });
      const c = colors();
      series = chart.addCandlestickSeries({ upColor: c.up, downColor: c.dn, wickUpColor: c.up, wickDownColor: c.dn, borderVisible: false,
                                            priceLineColor: c.text, priceLineStyle: 2 });
      chart.subscribeCrosshairMove((p) => { legend(p && p.time ? p.seriesData.get(series) : null); placeZones(); });
      chart.timeScale().subscribeVisibleLogicalRangeChange(() => requestAnimationFrame(placeZones));
      box.addEventListener("dblclick", showDefaultRange);
      if (window.ResizeObserver) new ResizeObserver(() => requestAnimationFrame(placeZones)).observe(box);
      return true;
    }
    function recolor() {
      if (!chart) { if (svgMode && data) drawSvg(); return; }
      const c = colors();
      chart.applyOptions(chartOptions());
      series.applyOptions({ upColor: c.up, downColor: c.dn, wickUpColor: c.up, wickDownColor: c.dn, priceLineColor: c.text });
      paintLevels(); paintMarkers();
    }
    function showDefaultRange() {
      if (!chart || !bars.length) return;
      const n = bars.length, show = tf === "5" ? 120 : tf === "15" ? 64 : n;
      if (n > show) chart.timeScale().setVisibleLogicalRange({ from: n - show, to: n + 5 });
      else chart.timeScale().fitContent();
      chart.priceScale("right").applyOptions({ autoScale: true });
    }

    // Légende en haut à gauche : bougie survolée, sinon la dernière
    function legend(bar) {
      if (!data) { ov.innerHTML = ""; return; }
      const b = bar && bar.open !== undefined ? bar : bars[bars.length - 1];
      if (!b) return;
      const ch = (b.close / b.open - 1) * 100;
      const lastTs = data.candles[data.candles.length - 1][0] + 300;
      ov.innerHTML = `<div class="n">${escHtml(data.label)}<span>${TF_LABEL[tf]}</span></div>
        <div class="o"><span>O ${fmt(b.open, digits)}</span><span>H ${fmt(b.high, digits)}</span><span>B ${fmt(b.low, digits)}</span><span>C ${fmt(b.close, digits)}</span><span style="color:var(${ch >= 0 ? "--up-text" : "--dn-text"})">${sgnPct(ch)}</span></div>
        <div class="a">Dernière clôture ${hhmm(lastTs)}, ${ago(new Date(lastTs * 1000).toISOString())}</div>`;
    }
    const escHtml = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

    // Niveaux des signaux ouverts : TP, SL, entrée
    function paintLevels() {
      if (!series) return;
      for (const l of priceLines) series.removePriceLine(l);
      priceLines = [];
      const c = colors();
      for (const s of (data && data.open_signals) || []) {
        for (const [v, color, title] of [[s.take_profit, c.up, "TP"], [s.stop_loss, c.dn, "SL"], [s.entry, c.neu, "Entrée"]]) {
          if (v == null) continue;
          priceLines.push(series.createPriceLine({ price: v, color, lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title }));
        }
      }
    }
    // Flèches d'entrée et ronds de sortie des trades de la période
    function paintMarkers() {
      if (!series) return;
      const c = colors(), step = TF[tf], first = bars.length ? bars[0].time : 0;
      const snap = (iso) => Math.floor(new Date(iso).getTime() / 1000 / step) * step;
      const m = [];
      const push = (time, obj) => { if (time >= first) m.push({ time, ...obj }); };
      for (const t of (data && data.trades) || []) {
        const long = t.direction === "long";
        push(snap(t.created_at), { position: long ? "belowBar" : "aboveBar", shape: long ? "arrowUp" : "arrowDown", color: long ? c.up : c.dn, text: long ? "Achat" : "Vente" });
        if (t.closed_at) {
          const col = t.status === "tp" ? c.up : t.status === "sl" ? c.dn : c.neu;
          const lab = (t.status === "tp" ? "TP " : t.status === "sl" ? "SL " : "Expiré ") + (t.pnl_pct == null ? "" : sgnPct(t.pnl_pct));
          push(snap(t.closed_at), { position: long ? "aboveBar" : "belowBar", shape: "circle", color: col, text: lab });
        }
      }
      for (const s of (data && data.open_signals) || []) {
        const long = s.direction === "long";
        push(snap(s.created_at), { position: long ? "belowBar" : "aboveBar", shape: long ? "arrowUp" : "arrowDown", color: long ? c.up : c.dn, text: (long ? "Achat" : "Vente") + " en cours" });
      }
      m.sort((a, b) => a.time - b.time);
      series.setMarkers(m);
    }
    // Zones d'entrée des signaux ouverts, calées sur l'échelle du graphique
    function placeZones() {
      zonesEl.replaceChildren();
      if (!chart || !data) return;
      const scaleW = chart.priceScale("right").width(), paneW = box.clientWidth - scaleW;
      const step = TF[tf];
      for (const s of data.open_signals || []) {
        const z = zoneOf(s); if (!z) continue;
        const y1 = series.priceToCoordinate(z.hi), y2 = series.priceToCoordinate(z.lo);
        if (y1 === null || y2 === null) continue;
        let x = chart.timeScale().timeToCoordinate(Math.floor(new Date(s.created_at).getTime() / 1000 / step) * step);
        if (x === null) x = 0;
        const d = document.createElement("div");
        d.className = "lc-zone" + (s.direction === "short" ? " short" : "");
        Object.assign(d.style, { left: Math.max(0, x) + "px", width: Math.max(0, paneW - Math.max(0, x)) + "px", top: Math.min(y1, y2) + "px", height: Math.max(2, Math.abs(y2 - y1)) + "px" });
        zonesEl.appendChild(d);
      }
    }
    function signalStrip() {
      const sigs = (data && data.open_signals) || [];
      sigEl.hidden = !sigs.length;
      sigEl.innerHTML = sigs.map((s) => {
        const long = s.direction === "long", rr = Math.abs(s.take_profit - s.entry) / Math.abs(s.entry - s.stop_loss || 1);
        return `<span><span class="pill ${long ? "up" : "dn"}"><span class="d"></span>${long ? "Achat" : "Vente"} en cours</span></span>
          <span class="mono">Entrée ${fmt(s.entry, digits)} · TP ${fmt(s.take_profit, digits)} · SL ${fmt(s.stop_loss, digits)}</span>
          <span>Gain/risque <b>${rr.toFixed(2).replace(".", ",")}</b>${s.expires_at ? ` · expire à ${hhmm(new Date(s.expires_at).getTime() / 1000)}` : ""}</span>`;
      }).join("<br>");
    }

    // Graphique SVG de secours (bibliothèque indisponible)
    function drawSvg() {
      const plot = box; plot.querySelectorAll("svg").forEach((n) => n.remove());
      const cs = bars.slice(-120), c = colors();
      if (!cs.length) return;
      const W = Math.max(320, plot.clientWidth || 900), H = W < 500 ? 280 : 360, left = 6, right = 78, top = 40, bottom = 26;
      let min = Math.min(...cs.map((k) => k.low)), max = Math.max(...cs.map((k) => k.high));
      for (const s of data.open_signals || []) for (const v of [s.stop_loss, s.take_profit]) if (v != null) { min = Math.min(min, v); max = Math.max(max, v); }
      const pad = (max - min) * 0.06 || 1; min -= pad; max += pad;
      const band = (W - left - right) / cs.length, x = (i) => left + i * band + band / 2, y = (v) => top + (max - v) / (max - min) * (H - top - bottom);
      const bw = Math.max(1.5, Math.min(9, band - 2));
      let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Bougies ${escHtml(data.label)}">`;
      for (let g = 0; g <= 4; g++) { const v = min + (max - min) * g / 4; s += `<line x1="${left}" x2="${W - right}" y1="${y(v)}" y2="${y(v)}" stroke="${c.grid}"/><text x="${W - right + 6}" y="${y(v) + 4}">${fmt(v, digits)}</text>`; }
      cs.forEach((k, i) => {
        const col = k.close >= k.open ? c.up : c.dn;
        s += `<line x1="${x(i)}" x2="${x(i)}" y1="${y(k.high)}" y2="${y(k.low)}" stroke="${col}"/><rect x="${x(i) - bw / 2}" y="${y(Math.max(k.open, k.close))}" width="${bw}" height="${Math.max(1, Math.abs(y(k.open) - y(k.close)))}" fill="${col}" rx="1"/>`;
        if (i % Math.ceil(cs.length / 6) === 0) s += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle">${hhmm(k.time)}</text>`;
      });
      for (const sg of data.open_signals || []) for (const [v, col, t] of [[sg.take_profit, c.up, "TP"], [sg.stop_loss, c.dn, "SL"], [sg.entry, c.neu, "Entrée"]]) if (v != null) s += `<line x1="${left}" x2="${W - right}" y1="${y(v)}" y2="${y(v)}" stroke="${col}" stroke-dasharray="5 4"/><text x="${W - right - 4}" y="${y(v) - 4}" text-anchor="end" style="fill:${col}">${t} ${fmt(v, digits)}</text>`;
      plot.insertAdjacentHTML("beforeend", s + "</svg>");
    }

    function render(resetView) {
      const step = TF[tf];
      bars = aggregate(data.candles, step);
      digits = digitsOf(data);
      signalStrip();
      if (ensureChart()) {
        series.applyOptions({ priceFormat: { type: "price", precision: digits, minMove: Math.pow(10, -digits) } });
        chart.applyOptions({ localization: chartOptions().localization });
        series.setData(bars);
        paintLevels(); paintMarkers();
        if (resetView) showDefaultRange();
        legend(null);
        requestAnimationFrame(placeZones);
      } else { legend(null); drawSvg(); }
    }
    function empty(msg) {
      data = null; bars = [];
      if (series) { series.setData([]); series.setMarkers([]); paintLevels(); }
      zonesEl.replaceChildren(); sigEl.hidden = true;
      ov.innerHTML = `<div class="n">${escHtml(msg)}</div>`;
    }

    async function refresh(force) {
      const key = current, mine = ++seq;
      if (!key) return;
      const d = await snapshot(key, force ? 0 : 55000, base);
      if (mine !== seq) return;               // un choix plus récent est en cours de chargement
      if (!d || !(d.candles || []).length) { empty("Pas encore d'instantané pour cet actif : il est publié au prochain passage du bot."); lastKey = ""; return; }
      const sig = key + "|" + tf;
      const same = data && data.updated_at === d.updated_at && sig === lastKey;
      if (same) { legend(null); return; }
      const reset = sig !== lastKey;
      data = d; lastKey = sig;
      render(reset);
    }
    async function paintChips() {
      chipsEl.innerHTML = assets.map(([k, l, trial]) => `<button type="button" class="lc-chip" data-k="${escHtml(k)}" aria-pressed="${k === current}">${escHtml(shortLabel(l))}<span class="ch"></span>${trial ? '<span class="es">essai</span>' : ""}</button>`).join("");
      await Promise.all(assets.map(async ([k]) => {
        const d = await snapshot(k, 55000, base); const v = change(d);
        const el = chipsEl.querySelector(`[data-k="${CSS.escape(k)}"] .ch`);
        if (el && v !== null) { el.textContent = sgnPct(v); el.style.color = `var(${v >= 0 ? "--up-text" : "--dn-text"})`; el.title = "Variation sur les dernières 24 h de cotation"; }
      }));
    }
    function choose(key, remember) {
      if (!assets.some(([a]) => a === key)) return;
      current = key;
      if (remember) store.set(assetKey, key);
      chipsEl.querySelectorAll(".lc-chip").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.k === key)));
      refresh();
    }
    function setAssets(list) {
      const next = (list && list.length) ? list : DEFAULT_ASSETS;
      const same = JSON.stringify(next) === JSON.stringify(assets);
      assets = next;
      // lien depuis Telegram (index.html?actif=nasdaq) : l'actif du message passe en premier, sans être mémorisé
      let fromUrl = null;
      try { fromUrl = new URLSearchParams(location.search).get("actif"); } catch (e) { /* ancienne adresse */ }
      const pick = [current, fromUrl, saved(), opts.prefer].find((k) => k && assets.some(([a]) => a === k)) || assets[0][0];
      current = pick;
      if (!same) paintChips();
      refresh();
    }
    chipsEl.addEventListener("click", (ev) => { const b = ev.target.closest(".lc-chip"); if (b) choose(b.dataset.k, true); });
    tfBtns.forEach((b) => b.addEventListener("click", () => { tf = b.dataset.tf; store.set(tfKey, tf); paintTf(); if (data) { lastKey = current + "|" + tf; render(true); } }));

    // Mise à jour : chaque minute (le bot publie toutes les 5 min), au changement de thème et de taille
    setInterval(() => { refresh(); paintChips(); }, 60000);
    let t = null;
    const later = () => { clearTimeout(t); t = setTimeout(recolor, 60); };
    new MutationObserver(later).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    try { matchMedia("(prefers-color-scheme: dark)").addEventListener("change", later); } catch (e) { /* ancien navigateur */ }
    if (svgMode || !window.LightweightCharts) addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { if (data && svgMode) drawSvg(); }, 200); });

    setAssets(opts.assets);   // déclenche le premier chargement
    return { setAssets, select: (k) => choose(k, false), refresh: () => refresh(true), hasSavedChoice: () => !!saved(), current: () => current };
  }

  window.LiveChart = { mount, snapshot, zoneOf, DEFAULT_ASSETS };
})();
