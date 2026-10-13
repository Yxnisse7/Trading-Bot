/* Lecture de la structure du marché à partir des bougies publiées par le bot (docs/live/<actif>.json).
 *
 * Tout est calculé dans le navigateur, sur les 24 h de bougies 5 min (ou leur regroupement en 15 min
 * et 1 h) : rien n'est ajouté aux fichiers du bot. Utilisé par les pages Graphique et Événements.
 *
 *   Struct.resample(bougies5m, secondes) → bougies { t, o, h, l, c }
 *   Struct.analyze(bougies, actif)       → { swings, sweeps, fvgs, sessions, rounds, ma20, ma50, hi, lo }
 *   Struct.events(analyse, actif)        → liste d'événements datés, du plus ancien au plus récent
 *
 * Vocabulaire (en français simple) :
 *   sommet / creux     un point haut ou bas dépassant les 3 bougies de chaque côté (là où dorment des stops) ;
 *   chasse aux stops   une mèche passe au-delà d'un sommet ou d'un creux, mais la bougie clôture en deçà ;
 *   trou (FVG)         trois bougies où la 1re et la 3e ne se touchent pas : zone que le prix revient souvent combler ;
 *   sessions           Asie 00:00-07:00, Londres 07:00-13:30, New York 13:30-20:00 (heures UTC).
 */
