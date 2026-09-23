/* Sections repliables, communes aux pages du site.
 *
 * Chaque titre de section (h2 placé directement dans .wrap) devient un bloc repliable qui contient
 * tout ce qui le suit jusqu'au titre suivant. L'état replié ou déplié est mémorisé dans le navigateur,
 * page par page ; un h2 portant data-closed est replié tant que rien n'est mémorisé. Le repli glisse
 * en 0,2 seconde (sauf si le système demande moins d'animations). Un bouton « Tout replier / Tout
 * déplier » s'ajoute à l'en-tête, juste avant le bouton du thème.
 * Les éléments sont déplacés, jamais recréés : les identifiants et le code des pages restent valides.
 */
(function () {
  "use strict";
  const STYLE = `
  details.sec { margin: 0; scroll-margin-top: 84px; }
  details.sec > summary.sec-h { list-style: none; display: flex; align-items: center; gap: 10px; margin: 36px 0 14px;
    font-size: 18px; font-weight: 600; letter-spacing: -0.01em; color: var(--text); cursor: pointer; user-select: none; border-radius: 8px; }
  details.sec > summary.sec-h::-webkit-details-marker { display: none; }
  details.sec > summary.sec-h .sec-chev { flex: none; display: grid; place-items: center; width: 22px; height: 22px; border-radius: 6px; color: var(--muted); transition: transform .2s ease; }
  details.sec:not([open]) > summary.sec-h .sec-chev { transform: rotate(-90deg); }
  details.sec:not([open]) > summary.sec-h { margin-bottom: 0; padding: 14px 16px; margin-top: 12px; background: var(--card); border: 1px solid var(--line); border-radius: 14px; font-size: 15px; }
  details.sec > summary.sec-h:hover .sec-chev { background: var(--soft); color: var(--text); }
  details.sec > summary.sec-h .sec-hint { font-size: 13px; font-weight: 400; color: var(--muted); letter-spacing: 0; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  details.sec[open] > summary.sec-h .sec-hint { display: none; }
  details.sec > .sec-body { overflow: visible; }
  details.sec > .sec-body.anim { overflow: hidden; }`;
  const CHEV = `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  const FOLD = `<svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M5 2.5l3 3 3-3M5 13.5l3-3 3 3" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

  const page = (location.pathname.split("/").pop() || "index.html").replace(/\W/g, "_");
  const keyFor = (title) => `tb-section:${page}:${title}`;
  const read = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const write = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* stockage indisponible */ } };
  const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

  function animate(det, body, open) {
    if (reduced() || !body.animate) { det.open = open; return; }
    body.classList.add("anim");
    if (open) {
      det.open = true;
      const h = body.scrollHeight;
      body.animate([{ height: "0px", opacity: 0 }, { height: h + "px", opacity: 1 }], { duration: 200, easing: "cubic-bezier(.2,.7,.2,1)" })
        .onfinish = () => body.classList.remove("anim");
    } else {
      const h = body.scrollHeight;
      body.animate([{ height: h + "px", opacity: 1 }, { height: "0px", opacity: 0 }], { duration: 180, easing: "ease-in" })
        .onfinish = () => { det.open = false; body.classList.remove("anim"); };
    }
  }

  function init() {
    const wrap = document.querySelector(".wrap");
    if (!wrap || wrap.querySelector("details.sec")) return;
    const st = document.createElement("style"); st.textContent = STYLE; document.head.appendChild(st);

    const sections = [];
    for (const h of Array.from(wrap.children).filter((n) => n.tagName === "H2")) {
      const title = h.textContent.trim();
      const det = document.createElement("details"); det.className = "sec";
      if (h.id) { det.id = h.id; h.removeAttribute("id"); }
      const sum = document.createElement("summary"); sum.className = "sec-h";
      const chev = document.createElement("span"); chev.className = "sec-chev"; chev.innerHTML = CHEV;
      const label = document.createElement("span"); label.append(...Array.from(h.childNodes));
      const hint = document.createElement("span"); hint.className = "sec-hint";
      hint.textContent = h.dataset.hint || "replié, cliquez pour afficher";
      sum.append(chev, label, hint);
      const body = document.createElement("div"); body.className = "sec-body";
      det.append(sum, body);
      let n = h.nextElementSibling;
      while (n && n.tagName !== "H2" && !n.classList.contains("foot")) { const next = n.nextElementSibling; body.appendChild(n); n = next; }
      const closedByDefault = h.hasAttribute("data-closed");
      h.replaceWith(det);
      const stored = read(keyFor(title));
      det.open = stored === null ? !closedByDefault : stored !== "0";
      sum.addEventListener("click", (ev) => { ev.preventDefault(); animate(det, body, !det.open); });
      det.addEventListener("toggle", () => {
        write(keyFor(title), det.open ? "1" : "0");
        // les graphiques se dessinent à la largeur disponible : on les redessine à l'ouverture
        if (det.open) window.dispatchEvent(new Event("resize"));
        updateButton();
      });
      det.setHint = (t) => { hint.textContent = t; };
      sections.push(det);
    }
    if (!sections.length) return;

    const anchor = document.getElementById("btn-theme");
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "secondary"; btn.id = "btn-sections";
    btn.innerHTML = FOLD + "<span></span>";
    function updateButton() {
      const any = sections.some((d) => d.open);
      btn.querySelector("span").textContent = any ? "Tout replier" : "Tout déplier";
      btn.title = any ? "Replier toutes les sections" : "Déplier toutes les sections";
    }
    btn.addEventListener("click", () => { const open = !sections.some((d) => d.open); for (const d of sections) d.open = open; });
    updateButton();
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(btn, anchor);
    // ouvrir la section visée par un lien (apprentissage.html#backtests…)
    const openTarget = () => { const t = location.hash && document.getElementById(location.hash.slice(1)); if (t && t.tagName === "DETAILS") { t.open = true; t.scrollIntoView({ block: "start" }); } };
    openTarget(); addEventListener("hashchange", openTarget);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
