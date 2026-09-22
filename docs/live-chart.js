/* Graphique live partagé (tableau de bord et simulation de compte).
 *
 * Affiche les bougies 5 min publiées par le bot à chaque passage (docs/live/<actif>.json) avec les
 * niveaux des signaux ouverts : entrée, objectif, stop. Aucune dépendance, SVG pur.
 *
 * Utilisation :
 *   const live = LiveChart.mount(document.querySelector("#conteneur"), { assets: [["bitcoin", "Bitcoin"], …] });
 *   live.setAssets(liste);   // met à jour la liste d'actifs
 *   live.select("bitcoin");  // change d'actif
 *
 * Le choix d'actif est mémorisé dans le navigateur et partagé entre les pages. Le graphique se
 * redessine seul : chaque minute, au changement de thème et au redimensionnement.
 */
(function () {
  "use strict";
  const SVG = "http://www.w3.org/2000/svg";
  const STORE_KEY = "tb-live-asset";
  const DEFAULT_ASSETS = [["nasdaq", "Nasdaq 100 (NQ)"], ["sp500", "S&P 500 (ES)"], ["bitcoin", "Bitcoin (BTC/USD)"],
                          ["ethereum", "Ethereum (ETH/USD)"], ["gold", "Or (XAU/USD)"],
                          ["oil", "Pétrole WTI (CL)"], ["euro", "Euro / dollar (6E)"]];

  // Palette validée (bleu / orange lisibles en cas de daltonisme), mêmes valeurs que le tableau de bord.
  const CSS = `
  :root { --c-tp: #2a78d6; --c-sl: #eb6834; --c-exp: #898781; --c-grid: #e1e0d9; --c-axis: #c3c2b7; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --c-tp: #3987e5; --c-sl: #d95926; --c-exp: #898781; --c-grid: #2c2c2a; --c-axis: #383835; } }
  :root[data-theme="dark"] { --c-tp: #3987e5; --c-sl: #d95926; --c-exp: #898781; --c-grid: #2c2c2a; --c-axis: #383835; }
  .lc-head { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; justify-content: space-between; margin-bottom: 8px; }
  .lc-head select { width: auto; min-width: 180px; padding: 9px 10px; border: 1px solid var(--line); border-radius: 8px;
                    background: var(--bg); color: var(--text); font: inherit; }
  .lc-right { text-align: right; }
  .lc-price { font-size: 22px; font-weight: 650; }
  .lc-meta, .lc-how { font-size: 12px; color: var(--muted); }
  .lc-how { margin-top: 6px; }
  .lc-plot svg { display: block; width: 100%; height: auto; font: 12px system-ui, -apple-system, "Segoe UI", sans-serif; }
  .lc-plot svg text { fill: var(--muted); }
  .lc-plot svg text.lc-v { fill: var(--text); font-weight: 600; }
  .lc-up { fill: var(--c-tp); } .lc-down { fill: var(--c-sl); }
  .lc-lvl { stroke-dasharray: 5 4; stroke-width: 1.5; fill: none; }
  .lc-legend { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 12px; color: var(--muted); margin-top: 6px; }
  .lc-legend i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; vertical-align: -2px; margin-right: 5px; }
  .lc-empty { font-size: 13px; color: var(--muted); padding: 18px 0; }
  .lc-tip { position: fixed; z-index: 50; pointer-events: none; background: var(--card); color: var(--text); border: 1px solid var(--line);
            border-radius: 8px; padding: 8px 10px; font-size: 12px; box-shadow: 0 4px 16px rgba(0,0,0,.12); display: none; max-width: 260px; }
  .lc-tip b { font-size: 14px; } .lc-tip .r { display: flex; gap: 8px; justify-content: space-between; }
  .lc-tip .k { display: inline-block; width: 12px; height: 2px; vertical-align: 3px; margin-right: 6px; }`;

  function injectStyle() {
    if (document.getElementById("lc-style")) return;
    const st = document.createElement("style");
    st.id = "lc-style";
    st.textContent = CSS;
    document.head.appendChild(st);
  }
  const el = (tag, attrs, parent) => {
    const n = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  const txt = (parent, x, y, str, attrs) => { const t = el("text", { x, y, ...(attrs || {}) }, parent); t.textContent = str; return t; };
  const fmt = (v) => Number(v).toLocaleString("fr-FR");
  const colors = () => {
    const c = getComputedStyle(document.documentElement);
    const g = (n, d) => (c.getPropertyValue(n).trim() || d);
    return { up: g("--c-tp", "#2a78d6"), down: g("--c-sl", "#eb6834"), neutral: g("--c-exp", "#898781"),
             grid: g("--c-grid", "#e1e0d9"), axis: g("--c-axis", "#c3c2b7"), card: g("--card", "#ffffff") };
  };
  function niceStep(span) {
    const raw = span / 4, p = Math.pow(10, Math.floor(Math.log10(raw))), m = raw / p;
    return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
  }
  function age(iso) {
    const min = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
    if (min < 1) return "à l'instant";
    if (min < 60) return `il y a ${min} min`;
    return `il y a ${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")}`;
  }

  // Une seule infobulle pour toute la page
  let tip = null;
  function tipEl() {
    if (!tip) { tip = document.createElement("div"); tip.className = "lc-tip"; tip.setAttribute("role", "tooltip"); document.body.appendChild(tip); }
    return tip;
  }
  function moveTip(ev) {
    const t = tipEl(), w = t.offsetWidth, h = t.offsetHeight;
    let x = ev.clientX + 14, y = ev.clientY + 14;
    if (x + w > innerWidth - 8) x = ev.clientX - w - 14;
    if (y + h > innerHeight - 8) y = ev.clientY - h - 14;
    t.style.left = x + "px"; t.style.top = y + "px";
  }
  function showTip(ev, title, rows) {
    const t = tipEl();
    t.replaceChildren();
    const b = document.createElement("b"); b.textContent = title; t.appendChild(b);
    for (const [key, val, color] of rows) {
      const r = document.createElement("div"); r.className = "r";
      const k = document.createElement("span");
      if (color) { const i = document.createElement("i"); i.className = "k"; i.style.background = color; k.appendChild(i); }
      k.appendChild(document.createTextNode(key));
      const v = document.createElement("strong"); v.textContent = val;
      r.append(k, v); t.appendChild(r);
    }
    t.style.display = "block"; moveTip(ev);
  }
  const hideTip = () => { if (tip) tip.style.display = "none"; };

  async function fetchSnapshot(key) {
    for (const u of [`live/${key}.json`, `../data/live/${key}.json`, `/data/live/${key}.json`]) {
      try { const r = await fetch(u + "?t=" + Date.now(), { cache: "no-store" }); if (r.ok) return await r.json(); } catch (e) { /* suivant */ }
    }
    return null;
  }

  function draw(plot, d) {
    const c = colors(), cs = d.candles, lvls = d.open_signals || [];
    const W = Math.max(320, Math.round(plot.clientWidth || 900)), H = W < 500 ? 260 : 320;
    const left = 6, right = 74, top = 12, bottom = 26;
    const lows = cs.map((k) => k[3]), highs = cs.map((k) => k[2]);
    for (const s of lvls) for (const v of [s.stop_loss, s.take_profit, s.entry]) if (v != null) { lows.push(v); highs.push(v); }
    let min = Math.min(...lows), max = Math.max(...highs);
    const pad = (max - min) * 0.06 || 1; min -= pad; max += pad;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `Bougies 5 minutes ${d.label}` }, plot);
    const band = (W - left - right) / cs.length;
    const x = (i) => left + i * band + band / 2;
    const y = (v) => top + (max - v) / (max - min) * (H - top - bottom);
    const step = niceStep(max - min);
    for (let g = Math.ceil(min / step) * step; g <= max; g += step) {
      el("line", { x1: left, x2: W - right, y1: y(g), y2: y(g), stroke: c.grid }, svg);
      txt(svg, W - right + 6, y(g) + 4, fmt(g), { style: "font-size:11px" });
    }
    // moins d'étiquettes d'heure sur petit écran pour qu'elles ne se chevauchent pas
    const bw = Math.max(1.5, Math.min(11, band - 2)), every = Math.ceil(cs.length / (W < 500 ? 4 : 6));
    cs.forEach((k, i) => {
      const [ts, o, h, l, cl] = k, up = cl >= o;
      el("line", { x1: x(i), x2: x(i), y1: y(h), y2: y(l), stroke: up ? c.up : c.down, "stroke-width": 1 }, svg);
      const y0 = y(Math.max(o, cl)), y1 = y(Math.min(o, cl));
      el("rect", { class: up ? "lc-up" : "lc-down", x: x(i) - bw / 2, y: y0, width: bw, height: Math.max(1, y1 - y0), rx: 1 }, svg);
      if (i % every === 0) {
        const anchor = x(i) < 24 ? "start" : "middle";   // la première étiquette ne doit pas être coupée
        txt(svg, anchor === "start" ? left : x(i), H - 8,
            new Date(ts * 1000).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }),
            { "text-anchor": anchor, style: "font-size:11px" });
      }
    });
    // Niveaux des signaux ouverts : identifiés par leur étiquette, jamais par la couleur seule
    for (const s of lvls) {
      for (const [val, label, color] of [[s.entry, "Entrée", c.neutral], [s.take_profit, "Objectif", c.up], [s.stop_loss, "Stop", c.down]]) {
        if (val == null) continue;
        el("line", { class: "lc-lvl", x1: left, x2: W - right, y1: y(val), y2: y(val), stroke: color }, svg);
        txt(svg, left + 4, y(val) - 5, `${label} ${fmt(val)}`, { class: "lc-v", style: "font-size:11px" });
      }
    }
    const last = cs[cs.length - 1];
    el("circle", { cx: x(cs.length - 1), cy: y(last[4]), r: 4, fill: last[4] >= last[1] ? c.up : c.down, stroke: c.card, "stroke-width": 2 }, svg);
    // Survol : la bougie la plus proche
    const cross = el("line", { y1: top, y2: H - bottom, stroke: c.axis, visibility: "hidden" }, svg);
    const hit = el("rect", { x: left, y: top, width: W - left - right, height: H - top - bottom, fill: "transparent" }, svg);
    hit.addEventListener("pointermove", (ev) => {
      const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) / r.width * W;
      const i = Math.max(0, Math.min(cs.length - 1, Math.floor((px - left) / band))), k = cs[i];
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("visibility", "visible");
      const when = new Date(k[0] * 1000).toLocaleString("fr-FR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
      showTip(ev, when, [["Ouverture", fmt(k[1]), null], ["Plus haut", fmt(k[2]), null], ["Plus bas", fmt(k[3]), null],
                         ["Clôture", fmt(k[4]), k[4] >= k[1] ? c.up : c.down]]);
    });
    hit.addEventListener("pointerleave", () => { hideTip(); cross.setAttribute("visibility", "hidden"); });
    const legend = document.createElement("div"); legend.className = "lc-legend";
    const keys = [["Bougie haussière", c.up], ["Bougie baissière", c.down]];
    if (lvls.length) keys.push(["Niveaux des signaux ouverts (en pointillés, étiquetés)", c.neutral]);
    for (const [label, color] of keys) {
      const s = document.createElement("span"), i = document.createElement("i");
      i.style.background = color; s.append(i, document.createTextNode(label)); legend.appendChild(s);
    }
    plot.appendChild(legend);
  }

  function mount(root, opts) {
    injectStyle();
    opts = opts || {};
    root.replaceChildren();
    const head = document.createElement("div"); head.className = "lc-head";
    const sel = document.createElement("select"); sel.setAttribute("aria-label", "Actif du graphique live");
    const right = document.createElement("div"); right.className = "lc-right";
    const price = document.createElement("div"); price.className = "lc-price"; price.textContent = "—";
    const meta = document.createElement("div"); meta.className = "lc-meta"; meta.textContent = "Chargement…";
    right.append(price, meta);
    const selWrap = document.createElement("div"); selWrap.appendChild(sel);
    head.append(selWrap, right);
    const plot = document.createElement("div"); plot.className = "lc-plot";
    const how = document.createElement("div"); how.className = "lc-how";
    how.textContent = opts.how || ("Bougies de 5 minutes. Les traits horizontaux sont les signaux ouverts sur cet actif : entrée, objectif et stop. "
      + "L'image se met à jour à chaque passage du bot, soit environ toutes les 5 minutes : ce n'est pas un flux temps réel.");
    root.append(head, plot, how);

    let assets = [], seq = 0;
    const saved = () => { try { return localStorage.getItem(STORE_KEY); } catch (e) { return null; } };

    async function refresh() {
      const key = sel.value, mine = ++seq;
      if (!key) return;
      const d = await fetchSnapshot(key);
      if (mine !== seq) return;               // un choix plus récent est en cours de chargement
      hideTip();
      plot.replaceChildren();
      if (!d || !(d.candles || []).length) {
        price.textContent = "—";
        meta.textContent = "Pas encore d'instantané : il est publié au prochain passage du bot.";
        const e = document.createElement("div"); e.className = "lc-empty"; e.textContent = "Aucune bougie disponible pour cet actif.";
        plot.appendChild(e);
        return;
      }
      price.textContent = fmt(d.last);
      meta.textContent = `${d.label} · bougies 5 min · mis à jour ${age(d.updated_at)}`;
      draw(plot, d);
    }
    function setAssets(list) {
      assets = (list && list.length) ? list : DEFAULT_ASSETS;
      const cur = sel.value;
      sel.replaceChildren(...assets.map(([k, l]) => { const o = document.createElement("option"); o.value = k; o.textContent = l; return o; }));
      const pick = [cur, saved(), opts.prefer].find((k) => k && assets.some(([a]) => a === k));
      if (pick) sel.value = pick;
      if (pick !== cur) refresh();
    }
    function select(key) {
      if (!assets.some(([a]) => a === key) || sel.value === key) return;
      sel.value = key; refresh();
    }
    sel.addEventListener("change", () => { try { localStorage.setItem(STORE_KEY, sel.value); } catch (e) { /* stockage indisponible */ } refresh(); });

    // Redessiner : chaque minute, au changement de thème, au redimensionnement
    setInterval(refresh, 60000);
    let t = null;
    const later = () => { clearTimeout(t); t = setTimeout(refresh, 200); };
    addEventListener("resize", later);
    new MutationObserver(later).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    try { matchMedia("(prefers-color-scheme: dark)").addEventListener("change", later); } catch (e) { /* ancien navigateur */ }

    setAssets(opts.assets);   // déclenche le premier chargement
    return { setAssets, select, refresh, hasSavedChoice: () => !!saved() };
  }

  window.LiveChart = { mount, DEFAULT_ASSETS };
})();
