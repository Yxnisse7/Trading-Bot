/* Outils communs aux pages du site (tableau de bord, simulation, apprentissage).
 *
 * - en-tête (logo, onglets, état du bot, thème) et navigation du bas sur téléphone ;
 * - format des nombres à la française (virgule, espace des milliers, vrai signe moins) ;
 * - libellés lisibles des critères, notifications, chiffres qui défilent ;
 * - lecture des données du tableau de bord (serveur local, GitHub Pages, API GitHub, claude.ai)
 *   et déclenchement du bot sur GitHub Actions.
 * Tout est exposé dans window.YK.
 */
(function () {
  "use strict";
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const MINUS = "−", NB = " ";
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* stockage indisponible */ } },
  };

  // ------------------------------------------------------------------ nombres
  function num(v, d = 2, opts = {}) {
    if (v === null || v === undefined || !Number.isFinite(Number(v))) return "n/a";
    const x = Number(v);
    const s = Math.abs(x).toLocaleString("fr-FR", { minimumFractionDigits: opts.min ?? d, maximumFractionDigits: d }).replace(/[\s ]/g, NB);
    return (x < 0 && Math.abs(x) >= Math.pow(10, -d) / 2 ? MINUS : "") + s;
  }
  const signed = (v, d = 2, suffix = "") => (v === null || v === undefined || !Number.isFinite(Number(v))) ? "n/a"
    : (Number(v) > 0 && Math.abs(v) >= Math.pow(10, -d) / 2 ? "+" : "") + num(v, d) + suffix;
  const pct = (ratio, d = 1) => (ratio === null || ratio === undefined) ? "n/a" : num(ratio * 100, d) + NB + "%";
  const pctv = (v, d = 2) => (v === null || v === undefined) ? "n/a" : signed(v, d, NB + "%");
  const money = (v, cur = "$", d = 2) => (v === null || v === undefined) ? "n/a" : num(v, d) + NB + cur;
  const smoney = (v, cur = "$", d = 2) => (v === null || v === undefined) ? "n/a" : signed(v, d, NB + cur);
  const decimals = (v) => { const s = String(v); return s.includes(".") ? s.split(".")[1].length : 0; };
  const price = (v, digits) => num(v, digits ?? Math.min(5, Math.max(2, decimals(v))), { min: digits ?? 2 });
  const tone = (v) => (v > 0 ? "up" : v < 0 ? "dn" : "neu");
  function ago(iso) {
    if (!iso) return "";
    const min = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
    if (min < 1) return "à l'instant";
    if (min < 60) return `il y a ${min} min`;
    if (min < 48 * 60) return `il y a ${Math.floor(min / 60)} h ${String(min % 60).padStart(2, "0")}`;
    return `il y a ${Math.floor(min / 1440)} jours`;
  }
  const hhmm = (d) => new Date(d).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  const ddmm = (d) => new Date(d).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });

  // ------------------------------------------------------------------ libellés
  const CRIT = {
    trend_5m: "Tendance 5 min", trend_15m: "Tendance 15 min", trend_1h: "Tendance 1 h", adx: "Tendance forte",
    macd: "MACD", rsi: "RSI", vwap: "VWAP", orb: "Cassure d'ouverture", pdhl: "Niveaux de la veille",
    level: "Niveau clé", corr: "Corrélation", volume: "Volume anormal",
  };
  const SRC = { bot: "Bot", manual: "Manuel", request: "Proposition", shadow: "Ombre", backtest: "Backtest" };
  const RES = { tp: "TP", sl: "SL", expired: "Expiré", open: "En cours" };
  const shortLabel = (l) => String(l || "").replace(/ \(.*\)$/, "");
  function critTags(list, max = 2) {
    const c = list || [];
    const trend = ["trend_5m", "trend_15m", "trend_1h"].filter((k) => c.includes(k));
    const labels = [];
    if (trend.length) labels.push("Tendance " + trend.map((k) => ({ trend_5m: "5 min", trend_15m: "15 min", trend_1h: "1 h" }[k])).join(" · "));
    for (const k of c) if (!k.startsWith("trend_")) labels.push(CRIT[k] || k);
    const shown = labels.slice(0, max).map((l) => `<span class="tag">${esc(l)}</span>`).join("");
    const rest = labels.length - max;
    return `<span class="tags" title="${esc(labels.join(", "))}">${shown}${rest > 0 ? `<span class="tag more">+${rest}</span>` : ""}</span>`;
  }
  const resultPill = (status, pnl) => `<span class="pill ${esc(status)}"><b>${RES[status] || esc(status)}</b>${pnl === null || pnl === undefined ? "" : " " + pctv(pnl, 2)}</span>`;
  const dirHtml = (d) => d === "long" ? `<span class="dir"><b class="up">↗</b>Achat</span>` : `<span class="dir"><b class="dn">↘</b>Vente</span>`;

  // ------------------------------------------------------------------ icônes
  const I = {
    logo: (s = 32) => `<svg width="${s}" height="${s}" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="var(--brand)"/><path d="M10.5 9 L16 16.5 L21.5 9 M16 16.5 V23.5" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M7.5 25.5 L25 7" stroke="#fff" stroke-opacity=".4" stroke-width="1.3" stroke-linecap="round"/></svg>`,
    moon: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M13.5 9.6A5.6 5.6 0 0 1 6.4 2.5a5.6 5.6 0 1 0 7.1 7.1z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>`,
    sun: `<svg width="16" height="16" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="3.4" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M9 1.5v1.8M9 14.7v1.8M1.5 9h1.8M14.7 9h1.8M3.7 3.7l1.3 1.3M13 13l1.3 1.3M3.7 14.3L5 13M13 5l1.3-1.3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`,
    plus: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`,
    info: `<svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.3" fill="none" stroke="currentColor" stroke-width="1.3"/><path d="M8 7.3v3.9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="5" r=".9" fill="currentColor"/></svg>`,
    fold: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 2.5l3 3 3-3M5 13.5l3-3 3 3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    refresh: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M13 8a5 5 0 1 1-1.5-3.6M13 2.5v3h-3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    chevR: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5l4.5 4.5L6 12.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    chevD: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    x: `<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M4.5 4.5l9 9M13.5 4.5l-9 9" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>`,
    warn: `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.2L14.5 13.5h-13z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/><path d="M8 6.5v3.2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="11.6" r=".85" fill="currentColor"/></svg>`,
    bell: `<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><path d="M4.5 12.5V8a4.5 4.5 0 0 1 9 0v4.5l1.2 1.5H3.3z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><path d="M7.3 15.5a1.8 1.8 0 0 0 3.4 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>`,
    home: `<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><g fill="none" stroke="currentColor" stroke-width="1.7"><rect x="3" y="3" width="6.5" height="8" rx="1.8"/><rect x="12.5" y="3" width="6.5" height="5" rx="1.8"/><rect x="3" y="14" width="6.5" height="5" rx="1.8"/><rect x="12.5" y="11" width="6.5" height="8" rx="1.8"/></g></svg>`,
    wallet: `<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><path d="M3 7.5A2.5 2.5 0 0 1 5.5 5h11A2.5 2.5 0 0 1 19 7.5v8a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 3 15.5z" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M14 11.5h2.5" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>`,
    learn: `<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><path d="M3 17l5-6 4 3.5L19 5M14.5 5H19v4.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    crescent: `<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><path d="M17.5 13.6A7 7 0 0 1 8.4 4.5a7 7 0 1 0 9.1 9.1z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>`,
    plusBig: `<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><path d="M11 4.5v13M4.5 11h13" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>`,
  };

  // ------------------------------------------------------------------ en-tête, onglets, navigation du bas
  const PAGES = [["dashboard", "index.html", "Tableau de bord", "Tableau", "home"], ["simulation", "portfolio.html", "Simulation", "Simulation", "wallet"],
                 ["learning", "apprentissage.html", "Apprentissage", "Apprendre", "learn"], ["halal", "halal.html", "Halal", "Halal", "crescent"]];
  function header(page) {
    const host = document.getElementById("yk-header");
    if (!host) return;
    const onDash = page === "dashboard";
    const trade = page === "halal" ? "" : onDash ? `<button type="button" id="btn-trade">${I.plus}<span class="btn-lbl">Nouveau trade</span></button>`
                         : `<a class="btn" id="btn-trade" href="index.html#trade">${I.plus}<span class="btn-lbl">Nouveau trade</span></a>`;
    host.className = "yk-top";
    host.innerHTML = `<div class="yk-top-in">
      <div class="yk-left">
        <a class="yk-brand" href="index.html" aria-label="Yasuke, tableau de bord">${I.logo(32)}<span><b>Yasuke</b><small>Trading-Bot</small></span></a>
        <nav class="yk-tabs" aria-label="Pages">${PAGES.map(([k, href, l]) => `<a class="yk-tab${k === page ? " active" : ""}" href="${href}"${k === page ? ' aria-current="page"' : ""}>${l}</a>`).join("")}</nav>
      </div>
      <div class="yk-right">
        <span class="yk-status" id="yk-status" role="status"><span class="dot"></span><b>Chargement</b><span class="yk-st-sub"></span></span>
        <button type="button" class="btn-icon" id="btn-theme" aria-label="Changer de thème" title="Thème clair ou sombre"></button>
        ${trade}
      </div></div>`;
    const nav = document.createElement("nav");
    nav.className = "yk-bnav"; nav.setAttribute("aria-label", "Navigation");
    const item = ([k, href, , short, ic]) => `<a href="${href}" class="${k === page ? "active" : ""}"${k === page ? ' aria-current="page"' : ""}>${I[ic]}<span>${short}</span></a>`;
    nav.innerHTML = item(PAGES[0]) + item(PAGES[1]) +
      (onDash ? `<button type="button" class="plus" id="bnav-trade"><span class="pb">${I.plusBig}</span><span>Trade</span></button>`
              : `<a class="plus" href="index.html#trade"><span class="pb">${I.plusBig}</span><span>Trade</span></a>`) + item(PAGES[2]) + item(PAGES[3]);
    document.body.appendChild(nav);
    themeButton();
  }

  // ------------------------------------------------------------------ thème
  function applyStoredTheme() { const t = store.get("tb-theme"); if (t) document.documentElement.dataset.theme = t; }
  function isDark() {
    const t = document.documentElement.dataset.theme;
    return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function themeButton() {
    const b = document.getElementById("btn-theme"); if (!b) return;
    const paint = () => { b.innerHTML = isDark() ? I.sun : I.moon; };
    paint();
    b.addEventListener("click", () => {
      const root = document.documentElement;
      root.classList.add("theme-fade");
      const next = isDark() ? "light" : "dark";
      root.dataset.theme = next; store.set("tb-theme", next); paint();
      setTimeout(() => root.classList.remove("theme-fade"), 320);
      document.dispatchEvent(new CustomEvent("yk:theme"));
    });
    try { matchMedia("(prefers-color-scheme: dark)").addEventListener("change", paint); } catch (e) { /* ancien navigateur */ }
  }

  // ------------------------------------------------------------------ état du bot
  function status(lastIso, note) {
    const el = document.getElementById("yk-status"); if (!el) return;
    const b = el.querySelector("b"), sub = el.querySelector(".yk-st-sub");
    if (!lastIso) { el.className = "yk-status"; b.textContent = "Bot inconnu"; sub.textContent = "aucun passage enregistré"; return; }
    const min = Math.max(0, Math.round((Date.now() - new Date(lastIso).getTime()) / 60000));
    const late = min > 15;
    el.className = "yk-status " + (late ? "late" : "ok");
    b.textContent = late ? "Bot en retard" : "Bot actif";
    sub.textContent = (late ? `aucun passage depuis ${min < 120 ? min + " min" : Math.round(min / 60) + " h"}` : `dernier passage ${ago(lastIso)}`)
      + (S.direct ? " · direct" : "");
    el.title = (late ? "Le bot tourne normalement toutes les 5 minutes. " : "") + (note ? "Dernier passage : " + note + ". " : "")
      + (S.direct ? "Données lues directement sur GitHub (jeton de ce navigateur) : environ 1 min après Telegram." : "Données publiées par GitHub Pages : 3 à 5 min après Telegram.");
  }

  // ------------------------------------------------------------------ notifications
  function toast({ title, text, meta, actions = [], timeout = 12000 }) {
    let box = $(".yk-toasts");
    if (!box) { box = document.createElement("div"); box.className = "yk-toasts"; box.setAttribute("aria-live", "polite"); document.body.appendChild(box); }
    const t = document.createElement("div"); t.className = "yk-toast";
    t.innerHTML = `<div class="ic">${I.bell}</div><div><div><b>${esc(title)}</b> <span class="faint">à l'instant</span></div>
      ${text ? `<div class="t">${esc(text)}</div>` : ""}${meta ? `<div class="m mono">${esc(meta)}</div>` : ""}<div class="acts"></div></div>`;
    const acts = t.querySelector(".acts");
    const close = () => { t.classList.add("out"); setTimeout(() => t.remove(), 260); };
    for (const [label, fn] of actions) { const a = document.createElement("button"); a.type = "button"; a.textContent = label; if (fn) a.style.color = "var(--brand-text)"; a.addEventListener("click", () => { if (fn) fn(); close(); }); acts.appendChild(a); }
    if (!actions.length) acts.remove();
    box.appendChild(t);
    if (timeout) setTimeout(close, timeout);
    return close;
  }

  // ------------------------------------------------------------------ chiffres qui défilent
  const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  function countTo(el, value, format) {
    if (!el) return;
    const prev = el.dataset.v === undefined ? null : Number(el.dataset.v);
    el.dataset.v = String(value);
    if (prev === null || prev === value || reduced() || !Number.isFinite(value) || !Number.isFinite(prev)) { el.textContent = format(value); return; }
    const t0 = performance.now(), dur = 320;
    const step = (t) => {
      const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      el.textContent = format(prev + (value - prev) * e);
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // mini-courbe SVG (tuiles)
  function spark(vals, endColor) {
    if (!vals || vals.length < 2) return "";
    const W = 280, H = 44, mn = Math.min(...vals), mx = Math.max(...vals), sp = (mx - mn) || 1;
    const X = (i) => 2 + i * (W - 6) / (vals.length - 1), Y = (v) => H - 4 - (v - mn) / sp * (H - 8);
    const d = vals.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join(" ");
    const lx = X(vals.length - 1), ly = Y(vals[vals.length - 1]);
    return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><path d="${d}" fill="none" stroke="var(--text)" stroke-width="1.75" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/><circle cx="${lx}" cy="${ly}" r="3.5" fill="${endColor}" stroke="var(--card)" stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>`;
  }

  // ------------------------------------------------------------------ GitHub : jeton du navigateur
  const GH_DEFAULT = { owner: "Yxnisse7", repo: "Trading-Bot" };
  function ghSettings() {
    const owner = (store.get("tb-gh-owner") || "").trim(), repo = (store.get("tb-gh-repo") || "").trim(), token = (store.get("tb-gh-token") || "").trim();
    return owner && repo && token ? { owner, repo, token } : null;
  }
  // Lecture directe sur GitHub (navigateur avec jeton enregistré) : les fichiers publiés par le bot sont lus
  // dans le dépôt dès leur enregistrement, sans attendre la mise en ligne de GitHub Pages (≈ 3 min).
  // Sans jeton, ou si GitHub refuse (jeton expiré, quota), les fichiers de GitHub Pages prennent le relais.
  let directOff = 0;
  async function ghRaw(path) {
    const gh = ghSettings();
    if (!gh || Date.now() < directOff) return null;
    try {
      const r = await fetch(`https://api.github.com/repos/${gh.owner}/${gh.repo}/contents/docs/${path}?ref=main`,
        { headers: { Authorization: "Bearer " + gh.token, Accept: "application/vnd.github.raw+json" }, cache: "no-store" });
      if (r.ok) { S.direct = true; return await r.json(); }
      if (r.status === 401 || r.status === 403 || r.status === 429) { directOff = Date.now() + 10 * 60000; S.direct = false; }
    } catch (e) { /* réseau : GitHub Pages prend le relais */ }
    return null;
  }
  // Fichier publié (chemin relatif à docs/) : lecture directe si possible, sinon GitHub Pages, sinon data/ (fichier local)
  async function getJson(path) {
    const d = await ghRaw(path);
    if (d) return d;
    for (const u of [path, `../data/${path}`]) {
      try { const r = await fetch(u + "?t=" + Date.now(), { cache: "no-store" }); if (r.ok) return await r.json(); } catch (e) { /* suivant */ }
    }
    return null;
  }
  // Rafraîchissement : toutes les minutes en lecture directe, toutes les 2 min sur GitHub Pages
  function poll(fn) { let n = 0; setInterval(() => { n++; if (S.direct || n % 2 === 0) fn(); }, 60000); }
  function ghRepo() { const s = ghSettings(); return { owner: (s && s.owner) || GH_DEFAULT.owner, repo: (s && s.repo) || GH_DEFAULT.repo }; }
  // Branche le bloc « Mode GitHub Actions » (champs gh-owner, gh-repo, gh-token, boutons gh-save, gh-test, texte gh-status)
  function bindGhSettings(onSaved) {
    const fields = ["owner", "repo", "token"];
    fields.forEach((k) => { const v = store.get("tb-gh-" + k); const i = document.getElementById("gh-" + k); if (v && i) i.value = v; });
    const st = () => {
      const el = document.getElementById("gh-status"); if (!el) return;
      const gh = ghSettings();
      el.textContent = gh ? `Jeton GitHub enregistré dans ce navigateur pour ${gh.owner}/${gh.repo}.` : "Aucun jeton GitHub enregistré dans ce navigateur : les boutons ne peuvent pas déclencher le bot tant qu'il n'est pas renseigné puis enregistré.";
    };
    st();
    const save = document.getElementById("gh-save"), test = document.getElementById("gh-test");
    if (save) save.addEventListener("click", () => {
      fields.forEach((k) => store.set("tb-gh-" + k, document.getElementById("gh-" + k).value.trim()));
      st(); if (onSaved) onSaved();
    });
    if (test) test.addEventListener("click", async () => {
      const el = document.getElementById("gh-status"), gh = ghSettings();
      if (!gh) { el.textContent = "Enregistrez d'abord le jeton."; return; }
      el.textContent = "Test en cours…";
      try {
        const r = await fetch(`https://api.github.com/repos/${gh.owner}/${gh.repo}/actions/workflows`, { headers: { "Authorization": "Bearer " + gh.token, "Accept": "application/vnd.github+json" } });
        if (r.status === 200) { const j = await r.json(); el.textContent = `Jeton valide : ${j.total_count} workflow(s) visibles. Vous pouvez utiliser les boutons.`; }
        else if (r.status === 401) el.textContent = "Jeton refusé (401) : il est invalide ou expiré. Générez-en un nouveau (fine-grained, dépôt Trading-Bot, Actions : Read and write).";
        else if (r.status === 403 || r.status === 404) el.textContent = `Accès refusé (${r.status}) : le jeton n'a pas la permission Actions sur ce dépôt, ou le dépôt est mal orthographié.`;
        else el.textContent = `Réponse inattendue de GitHub (${r.status}).`;
      } catch (e) { el.textContent = "Impossible de joindre GitHub : " + e.message; }
    });
  }

  // ------------------------------------------------------------------ données du tableau de bord
  // Quatre sources, dans l'ordre : claude.ai (connecteur GitHub du lecteur), serveur local
  // (`python run.py ui`), fichiers publiés (GitHub Pages), API GitHub avec le jeton du navigateur.
  const MCP_FIX = {
    needs_reauth: "Reconnectez GitHub dans claude.ai, Paramètres, Connecteurs, puis actualisez.",
    server_not_connected: "Ajoutez le connecteur GitHub dans claude.ai, Paramètres, Connecteurs, puis actualisez.",
    selection_required: "Plusieurs connecteurs GitHub : choisissez-en un dans l'invite de claude.ai, puis actualisez.",
    not_in_manifest: "Accès GitHub refusé pour cette page : autorisez-le quand claude.ai le demande.",
    consent_required: "Autorisez l'accès GitHub quand claude.ai le demande, puis réessayez.",
    blocked_by_policy: "L'accès GitHub est bloqué par la politique de votre organisation.",
    approval_required: "Cette action GitHub demande une approbation qui n'est pas disponible ici.",
  };
  const S = { mode: "static", mcp: null, mcpChecked: false, watching: false, consentAsked: false };
  function extractDashboard(result) {
    const cands = [];
    if (result && result.payload !== undefined) cands.push(result.payload);
    for (const b of (result && result.content) || []) {
      if (typeof b.text === "string") cands.push(b.text);
      if (b.resource && typeof b.resource.text === "string") cands.push(b.resource.text);
    }
    for (const c of cands) {
      if (c && typeof c === "object" && c.overview) return c;
      if (typeof c === "string") { const i = c.indexOf("{"); if (i >= 0) { try { const j = JSON.parse(c.slice(i)); if (j && j.overview) return j; } catch (e) { /* bloc suivant */ } } }
    }
    return null;
  }
  async function ensureConsent() {
    if (S.consentAsked) return "asked";
    S.consentAsked = true;
    try {
      const perms = window.claude && typeof window.claude.use === "function" ? await window.claude.use("permissions") : null;
      if (!perms) return "unknown";
      const before = await perms.state("mcp:github").catch(() => "unavailable");
      if (before === "granted") return "granted";
      const after = await perms.request(["mcp:github"]).catch(() => ({}));
      return after["mcp:github"] || before;
    } catch (e) { return "unknown"; }
  }
  function mcpErrorText(err) {
    const code = err && err.code;
    if (MCP_FIX[code]) return MCP_FIX[code];
    if (code === "tool_error") return "GitHub a refusé la demande : " + (err.message || "");
    return "GitHub n'a pas répondu (" + (code || "erreur") + (err && err.message ? " : " + err.message : "") + "). Réessayez dans un instant.";
  }
  async function initMcp(say) {
    if (S.mcp) return S.mcp;
    if (S.mcpChecked) return null;
    S.mcpChecked = true;
    if (!(window.claude && typeof window.claude.use === "function")) return null;
    try { S.mcp = await window.claude.use("mcp"); } catch (e) { S.mcp = null; }
    if (!S.mcp) {
      let state = "inconnu";
      try { const perms = await window.claude.use("permissions"); if (perms) state = await perms.state("mcp:github"); } catch (e) { /* diagnostic seulement */ }
      say("Connecteur GitHub indisponible dans cette vue (état : " + state + "). Ouvrez la page dans claude.ai sur navigateur, vérifiez que GitHub est bien connecté (Paramètres, Connecteurs), puis rechargez.");
    }
    return S.mcp;
  }
  // loadDashboard({ onData(data, mode), say(text) }) : relit les données ; en mode claude.ai, les mises à jour arrivent seules.
  async function loadDashboard({ onData, say, onNoData }) {
    if (await initMcp(say)) {
      if (S.watching) { try { await S.mcp.invalidate("github", "get_file_contents"); } catch (e) { /* rien en cache */ } return S.mode; }
      S.watching = true;
      await ensureConsent();
      const { owner, repo } = ghRepo();
      S.mcp.watchTool("github", "get_file_contents", { owner, repo, path: "data/dashboard.json", ref: "refs/heads/main" }, (ev) => {
        if (ev.type === "data") {
          const d = extractDashboard(ev.result);
          if (d) { S.mode = "mcp"; onData(d, "mcp"); }
          else say("Réponse GitHub inattendue : le fichier data/dashboard.json est-il présent ?");
          return;
        }
        const code = ev.error && ev.error.code;
        say(MCP_FIX[code] || ("GitHub ne répond pas pour le moment (" + (code || "erreur") + "). Cliquez sur Actualiser pour réessayer."));
      }, { cache: { staleTime: 60000 }, refetchInterval: 300000 });
      return "mcp";
    }
    if (window.claude) return "static";   // vue claude.ai sans connecteur : message déjà affiché
    try { const ping = await fetch("/api/ping", { cache: "no-store" }); S.mode = ping.ok ? "local" : "static"; } catch (e) { S.mode = "static"; }
    let data = null;
    if (S.mode === "local") {
      try { const r = await fetch("/api/state", { cache: "no-store" }); if (r.ok) data = await r.json(); } catch (e) { /* rien */ }
    } else {
      data = await ghRaw("dashboard.json");
      if (data) S.mode = "github";
      else data = await getJson("dashboard.json");
    }
    if (!data) { if (onNoData) onNoData(); return S.mode; }
    onData(data, S.mode);
    return S.mode;
  }
  // Déclenche le workflow du bot (commande manual, propose, portfolio…)
  async function dispatch(inputs, { retryOnce = false, workflow = "bot.yml" } = {}) {
    if (S.mcp) {
      const consent = await ensureConsent();
      if (consent === "denied") throw new Error("Accès GitHub refusé pour cette page. Rechargez la page et acceptez l'invite d'autorisation de claude.ai.");
      const { owner, repo } = ghRepo();
      const call = () => S.mcp.callTool("github", "actions_run_trigger", { method: "run_workflow", owner, repo, workflow_id: workflow, ref: "main", inputs });
      try { await call(); }
      catch (err) {
        if (retryOnce && err && err.retryable) {
          await new Promise((r) => setTimeout(r, Math.min(err.retryAfterMs || 3000, 10000)));
          try { await call(); return; } catch (err2) { throw new Error(mcpErrorText(err2)); }
        }
        throw new Error(mcpErrorText(err));
      }
      return;
    }
    const gh = ghSettings();
    if (!gh) throw new Error("Aucun jeton GitHub enregistré dans ce navigateur : dépliez « Mode GitHub Actions », collez votre jeton, cliquez « Enregistrer », puis réessayez.");
    const r = await fetch(`https://api.github.com/repos/${gh.owner}/${gh.repo}/actions/workflows/${workflow}/dispatches`, {
      method: "POST", headers: { "Authorization": "Bearer " + gh.token, "Accept": "application/vnd.github+json", "Content-Type": "application/json" },
      body: JSON.stringify({ ref: "main", inputs }),
    });
    if (r.status === 401) throw new Error("GitHub a refusé le jeton (401) : il est invalide ou expiré.");
    if (r.status === 403 || r.status === 404) throw new Error(`GitHub a refusé la demande (${r.status}) : le jeton n'a pas la permission « Actions : Read and write » sur ce dépôt.`);
    if (r.status !== 204) throw new Error(`GitHub a répondu ${r.status} : vérifiez le jeton et le dépôt.`);
  }
  // ------------------------------------------------------------------ positions ouvertes : estimation et arrêt
  // Taux EUR/USD : dernier cours du contrat euro/dollar suivi par le bot (docs/live/euro.json), mis en cache 1 min
  let eurCache = null;
  async function eurRate() {
    if (eurCache && Date.now() - eurCache.t < 60000) return eurCache.v;
    const d = await getJson("live/euro.json");
    const v = d && Number(d.last) > 0.5 && Number(d.last) < 2 ? Number(d.last) : null;
    eurCache = { t: Date.now(), v };
    return v;
  }
  // Résultat d'une position simulée au prix `last` (mêmes règles que la simulation : coûts et frais d'ordre déduits)
  function estimate(pos, asset, last) {
    if (!pos || last == null || !pos.lots) return null;
    const sign = pos.direction === "long" ? 1 : -1, mult = Number((asset && asset.lot_multiplier) || 1);
    const gross = sign * (last - pos.entry) * mult * pos.lots;
    const cost = (Number(asset && asset.cost_pct) || 0) / 100 * Number(pos.notional || 0) + 2 * (Number(asset && asset.fee_per_order) || 0);
    return { gross, net: gross - cost, pct: sign * (last / pos.entry - 1) * 100 };
  }
  // « +8,20 € » (converti depuis les dollars de la simulation), ou en dollars sans taux de change
  const eur = (usd, rate, d = 2) => rate ? smoney(usd / rate, "€", d) : smoney(usd, "$", d);
  // Cellule « Estimation » : remplie après coup (dernier prix du graphique live, taux de change, position simulée)
  async function fillEstimates(root, { positions = {}, assets = [], base = "" } = {}) {
    const cells = [...root.querySelectorAll("[data-est]")];
    if (!cells.length) return;
    const rate = await eurRate();
    for (const el of cells) {
      const id = el.dataset.est, key = el.dataset.asset, pos = positions[id];
      const snap = window.LiveChart ? await window.LiveChart.snapshot(key, 55000, base) : null;
      const last = snap && Number(snap.last);
      if (!snap || !Number.isFinite(last)) { el.innerHTML = `<span class="faint">n/a</span>`; continue; }
      const when = snap.candles && snap.candles.length ? hhmm(snap.candles[snap.candles.length - 1][0] * 1000 + 300000) : "";
      const e = estimate(pos, assets.find((a) => a.key === key), last);
      if (e) {
        el.innerHTML = `<b class="${tone(e.net)}">${eur(e.net, rate)}</b> <span class="muted" style="font-size:12px">${pctv(e.pct, 2)}</span>`;
        el.title = `Au dernier prix connu (${fmtNum(last)}, clôture ${when}), frais estimés déduits${rate ? ` · ${smoney(e.net, "$")} au taux ${num(rate, 4)} $ pour 1 €` : ""}.`;
      } else {
        const dir = el.dataset.dir === "short" ? -1 : 1, entry = Number(el.dataset.entry);
        el.innerHTML = `<span class="${tone(dir * (last - entry))}">${pctv(dir * (last / entry - 1) * 100, 2)}</span>`;
        el.title = "Pas de position simulée pour ce signal : variation depuis l'entrée seulement.";
      }
    }
  }
  const fmtNum = (v) => num(v, Math.min(5, Math.max(2, decimals(v))));
  // Arrêt manuel : serveur local, ou workflow GitHub (bot principal ou mode halal)
  async function stopTrade(id, { halal = false } = {}) {
    if (S.mode === "local" && !halal) {
      const r = await fetch("/api/stop", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok || !j.ok) throw new Error(j.error || "erreur");
      return "local";
    }
    await dispatch({ command: "stop", signal: id }, { workflow: halal ? "halal.yml" : "bot.yml" });
    return "github";
  }
  // Branche les boutons « Arrêter » d'un conteneur (délégation : survit aux re-rendus)
  function bindStopButtons(root, { halal = false, onDone } = {}) {
    root.addEventListener("click", async (ev) => {
      const b = ev.target.closest("[data-stop]"); if (!b) return;
      const label = b.dataset.label || "ce trade";
      if (!confirm(`Arrêter ${label} au prix du moment ?\n\nLa simulation encaisse la sortie maintenant. Le bot continue ensuite de suivre le trade en silence jusqu'au TP, au SL ou à l'expiration, pour apprendre de son vrai résultat.`)) return;
      b.disabled = true; b.textContent = "Envoi…";
      try {
        const how = await stopTrade(b.dataset.stop, { halal });
        toast({ title: "Arrêt demandé", text: how === "local" ? `${label} arrêté.` : `${label} sera arrêté au prix du moment dans 1 à 2 minutes.`,
                meta: "Confirmation sur Telegram, avec le résultat en euros.", timeout: 9000 });
        b.textContent = "Demandé";
        if (onDone) onDone();
      } catch (e) {
        b.disabled = false; b.textContent = "Arrêter";
        toast({ title: "Arrêt impossible", text: e.message, timeout: 12000 });
      }
    });
  }
  const modeText = (m) => ({ local: "serveur local", mcp: "connecté à GitHub via claude.ai", github: "lecture directe sur GitHub", static: "GitHub Pages" }[m] || m);

  applyStoredTheme();
  // l'en-tête est dessiné tout de suite (le script est chargé en fin de page), avant sections.js
  if (document.getElementById("yk-header")) header(document.body.dataset.page || "");
  window.YK = {
    $, esc, store, num, signed, pct, pctv, money, smoney, price, decimals, tone, ago, hhmm, ddmm, CRIT, SRC, RES, shortLabel,
    critTags, resultPill, dirHtml, I, header, isDark, status, toast, countTo, spark, ghSettings, bindGhSettings,
    loadDashboard, dispatch, modeText, state: S, MINUS, NB, ghRaw, getJson, poll,
    eurRate, estimate, eur, fillEstimates, stopTrade, bindStopButtons,
  };
})();