(function () {
  "use strict";
  const PIVOT = 3;
  const SESSIONS = [["asie", "Asie", 0, 420], ["londres", "Londres", 420, 810], ["ny", "New York", 810, 1200]];   // minutes UTC
  const ROUND = { gold: 10, nasdaq: 100, sp500: 25, bitcoin: 1000, ethereum: 50, oil: 1, euro: 0.005 };

  function resample(rows, sec) {
    const out = [];
    for (const r of rows || []) {
      const [t, o, h, l, c] = r, k = Math.floor(t / sec) * sec, last = out[out.length - 1];
      if (last && last.t === k) { last.h = Math.max(last.h, h); last.l = Math.min(last.l, l); last.c = c; }
      else out.push({ t: k, o, h, l, c });
    }
    return out;
  }

  function sma(c, n) {
    const out = []; let s = 0;
    for (let i = 0; i < c.length; i++) {
      s += c[i].c; if (i >= n) s -= c[i - n].c;
      if (i >= n - 1) out.push({ time: c[i].t, value: s / n });
    }
    return out;
  }

  // Sommets et creux, puis la première bougie qui les « chasse » (mèche au-delà, clôture en deçà)
  // ou qui les casse franchement (clôture au-delà) ; un niveau touché n'est plus actif.
  function swingsAndSweeps(c) {
    const swings = [], sweeps = [];
    for (let i = PIVOT; i < c.length - PIVOT; i++) {
      let hi = true, lo = true;
      for (let k = 1; k <= PIVOT; k++) {
        if (!(c[i].h > c[i - k].h && c[i].h >= c[i + k].h)) hi = false;
        if (!(c[i].l < c[i - k].l && c[i].l <= c[i + k].l)) lo = false;
      }
      if (hi) swings.push({ kind: "high", t: c[i].t, i, price: c[i].h, end: null, how: null });
      if (lo) swings.push({ kind: "low", t: c[i].t, i, price: c[i].l, end: null, how: null });
    }
    for (const s of swings) {
      for (let j = s.i + PIVOT + 1; j < c.length; j++) {
        const b = c[j];
        if (s.kind === "high" && b.h > s.price) {
          s.end = b.t; s.how = b.c < s.price ? "sweep" : "break";
          if (s.how === "sweep") sweeps.push({ t: b.t, dir: "short", price: s.price, wick: b.h, from: s.t });
          break;
        }
        if (s.kind === "low" && b.l < s.price) {
          s.end = b.t; s.how = b.c > s.price ? "sweep" : "break";
          if (s.how === "sweep") sweeps.push({ t: b.t, dir: "long", price: s.price, wick: b.l, from: s.t });
          break;
        }
      }
    }
    sweeps.sort((a, b) => a.t - b.t);
    return { swings, sweeps };
  }

  // Trous de prix (FVG) d'au moins un quart de la taille moyenne des bougies, et le moment où ils sont comblés.
  function fairValueGaps(c) {
    const out = [];
    if (c.length < 3) return out;
    const avg = c.reduce((s, b) => s + (b.h - b.l), 0) / c.length, min = avg * 0.25;
    for (let i = 1; i < c.length - 1; i++) {
      const a = c[i - 1], z = c[i + 1];
      let g = null;
      if (z.l - a.h > min) g = { dir: "long", top: z.l, bottom: a.h };
      else if (a.l - z.h > min) g = { dir: "short", top: a.l, bottom: z.h };
      if (!g) continue;
      g.t = c[i].t; g.end = null;
      for (let j = i + 2; j < c.length; j++) {
        if ((g.dir === "long" && c[j].l <= g.bottom) || (g.dir === "short" && c[j].h >= g.top)) { g.end = c[j].t; break; }
      }
      out.push(g);
    }
    return out;
  }

  function sessions(c) {
    const out = [];
    for (const b of c) {
      const day = Math.floor(b.t / 86400) * 86400, m = (b.t - day) / 60;
      const s = SESSIONS.find(([, , a, z]) => m >= a && m < z);
      if (!s) continue;
      const key = day + ":" + s[0];
      let cur = out[out.length - 1];
      if (!cur || cur.key !== key) {
        cur = { key, id: s[0], label: s[1], t: day + s[2] * 60, end: day + s[3] * 60, open: b.o, hi: b.h, lo: b.l, first: b.t, last: b.t };
        out.push(cur);
      }
      cur.hi = Math.max(cur.hi, b.h); cur.lo = Math.min(cur.lo, b.l); cur.last = b.t;
    }
    return out;
  }

  function rounds(c, asset) {
    if (!c.length) return [];
    const step = ROUND[asset] || Math.pow(10, Math.floor(Math.log10(c[c.length - 1].c)) - 1) * 5;
    const hi = Math.max(...c.map((b) => b.h)), lo = Math.min(...c.map((b) => b.l)), out = [];
    for (let p = Math.ceil(lo / step) * step; p <= hi + 1e-9; p += step) out.push(+p.toFixed(6));
    return out.length > 14 ? out.filter((_, i) => i % Math.ceil(out.length / 14) === 0) : out;
  }

  function analyze(c, asset) {
    const { swings, sweeps } = swingsAndSweeps(c);
    return {
      candles: c, swings, sweeps, fvgs: fairValueGaps(c), sessions: sessions(c), rounds: rounds(c, asset),
      ma20: sma(c, 20), ma50: sma(c, 50),
      hi: c.length ? Math.max(...c.map((b) => b.h)) : null, lo: c.length ? Math.min(...c.map((b) => b.l)) : null,
    };
  }

  function fmt(p) { return Math.abs(p) >= 100 ? p.toFixed(2) : p.toFixed(Math.abs(p) >= 1 ? 3 : 5); }

  // Événements à afficher dans la liste : chasses aux stops, cassures franches, trous de prix, sessions.
  function events(a) {
    const ev = [];
    for (const s of a.sweeps) ev.push({ t: s.t, type: "sweep", dir: s.dir, price: s.price,
      text: s.dir === "short" ? `Chasse aux stops au-dessus du sommet ${fmt(s.price)} (mèche à ${fmt(s.wick)}), clôture revenue dessous`
                              : `Chasse aux stops sous le creux ${fmt(s.price)} (mèche à ${fmt(s.wick)}), clôture revenue dessus` });
    for (const s of a.swings) if (s.how === "break") ev.push({ t: s.end, type: "break", dir: s.kind === "high" ? "long" : "short", price: s.price,
      text: s.kind === "high" ? `Cassure du sommet ${fmt(s.price)} (clôture au-dessus)` : `Cassure du creux ${fmt(s.price)} (clôture dessous)` });
    for (const g of a.fvgs) ev.push({ t: g.t, type: "fvg", dir: g.dir, price: (g.top + g.bottom) / 2,
      text: `Trou de prix ${g.dir === "long" ? "haussier" : "baissier"} ${fmt(g.bottom)} – ${fmt(g.top)}${g.end ? ", comblé ensuite" : ", pas encore comblé"}` });
    for (const s of a.sessions) if (s.first === s.t) ev.push({ t: s.t, type: "session", dir: null, price: s.open,
      text: `Ouverture ${s.label} à ${fmt(s.open)}` });
    return ev.sort((x, y) => x.t - y.t);
  }

  window.Struct = { resample, analyze, events, SESSIONS, fmt };
})();
