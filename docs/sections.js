/* Sections repliables, partagées par le tableau de bord et la simulation de compte.
 *
 * Chaque titre de section (h2 placé directement dans .wrap) devient un bloc repliable qui contient
 * tout ce qui le suit jusqu'au titre suivant. L'état replié ou déplié de chaque section est mémorisé
 * dans le navigateur, page par page. Un bouton « Tout replier / Tout déplier » s'ajoute à l'en-tête.
 * Les éléments sont déplacés, jamais recréés : les identifiants et le code des pages restent valides.
 */
(function () {
  "use strict";
  const CSS = `
  details.sec { margin: 0; }
  details.sec > summary.sec-h { list-style: none; display: flex; align-items: center; gap: 10px; margin: 28px 0 10px;
    font-size: 17px; font-weight: 650; color: var(--text); cursor: pointer; user-select: none; border-radius: 6px; }
  details.sec > summary.sec-h::-webkit-details-marker { display: none; }
  details.sec > summary.sec-h::before { content: ""; flex: none; width: 7px; height: 7px; margin: 0 2px 3px 2px;
    border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted); transform: rotate(45deg); transition: transform .15s; }
  details.sec:not([open]) > summary.sec-h::before { transform: rotate(-45deg); margin-bottom: 0; }
  details.sec:not([open]) > summary.sec-h { margin-bottom: 0; color: var(--muted); }
  details.sec > summary.sec-h:hover { color: var(--accent); }
  details.sec > summary.sec-h:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
  details.sec > summary.sec-h .sec-hint { font-size: 12px; font-weight: 400; color: var(--muted); }
  details.sec[open] > summary.sec-h .sec-hint { display: none; }`;

  const page = (location.pathname.split("/").pop() || "index.html").replace(/\W/g, "_");
  const keyFor = (title) => `tb-section:${page}:${title}`;
  const read = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
  const write = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* stockage indisponible */ } };

  function init() {
    const wrap = document.querySelector(".wrap");
    if (!wrap || wrap.querySelector("details.sec")) return;
    const st = document.createElement("style");
    st.textContent = CSS;
    document.head.appendChild(st);

    const sections = [];
    for (const h of Array.from(wrap.children).filter((n) => n.tagName === "H2")) {
      const title = h.textContent.trim();
      const det = document.createElement("details");
      det.className = "sec";
      const sum = document.createElement("summary");
      sum.className = "sec-h";
      sum.append(...Array.from(h.childNodes));          // contenu statique du titre, déplacé tel quel
      const hint = document.createElement("span");
      hint.className = "sec-hint";
      hint.textContent = "replié, cliquez pour afficher";
      sum.appendChild(hint);
      det.appendChild(sum);
      let n = h.nextElementSibling;
      while (n && n.tagName !== "H2" && !n.classList.contains("disclaimer")) {
        const next = n.nextElementSibling;
        det.appendChild(n);
        n = next;
      }
      h.replaceWith(det);
      det.open = read(keyFor(title)) !== "0";
      det.addEventListener("toggle", () => {
        write(keyFor(title), det.open ? "1" : "0");
        // les graphiques se dessinent à la largeur disponible : on les redessine à l'ouverture
        if (det.open) window.dispatchEvent(new Event("resize"));
        updateButton();
      });
      sections.push(det);
    }
    if (!sections.length) return;

    // Bouton « Tout replier / Tout déplier » à côté des autres boutons de l'en-tête
    const anchor = document.getElementById("btn-theme");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "secondary";
    btn.id = "btn-sections";
    function updateButton() { btn.textContent = sections.some((d) => d.open) ? "Tout replier" : "Tout déplier"; }
    btn.addEventListener("click", () => {
      const open = !sections.some((d) => d.open);
      for (const d of sections) d.open = open;          // chaque « toggle » mémorise son état
    });
    updateButton();
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(btn, anchor);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
