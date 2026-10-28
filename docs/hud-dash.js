/* Panneaux « HUD » du test : résumé en 5 indicateurs, jauge en anneaux (fiabilité, taux de réussite du bot, hasard), barres à rayures par actif. */
(function () {
  const Y = window.YK, NS = "http://www.w3.org/2000/svg";
  const polar = (cx, cy, r, a) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  const arc = (cx, cy, r, a0, a1) => { const [x0, y0] = polar(cx, cy, r, a0), [x1, y1] = polar(cx, cy, r, a1);
    return `M${x0.toFixed(1)},${y0.toFixed(1)} A${r},${r} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${x1.toFixed(1)},${y1.toFixed(1)}`; };
  function ring(cx, cy, r, n, frac, color, w) {
    const step = Math.PI * 2 / n, gap = step * 0.28, start = -Math.PI / 2, lit = Math.round(Math.max(0, Math.min(1, frac)) * n);
    let out = "";
    for (let i = 0; i < n; i++) {
      const a0 = start + i * step + gap / 2, a1 = start + (i + 1) * step - gap / 2;
      out += `<path d="${arc(cx, cy, r, a0, a1)}" fill="none" stroke="${color}" stroke-width="${w}" opacity="${i < lit ? 1 : .16}"${i < lit ? ` style="filter:drop-shadow(0 0 3px ${color})"` : ""}/>`;
    }
    return out;
  }
  function build(d) {
    const v = d.overview.visible, pf = d.portfolio || {}, cur = pf.currency || "$", wrap = document.querySelector(".hero-row");
    if (!wrap || !v.n) return;
    const p = v.neutral_win_rate ?? 0.4, need = Math.ceil(7.84 * p * (1 - p) / 0.01), rel = Math.min(1, v.n / need);
    const tone = (x) => x >= 0 ? "up" : "dn", arrow = (x) => (x >= 0 ? "▲ " : "▼ ");
    const edge = v.edge * 100;
    const kpis = [
      pf.balance !== undefined ? ["Balance simulée", Y.money(pf.balance, cur, 0), `${arrow(pf.pnl_pct)}${Y.signed(pf.pnl_pct, 1)} %`, tone(pf.pnl_pct)] : null,
      ["Résultat cumulé", Y.signed(v.pnl_pct, 2) + " %", `${arrow(v.avg_pnl_pct)}${Y.signed(v.avg_pnl_pct, 2)} % par trade`, tone(v.avg_pnl_pct)],
      ["Trades clôturés", String(v.n), `${v.tp} TP · ${v.sl} SL · ${v.expired} exp.`, ""],
      ["Trades gagnants", Y.num(v.win_rate * 100, 1) + " %", `hasard ${Y.num(p * 100, 1)} %`, ""],
      ["Avantage", Y.signed(edge, 1) + " pts", `${arrow(edge)}face au hasard`, tone(edge)],
    ].filter(Boolean);
    const sum = document.createElement("div");
    sum.className = "card fx-sum";
    sum.innerHTML = `<div class="card-head"><h3>Résumé</h3><span class="faint">${Y.shortLabel ? "" : ""}mis à jour ${new Date(d.updated_at).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span></div>
      <div class="fx-kpis">${kpis.map(([l, val, sub, t]) => `<div class="fx-kpi"><small>${l}</small><b class="${t}">${val}</b><em class="${t}">${sub}</em></div>`).join("")}</div>`;
    wrap.before(sum);
    // jauge
    const g = document.createElement("div");
    g.className = "card fx-panel";
    g.innerHTML = `<div class="card-head"><h3>Fiabilité</h3></div><div class="fx-gauge"><svg viewBox="0 0 280 280" role="img" aria-label="Fiabilité de la mesure ${Math.round(rel * 100)} pour cent">
      <circle cx="140" cy="140" r="130" fill="none" stroke="var(--c-axis)" stroke-dasharray="1 5" stroke-linecap="round"/>
      <line x1="10" x2="270" y1="140" y2="140" stroke="var(--line)"/><line y1="10" y2="270" x1="140" x2="140" stroke="var(--line)"/>
      ${ring(140, 140, 112, 30, rel, "var(--brand)", 11)}${ring(140, 140, 90, 26, v.win_rate, "var(--info)", 9)}${ring(140, 140, 70, 22, p, "var(--neu)", 8)}
      <text x="140" y="146" text-anchor="middle" font-size="46" font-weight="600" style="filter:drop-shadow(0 0 8px rgba(127,243,200,.6))">${v.n}</text>
      <text x="140" y="168" text-anchor="middle" font-size="12" letter-spacing="2.4" opacity=".7">TRADES</text></svg>
      <div class="fx-legend"><span><i style="background:var(--brand)"></i>Fiabilité ${Math.round(rel * 100)} %</span><span><i style="background:var(--info)"></i>Bot ${Y.num(v.win_rate * 100, 0)} %</span><span><i style="background:var(--neu)"></i>Hasard ${Y.num(p * 100, 0)} %</span></div></div>`;
    wrap.appendChild(g);
    // barres par actif
    const rows = (d.assets || []).filter((a) => a.stats && a.stats.n > 0).map((a) => [Y.shortLabel ? Y.shortLabel(a.label) : a.label, a.stats.pnl_pct, a.stats.n]);
    const b = document.createElement("div");
    b.className = "card fx-panel fx-bars";
    const W = 330, H = 300, top = 28, bot = 52, mx = Math.max(1, ...rows.map((r) => Math.abs(r[1])));
    const hasNeg = rows.some((r) => r[1] < 0), zero = hasNeg ? top + (H - top - bot) * 0.62 : H - bot, up = zero - top, dn = H - bot - zero + 0;
    const slot = W / Math.max(1, rows.length), bw = Math.min(34, slot * 0.58);
    b.innerHTML = `<div class="card-head"><h3>Résultat par actif</h3><span class="faint">% cumulé</span></div><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Résultat cumulé par actif">
      <defs><pattern id="st-up" width="4" height="6" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="var(--brand)"/></pattern>
      <pattern id="st-dn" width="4" height="6" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="var(--dn)"/></pattern></defs>
      ${[0, .25, .5, .75, 1].map((k) => `<line x1="0" x2="${W}" y1="${top + (H - top - bot) * k}" y2="${top + (H - top - bot) * k}" stroke="var(--grid)"/>`).join("")}
      ${rows.map((r, i) => `<line x1="${slot * (i + .5)}" x2="${slot * (i + .5)}" y1="${top}" y2="${H - bot}" stroke="var(--grid)"/>`).join("")}
      <line x1="0" x2="${W}" y1="${zero}" y2="${zero}" stroke="var(--c-axis)"/>
      ${rows.map(([lab, val, n], i) => { const x = slot * (i + .5) - bw / 2, h = Math.abs(val) / mx * (val >= 0 ? up : Math.max(dn, 30)), y = val >= 0 ? zero - h : zero;
        return `<rect x="${x}" y="${y}" width="${bw}" height="${Math.max(2, h)}" fill="url(#${val >= 0 ? "st-up" : "st-dn"})"${val >= 0 ? ' style="filter:drop-shadow(0 0 4px rgba(127,243,200,.45))"' : ""}/>
          <text class="val ${val < 0 ? "dn" : ""}" x="${x + bw / 2}" y="${val >= 0 ? y - 6 : y + h + 14}" text-anchor="middle">${Y.signed(val, 1)}</text>
          <text x="${x + bw / 2}" y="${H - bot + 18}" text-anchor="middle">${lab.split(" ")[0].slice(0, 9)}</text>
          <text x="${x + bw / 2}" y="${H - bot + 32}" text-anchor="middle" opacity=".6">${n} tr.</text>`; }).join("")}</svg>`;
    wrap.appendChild(b);
  }
  Y.getJson("dashboard.json").then((d) => { if (d && d.overview) build(d); }).catch(() => {});
})();
