/* Résumé « HUD » de l'espace Investir : cinq indicateurs en haut de page, lus dans invest/data.json. */
(function () {
  const Y = window.YK;
  const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
  function build(d) {
    const anchor = document.querySelector(".wrap .principles");
    if (!anchor || document.querySelector(".fx-sum")) return;
    const prod = (k) => (d.products || []).find((p) => p.key === k);
    const monde = prod("monde"), st = monde && monde.stats ? monde.stats : null;
    const tone = (x) => (x >= 0 ? "" : "dn"), arrow = (x) => (x >= 0 ? "▲ " : "▼ ");
    const rev = d.revision || {}, nxt = rev.next ? rev.next.split("-") : null;
    const advTone = monde && monde.advice ? ({ up: "", dn: "dn" }[monde.advice.tag] || "") : "";
    const kpis = [
      st && st.r1 != null ? ["Monde islamique, 1 an", Y.signed(st.r1 * 100, 1) + " %", `${arrow(st.r1)}par an sur 3 ans : ${Y.signed((st.r3 || 0) * 100, 1)} %`, tone(st.r1)] : null,
      st ? ["Depuis le plus haut", st.dd_now ? Y.signed(st.dd_now * 100, 1) + " %" : "Au sommet", st.dd_now ? "▼ à rattraper" : "▲ record du fonds", st.dd_now ? "dn" : ""] : null,
      monde && monde.advice ? ["Avis du jour", monde.advice.label, "fonds Monde islamique", advTone] : null,
      d.metals && d.metals.gold_eur_g ? ["Or, le gramme", Y.num(d.metals.gold_eur_g, 1) + " €", `argent ${Y.num(d.metals.silver_eur_g, 2)} €`, ""] : null,
      nxt ? ["Prochaine révision", MOIS[+nxt[1] - 1], rev.now ? "c'est ce mois-ci" : "actions : rappel Telegram", rev.now ? "warn" : ""] : null,
    ].filter(Boolean);
    if (!kpis.length) return;
    const sum = document.createElement("div");
    sum.className = "card fx-sum";
    const when = d.updated_at ? new Date(d.updated_at).toLocaleDateString("fr-FR", { day: "numeric", month: "long" }) : "";
    sum.innerHTML = `<div class="card-head"><h3>Résumé</h3><span class="faint">données du ${Y.esc(when)}</span></div>
      <div class="fx-kpis">${kpis.map(([l, v, s, t]) => `<div class="fx-kpi"><small>${Y.esc(l)}</small><b class="${t}${v.length > 7 ? " txt" : ""}">${Y.esc(v)}</b><em class="${t}">${Y.esc(s)}</em></div>`).join("")}</div>`;
    anchor.before(sum);
  }
  Y.getJson("invest/data.json").then((d) => { if (d && d.products) build(d); }).catch(() => {});
})();
