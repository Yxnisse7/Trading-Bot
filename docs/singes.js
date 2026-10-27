/* Les singes traders (27/10/2026, idée de Yanisse) : chaque compte est un trader singe, clin d'œil aux
 * 1 000 singes de l'essai 21. Dessinés à la main en SVG (pas d'image externe) : un buste en costume, une
 * cravate et un accessoire par compte, 7 humeurs. Aucun effet sur les trades : ils montrent l'état du compte.
 *
 *   YK.singe("peur", { compte: "mt5", taille: 160 })  → chaîne SVG
 *   YK.SINGE_HUMEURS                                   → libellés et couleurs des humeurs
 */
(function () {
  const Y = (window.YK = window.YK || {});
  const FUR = "#7b4a2a", FUR_D = "#5e361d", SKIN = "#f1cba3", SKIN_D = "#d9a77c", INK = "#2a1a12";
  const COMPTES = {
    simulation: { cravate: "#8b7cf6", nom: "Simu", accessoire: "lunettes" },
    topstep: { cravate: "#f59e0b", nom: "Topper", accessoire: "casquette" },
    mt5: { cravate: "#14b8a6", nom: "Agent", accessoire: "casque" },
  };
  Y.SINGE_COMPTES = COMPTES;
  Y.SINGE_HUMEURS = {
    serein: { label: "Serein", couleur: "#22c55e", phrase: "Il suit son plan, tranquille." },
    confiant: { label: "Confiant", couleur: "#3b82f6", phrase: "Ça tourne bien, il garde la tête froide." },
    euphorique: { label: "Euphorique", couleur: "#eab308", phrase: "Série de gains : attention à l'excès de confiance." },
    frustre: { label: "Frustré", couleur: "#f97316", phrase: "Série de pertes : il serre les dents." },
    tilt: { label: "En tilt", couleur: "#ef4444", phrase: "Grosse journée rouge : danger de vouloir se refaire." },
    pause: { label: "En pause", couleur: "#94a3b8", phrase: "Il s'est arrêté (limite atteinte ou rien à faire)." },
    peur: { label: "Peur de son ombre", couleur: "#a855f7", phrase: "Ses trades en ombre font mieux que ses trades réels." },
  };

  let uid = 0;

  // ---------------------------------------------------------------- morceaux communs
  const tete = (id) => `
    <g class="tete">
      <circle cx="40" cy="98" r="20" fill="${FUR}"/><circle cx="40" cy="98" r="12" fill="${SKIN_D}"/>
      <circle cx="160" cy="98" r="20" fill="${FUR}"/><circle cx="160" cy="98" r="12" fill="${SKIN_D}"/>
      <path d="M86 40 q6 -16 14 -4 q6 -14 13 0 q8 -10 9 6" fill="${FUR}" stroke="${FUR_D}" stroke-width="2" stroke-linejoin="round"/>
      <circle cx="100" cy="96" r="60" fill="${FUR}"/>
      <path d="M100 52 c-14 -6 -40 2 -42 30 c-2 14 4 26 10 34 c-6 10 -6 24 6 34 c12 10 40 12 52 0 c12 -10 12 -24 6 -34
               c6 -8 12 -20 10 -34 c-2 -28 -28 -36 -42 -30z" fill="${SKIN}"/>
      <ellipse cx="100" cy="132" rx="30" ry="20" fill="url(#mz${id})"/>
      <ellipse cx="94" cy="122" rx="3" ry="2.2" fill="${INK}" opacity=".75"/>
      <ellipse cx="106" cy="122" rx="3" ry="2.2" fill="${INK}" opacity=".75"/>
    </g>`;

  const buste = (c) => `
    <path d="M30 220 c4 -34 26 -54 70 -54 c44 0 66 20 70 54z" fill="#27324a"/>
    <path d="M78 166 l22 30 l22 -30z" fill="#f4f4f5"/>
    <path d="M100 172 l-7 8 l7 30 l7 -30z" fill="${c.cravate}"/>
    <path d="M93 168 h14 l-3 6 h-8z" fill="${c.cravate}" opacity=".85"/>
    <path d="M78 166 l-10 20 l18 -6z M122 166 l10 20 l-18 -6z" fill="#1d263a"/>`;

  const accessoire = (c) => {
    if (c.accessoire === "lunettes") return `
      <g fill="none" stroke="${INK}" stroke-width="3"><circle cx="81" cy="92" r="15"/><circle cx="119" cy="92" r="15"/>
      <path d="M96 92 q4 -4 8 0 M66 90 l-18 -4 M134 90 l18 -4"/></g>
      <circle cx="81" cy="92" r="15" fill="#bfe3ff" opacity=".18"/><circle cx="119" cy="92" r="15" fill="#bfe3ff" opacity=".18"/>`;
    if (c.accessoire === "casquette") return `
      <path d="M48 66 c6 -36 98 -36 104 0 c-30 -8 -74 -8 -104 0z" fill="${c.cravate}"/>
      <path d="M44 66 c30 -10 82 -10 112 0 l18 6 c-40 -6 -98 -8 -130 -6z" fill="#b45309"/>
      <text x="100" y="56" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="700" fill="#fff">50K</text>`;
    return `
      <path d="M44 96 c0 -70 112 -70 112 0" fill="none" stroke="#1f2937" stroke-width="7" stroke-linecap="round"/>
      <rect x="32" y="84" width="16" height="28" rx="7" fill="#1f2937"/><rect x="152" y="84" width="16" height="28" rx="7" fill="#1f2937"/>
      <path d="M40 112 c0 20 18 32 40 30" fill="none" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
      <circle cx="82" cy="142" r="5" fill="${c.cravate}"/>`;
  };

  // ---------------------------------------------------------------- yeux, sourcils, bouche selon l'humeur
  const oeil = (x, y, r = 10, p = 5, dx = 0, dy = 0) =>
    `<ellipse cx="${x}" cy="${y}" rx="${r}" ry="${r * 1.1}" fill="#fff" stroke="${INK}" stroke-width="2"/>
     <circle cx="${x + dx}" cy="${y + dy}" r="${p}" fill="${INK}"/><circle cx="${x + dx + p * 0.4}" cy="${y + dy - p * 0.4}" r="${p * 0.35}" fill="#fff"/>`;
  const etoile = (x, y) => `<path d="M${x} ${y - 12} L${x + 3.5} ${y - 3.5} L${x + 12} ${y} L${x + 3.5} ${y + 3.5} L${x} ${y + 12}
     L${x - 3.5} ${y + 3.5} L${x - 12} ${y} L${x - 3.5} ${y - 3.5}z" fill="#facc15" stroke="${INK}" stroke-width="1.5" stroke-linejoin="round"/>`;
  const spirale = (x, y) => `<path d="M${x} ${y} m-1 0 a2 2 0 1 1 3 1 a5 5 0 1 1 -7 -4 a8 8 0 1 1 12 7" fill="none" stroke="${INK}" stroke-width="2.4" stroke-linecap="round"/>`;
  const S = `fill="none" stroke="${INK}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"`;

  const VISAGES = {
    serein: () => `
      <path d="M71 94 q10 -9 20 0 M109 94 q10 -9 20 0" ${S}/>
      <path d="M72 78 q9 -4 18 -1 M110 77 q9 -3 18 1" ${S} stroke-width="2.6"/>
      <path d="M86 140 q14 10 28 0" ${S}/>
      <ellipse cx="66" cy="114" rx="7" ry="4" fill="#f59e9e" opacity=".45"/><ellipse cx="134" cy="114" rx="7" ry="4" fill="#f59e9e" opacity=".45"/>`,
    confiant: () => `
      ${oeil(81, 92, 10, 5, 2, 1)}${oeil(119, 92, 10, 5, 2, 1)}
      <path d="M70 90 q11 -6 22 0 v-6 q-11 -6 -22 0z" fill="${SKIN}"/><path d="M70 90 q11 -6 22 0" ${S} stroke-width="2.4"/>
      <path d="M71 76 q9 -3 19 0 M109 70 q10 -7 20 -1" ${S} stroke-width="2.8"/>
      <path d="M86 140 q16 6 30 -6" ${S}/><path d="M114 132 l4 4" ${S} stroke-width="2.4"/>`,
    euphorique: () => `
      ${etoile(81, 92)}${etoile(119, 92)}
      <path d="M70 74 q10 -9 21 -3 M109 71 q11 -6 21 3" ${S} stroke-width="2.8"/>
      <path d="M80 132 q20 4 40 0 q-2 22 -20 22 q-18 0 -20 -22z" fill="#7f1d1d" stroke="${INK}" stroke-width="3" stroke-linejoin="round"/>
      <path d="M84 133 h32 v5 q-16 3 -32 0z" fill="#fff"/><ellipse cx="100" cy="148" rx="9" ry="5" fill="#fb7185"/>
      <ellipse cx="64" cy="116" rx="9" ry="5" fill="#f87171" opacity=".55"/><ellipse cx="136" cy="116" rx="9" ry="5" fill="#f87171" opacity=".55"/>
      <g fill="#facc15">${etoile(30, 40)}${etoile(172, 52)}</g>`,
    frustre: () => `
      ${oeil(81, 94, 9, 4.5, 0, 2)}${oeil(119, 94, 9, 4.5, 0, 2)}
      <path d="M69 78 l22 8 M131 78 l-22 8" ${S} stroke-width="4"/>
      <path d="M86 146 q14 -11 28 0" ${S}/>
      <path d="M148 62 q6 10 0 14 q-6 -4 0 -14z" fill="#7dd3fc" stroke="${INK}" stroke-width="1.5"/>`,
    tilt: (id) => `
      <ellipse cx="100" cy="104" rx="46" ry="52" fill="#ef4444" opacity=".28"/>
      ${spirale(81, 93)}${spirale(119, 93)}
      <path d="M67 74 l24 10 M133 74 l-24 10" ${S} stroke-width="4.2"/>
      <path d="M82 140 l6 -6 l6 6 l6 -6 l6 6 l6 -6 l6 6" ${S}/>
      <g fill="#e5e7eb" stroke="#9ca3af" stroke-width="1.5" class="vapeur${id}">
        <circle cx="54" cy="36" r="9"/><circle cx="44" cy="26" r="6"/><circle cx="146" cy="36" r="9"/><circle cx="156" cy="26" r="6"/></g>
      <text x="168" y="74" font-family="Inter, sans-serif" font-size="16" font-weight="800" fill="#ef4444">#@!</text>`,
    pause: () => `
      <path d="M71 96 q10 6 20 0 M109 96 q10 6 20 0" ${S}/>
      <path d="M72 82 q9 2 18 2 M110 84 q9 0 18 -2" ${S} stroke-width="2.4"/>
      <ellipse cx="100" cy="142" rx="5" ry="4" fill="${INK}" opacity=".8"/>
      <g font-family="Inter, sans-serif" font-weight="800" fill="#94a3b8"><text x="146" y="54" font-size="16">z</text>
      <text x="158" y="38" font-size="21">z</text><text x="172" y="20" font-size="26">Z</text></g>`,
    peur: () => `
      ${oeil(81, 92, 12, 2.6, 0, -1)}${oeil(119, 92, 12, 2.6, 0, -1)}
      <path d="M70 72 q10 -8 20 2 M130 72 q-10 -8 -20 2" ${S} stroke-width="2.8"/>
      <path d="M84 142 q4 -5 8 0 q4 5 8 0 q4 -5 8 0 q4 5 8 0" ${S}/>
      <path d="M150 70 q6 10 0 14 q-6 -4 0 -14z M46 76 q5 8 0 12 q-5 -4 0 -12z" fill="#7dd3fc" stroke="${INK}" stroke-width="1.5"/>
      <path d="M22 140 l-8 4 M24 152 l-9 0 M178 140 l8 4 M176 152 l9 0" stroke="#a855f7" stroke-width="3" stroke-linecap="round"/>`,
  };

  // l'ombre qui fait peur : la silhouette du singe, plus grande, derrière lui, yeux rouges et sourire de requin
  const ombre = () => `
    <g transform="translate(66 -46) scale(0.95)">
      <g fill="#2b1d40" stroke="#a855f7" stroke-width="2" stroke-opacity=".55">
      <path d="M86 40 q6 -16 14 -4 q6 -14 13 0 q8 -10 9 6"/>
      <circle cx="40" cy="98" r="20"/><circle cx="160" cy="98" r="20"/>
      <circle cx="100" cy="96" r="62"/><path d="M28 220 c4 -34 26 -54 72 -54 c46 0 68 20 72 54z"/></g>
      <path d="M72 88 l16 6 l-16 4z M128 88 l-16 6 l16 4z" fill="#ef4444"/>
      <path d="M74 128 l6 8 l6 -8 l6 8 l6 -8 l6 8 l6 -8 l6 8 l6 -8 l6 8" fill="none" stroke="#f5f5f5" stroke-width="2.5" stroke-linejoin="round"/>
    </g>`;

  // Dessins pixel (Gemini, validés par Yanisse le 27/10) : docs/singes/<agent|simu|topper>-<humeur>.png, carrés,
  // fond transparent ; Agent argent, Simu bronze, Topper or. Un compte sans dessins garde le singe SVG ci-dessus.
  const IMAGES = { mt5: "agent", simulation: "simu", topstep: "topper" };

  Y.singe = function (humeur, opts = {}) {
    const id = ++uid;
    const c = COMPTES[opts.compte] || COMPTES.mt5;
    const h = VISAGES[humeur] ? humeur : "serein";
    const taille = opts.taille || 160;
    const img = IMAGES[opts.compte || "mt5"];
    if (img) {
      const label = (Y.SINGE_HUMEURS[h] || {}).label || h;
      return `<img class="singe singe-${h} singe-pixel" src="singes/${img}-${h}.png" width="${taille}" height="${taille}"
        alt="Singe ${c.nom} : ${label}" loading="lazy" decoding="async">`;
    }
    const penche = h === "pause" ? "rotate(-6 100 200)" : h === "peur" ? "translate(-20 8)" : "";
    const label = (Y.SINGE_HUMEURS[h] || {}).label || h;
    return `<svg class="singe singe-${h}" viewBox="-20 -20 240 250" width="${taille}" height="${Math.round(taille * 250 / 240)}" role="img"
      aria-label="Singe ${c.nom} : ${label}" xmlns="http://www.w3.org/2000/svg">
      <defs><radialGradient id="mz${id}" cx="50%" cy="40%" r="60%"><stop offset="0" stop-color="#f7dcbf"/><stop offset="1" stop-color="${SKIN_D}"/></radialGradient></defs>
      ${h === "peur" ? ombre() : ""}
      <g transform="${penche}">${buste(c)}${tete(id)}${VISAGES[h](id)}${accessoire(c)}</g>
    </svg>`;
  };
})();
