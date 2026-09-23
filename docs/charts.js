/* Petits graphiques SVG du site (sans dépendance) : courbe du résultat, issues par catégorie,
 * trades par heure, réussite par indicateur contre le hasard. Couleurs : bleu = TP, orange = SL,
 * gris = expiré ou hasard. Une infobulle unique (#tip) sert tous les graphiques de la page.
 * Exposé dans window.YKCharts.
 */
(function () {
  "use strict";
  const SVGNS = "http://www.w3.org/2000/svg";
  const Y = () => window.YK;
  const el = (tag, attrs = {}, parent = null) => { const n = document.createElementNS(SVGNS, tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); if (parent) parent.appendChild(n); return n; };
  const txt = (parent, x, y, str, attrs = {}) => { const t = el("text", { x, y, ...attrs }, parent); t.textContent = str; return t; };
  const col = () => { const c = getComputedStyle(document.documentElement), g = (n) => c.getPropertyValue(n).trim(); return { tp: g("--up"), sl: g("--dn"), exp: g("--neu"), grid: g("--grid"), axis: g("--c-axis"), card: g("--card"), text: g("--text"), line: g("--line") }; };

  let tip = null;
  function tipEl() { if (!tip) { tip = document.getElementById("tip") || Object.assign(document.createElement("div"), { id: "tip" }); tip.setAttribute("role", "tooltip"); if (!tip.parentNode) document.body.appendChild(tip); } return tip; }
  function showTip(evt, title, rows) {
    const t = tipEl(); t.replaceChildren();
    const b = document.createElement("b"); b.textContent = title; t.appendChild(b);
    for (const [key, val, color] of rows) {
      const r = document.createElement("div"); r.className = "r";
      const k = document.createElement("span"); if (color) { const i = document.createElement("i"); i.className = "k"; i.style.background = color; k.appendChild(i); } k.appendChild(document.createTextNode(key));
      const v = document.createElement("strong"); v.textContent = val; r.append(k, v); t.appendChild(r);
    }
    t.style.display = "block"; moveTip(evt);
  }
  function moveTip(evt) { const t = tipEl(), w = t.offsetWidth, h = t.offsetHeight; let x = evt.clientX + 14, y = evt.clientY + 14; if (x + w > innerWidth - 8) x = evt.clientX - w - 14; if (y + h > innerHeight - 8) y = evt.clientY - h - 14; t.style.left = x + "px"; t.style.top = y + "px"; }
  const hideTip = () => { if (tip) tip.style.display = "none"; };
  const hover = (node, title, rows) => { node.addEventListener("pointerenter", (e) => showTip(e, title, rows)); node.addEventListener("pointermove", moveTip); node.addEventListener("pointerleave", hideTip); };

  function frame(root, title, how) {
    root.replaceChildren();
    if (title) { const h = document.createElement("h3"); h.textContent = title; root.appendChild(h); }
    if (how) { const p = document.createElement("div"); p.className = "how"; p.textContent = how; root.appendChild(p); }
    return root;
  }
  function empty(root, msg = "Pas encore de trade clôturé.") { const d = document.createElement("div"); d.className = "empty"; d.textContent = msg; root.appendChild(d); }
  function legend(root, items) {
    const l = document.createElement("div"); l.className = "legend";
    for (const [label, color, kind] of items) { const s = document.createElement("span"); const i = document.createElement("i"); if (kind) i.className = kind; if (color) i.style.background = color; s.append(i, document.createTextNode(label)); l.appendChild(s); }
    root.appendChild(l); return l;
  }
  const RESULT_ROWS = (st) => { const c = col(), f = Y(); return [["TP", String(st.tp), c.tp], ["SL", String(st.sl), c.sl], ["Expirés", String(st.expired), c.exp], ["Réussite", f.pct(st.win_rate), null], ["Hasard attendu", f.pct(st.neutral_win_rate), null], ["Résultat net", f.pctv(st.pnl_pct, 2), null]]; };
  // largeur utile du conteneur (sans ses marges intérieures) : le SVG est dessiné à l'échelle 1, textes nets
  const cw = (root, d) => { const st = getComputedStyle(root); return Math.round((root.clientWidth || d) - parseFloat(st.paddingLeft || 0) - parseFloat(st.paddingRight || 0)); };
  function niceStep(span) { const raw = span / 4, p = Math.pow(10, Math.floor(Math.log10(raw))); const m = raw / p; return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p; }

  // Courbe du résultat cumulé (un point par trade clôturé, en % du prix)
  function equityLine(root, pts, opts = {}) {
    frame(root, opts.title, opts.how);
    if (!pts || pts.length < 2) return empty(root, "La courbe apparaît à partir de deux trades clôturés.");
    const c = col(), f = Y(), W = Math.max(300, cw(root, 600)), H = opts.height || 220, left = 4, right = 48, top = 10, bottom = 26;
    const vals = [0, ...pts.map((p) => p.cum_pnl_pct)], min = Math.min(...vals), max = Math.max(...vals), span = (max - min) || 1;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.title || "Courbe du résultat" }, root);
    const n = pts.length;
    const x = (i) => left + i / n * (W - left - right), y = (v) => top + (max - v) / span * (H - top - bottom);
    const step = niceStep(span);
    for (let g = Math.ceil(min / step) * step; g <= max + 1e-9; g += step) {
      const zero = Math.abs(g) < 1e-9;
      el("line", { x1: left, x2: W - right, y1: y(g), y2: y(g), stroke: zero ? c.axis : c.grid, "stroke-dasharray": zero ? "0" : "2 4" }, svg);
      txt(svg, W - right + 8, y(g) + 4, (zero ? "0" : f.signed(g, step < 1 ? 1 : 0)) + " %", { class: "mono", style: "font-size:11px" });
    }
    const all = [{ cum_pnl_pct: 0 }, ...pts];
    const path = all.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.cum_pnl_pct).toFixed(1)}`).join(" ");
    const last = pts[n - 1], sign = last.cum_pnl_pct >= 0 ? c.tp : c.sl;
    el("path", { d: `${path} L${x(n).toFixed(1)},${y(0).toFixed(1)} Z`, fill: sign, "fill-opacity": 0.08 }, svg);
    el("path", { d: path, fill: "none", stroke: c.text, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }, svg);
    el("circle", { cx: x(n), cy: y(last.cum_pnl_pct), r: 4.5, fill: sign, stroke: c.card, "stroke-width": 2 }, svg);
    // dates : premier trade de chaque jour, sans chevauchement
    let lastX = -99;
    pts.forEach((p, i) => {
      const day = String(p.label || "").slice(0, 5); const prev = i ? String(pts[i - 1].label || "").slice(0, 5) : null;
      if (day && day !== prev && x(i + 1) - lastX > 52) { lastX = x(i + 1); txt(svg, Math.min(x(i + 1), W - right - 16), H - 6, day, { class: "mono", "text-anchor": "middle", style: "font-size:11px" }); }
    });
    const cross = el("line", { y1: top, y2: H - bottom, stroke: c.axis, visibility: "hidden" }, svg);
    const dot = el("circle", { r: 5, fill: c.text, stroke: c.card, "stroke-width": 2, visibility: "hidden" }, svg);
    const hit = el("rect", { x: left, y: top, width: W - left - right, height: H - top - bottom, fill: "transparent" }, svg);
    hit.addEventListener("pointermove", (e) => {
      const r = svg.getBoundingClientRect(); const px = (e.clientX - r.left) / r.width * W;
      const i = Math.max(1, Math.min(n, Math.round((px - left) / (W - left - right) * n))); const p = pts[i - 1];
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.setAttribute("visibility", "visible");
      dot.setAttribute("cx", x(i)); dot.setAttribute("cy", y(p.cum_pnl_pct)); dot.setAttribute("visibility", "visible");
      showTip(e, `${p.label} · ${f.shortLabel(p.asset_label)} ${p.direction === "long" ? "achat" : "vente"}`, [["Résultat", f.RES[p.status] || p.status, p.status === "tp" ? c.tp : p.status === "sl" ? c.sl : c.exp], ["Ce trade", f.pctv(p.pnl_pct, 2), null], ["Cumul net", f.pctv(p.cum_pnl_pct, 2), null]]);
    });
    hit.addEventListener("pointerleave", () => { hideTip(); cross.setAttribute("visibility", "hidden"); dot.setAttribute("visibility", "hidden"); });
  }

  // Barres empilées TP / SL / expirés, une ligne par catégorie (sans légende : une seule légende par groupe)
  function stackedOutcomes(root, rows, opts = {}) {
    frame(root, opts.title, opts.how);
    rows = rows.filter((r) => r.st && r.st.n > 0);
    if (!rows.length) return empty(root);
    const c = col(), f = Y(), W = Math.max(300, cw(root, 460)), rowH = 30, left = 96, right = 96, H = rows.length * rowH + 4;
    const max = Math.max(...rows.map((r) => r.st.n));
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.title || "" }, root);
    const x = (v) => left + v / max * (W - left - right);
    rows.forEach((r, i) => {
      const y = 4 + i * rowH, bh = 16;
      txt(svg, left - 10, y + bh / 2 + 4, r.label, { "text-anchor": "end", style: "font-size:12.5px;fill:var(--text)" });
      let cursor = 0;
      for (const [k, color] of [["tp", c.tp], ["sl", c.sl], ["expired", c.exp]]) {
        const v = r.st[k]; if (!v) continue;
        const x0 = x(cursor), x1 = x(cursor + v) - (cursor + v < r.st.n ? 2 : 0);
        const g = el("rect", { class: "mark", x: x0, y, width: Math.max(1, x1 - x0), height: bh, fill: color, rx: 3 }, svg);
        hover(g, r.label, RESULT_ROWS(r.st));
        if (x1 - x0 > 20) txt(svg, (x0 + x1) / 2, y + bh / 2 + 4, String(v), { "text-anchor": "middle", style: "fill:#fff;font-size:11px;font-weight:600" });
        cursor += v;
      }
      txt(svg, x(r.st.n) + 8, y + bh / 2 + 4, `${f.pct(r.st.win_rate, 0)} · ${r.st.n} tr.`, { class: "v", style: "font-size:11.5px" });
    });
  }

  // Réussite par critère contre le hasard attendu (barre + repère vertical)
  function rateBars(root, rows, opts = {}) {
    frame(root, opts.title, opts.how);
    rows = rows.filter((r) => r.st && r.st.n > 0).sort((a, b) => (b.st.edge ?? -1) - (a.st.edge ?? -1));
    if (!rows.length) return empty(root, "Aucun trade clôturé avec ce critère pour l'instant.");
    const c = col(), f = Y(), W = Math.max(520, cw(root, 760)), rowH = 30, left = 180, right = 96, H = rows.length * rowH + 24;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.title || "" }, root);
    const x = (v) => left + v * (W - left - right);
    for (const g of [0, 0.25, 0.5, 0.75, 1]) { el("line", { x1: x(g), x2: x(g), y1: 2, y2: H - 20, stroke: c.grid }, svg); txt(svg, x(g), H - 4, `${g * 100} %`, { class: "mono", "text-anchor": "middle", style: "font-size:11px" }); }
    rows.forEach((r, i) => {
      const y = 4 + i * rowH, bh = 16;
      txt(svg, left - 10, y + bh / 2 + 4, r.label, { "text-anchor": "end", style: "font-size:12.5px;fill:var(--text)" });
      const bar = el("rect", { class: "mark", x: x(0), y, width: Math.max(2, x(r.st.win_rate || 0) - x(0)), height: bh, fill: r.st.n >= 10 ? c.tp : c.exp, rx: 3 }, svg);
      hover(bar, r.label, [["Trades", String(r.st.n), null], ["Réussite", f.pct(r.st.win_rate), null], ["Hasard attendu", f.pct(r.st.neutral_win_rate), null], ["Avantage", f.signed((r.st.edge || 0) * 100, 1, " pts"), null], ["Poids appris", r.weight == null ? "n/a" : f.num(r.weight, 2), null]]);
      if (r.st.neutral_win_rate != null) el("rect", { x: x(r.st.neutral_win_rate) - 1, y: y - 3, width: 2, height: bh + 6, fill: c.text }, svg);
      txt(svg, x(Math.max(r.st.win_rate || 0, r.st.neutral_win_rate || 0)) + 8, y + bh / 2 + 4, `${f.pct(r.st.win_rate, 0)} (${r.st.n})`, { class: "v", style: "font-size:11.5px" });
    });
    legend(root, [["Réussite, au moins 10 trades", c.tp], ["Moins de 10 trades : pas encore significatif", c.exp], ["Hasard attendu", null, "tick"]]);
  }

  // Colonnes : trades par heure d'émission (heure de Paris)
  function hourColumns(root, byHour, opts = {}) {
    frame(root, opts.title, opts.how);
    const hours = Object.keys(byHour || {}).sort();
    const total = hours.reduce((a, h) => a + byHour[h].n, 0);
    if (!total) return empty(root);
    const c = col(), W = Math.max(300, cw(root, 460)), H = 180, left = 26, bottom = 22, top = 16;
    const max = Math.max(...hours.map((h) => byHour[h].n));
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.title || "" }, root);
    const slot = (W - left) / 24, bw = Math.min(14, slot - 4);
    const y = (v) => top + (1 - v / max) * (H - top - bottom);
    el("line", { x1: left, x2: W, y1: y(0), y2: y(0), stroke: c.axis }, svg);
    txt(svg, left - 6, y(max) + 4, String(max), { class: "mono", "text-anchor": "end", style: "font-size:11px" });
    hours.forEach((h, i) => {
      const st = byHour[h]; const x0 = left + i * slot + (slot - bw) / 2;
      if (i % 3 === 0) txt(svg, left + i * slot + slot / 2, H - 6, `${h}h`, { class: "mono", "text-anchor": "middle", style: "font-size:11px" });
      if (!st.n) return;
      const hit = el("rect", { x: left + i * slot, y: top, width: slot, height: H - top - bottom, fill: "transparent" }, svg);
      const bar = el("rect", { class: "mark", x: x0, y: y(st.n), width: bw, height: y(0) - y(st.n), fill: st.n >= 3 && st.win_rate > st.neutral_win_rate ? c.tp : c.exp, rx: 3 }, svg);
      for (const t of [hit, bar]) hover(t, `${h}h, heure de Paris`, RESULT_ROWS(st));
    });
    legend(root, [["Heure au-dessus du hasard, au moins 3 trades", c.tp], ["Autres heures", c.exp]]);
  }

  window.YKCharts = { equityLine, stackedOutcomes, rateBars, hourColumns, legend, showTip, moveTip, hideTip, col };
})();
