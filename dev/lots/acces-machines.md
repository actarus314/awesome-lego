# Lot accès des machines — robots, modèles de langage et agents

*Maintainer's working notes, in French: brief of the machine access batch (robots.txt, sitemap, llms.txt, Markdown list, structured data).*

Ligne : AL-81 de `dev/registre.md`. Ouvert le 27/11/2026 (question de Romain en vocal, puis échanges vocaux jusqu'à 23 h 27 : « fais tout ce que l'on a dit sans oublier d'étapes »). Type : mineur (le site sert des fichiers de plus et deux liens de plus ; rien ne change à l'affichage de l'annuaire). Relecture : ciblée Sonnet.

## Constat de départ (mesuré le 27/11/2026, v4.8 en ligne)

- `robots.txt`, `sitemap.xml`, `llms.txt` : absents (404). `data.json` (1.26 Mo, toutes les fiches) servi, mais rien ne le signale. Flux Atom annoncés dans l'en-tête. Données structurées schema.org : page À propos seulement (oubli, aucune raison écrite).
- Sans JavaScript, l'accueil ne montre que 528 caractères (menus) : les fiches sont un bloc JSON que `app.js` dessine. GPTBot, ClaudeBot et PerplexityBot n'exécutent pas le JavaScript (mesure de Vercel, 17/12/2024 : https://vercel.com/blog/the-rise-of-the-ai-crawler, ancienne) ; Googlebot l'exécute.
- `llms.txt` : 97 % des fichiers ne reçoivent aucune requête, lus surtout par les agents et outils de code (Ahrefs, 15/06/2026, 137210 domaines : https://ahrefs.com/blog/llmstxt-study/).
- Convention llms.txt (https://llmstxt.org/, modifiée le 10/08/2026, lue le 27/11/2026) : titre H1 seul obligatoire, résumé en citation, listes de liens `[nom](url): notes` sous des H2, section `Optional` ; version Markdown d'une page sans nom de fichier en `index.md` ; `link rel="alternate" type="text/markdown"` vers elle et `rel="describedby"` vers le `llms.txt`.

## Décisions de Romain (27/11/2026, vocal)

- Pas de refonte en HTML rendu à l'avance pour les robots : le site actuel (léger, rapide, sources séparées puis assemblées) se garde, sauf gain mesuré sur la vitesse et le reste. Le rendu à l'avance se **mesure en comparaison seulement**, temps de construction compris (« il ne faudrait pas que la génération prenne 3 plombes »).
- Un renvoi en dur dans le HTML vers le contenu pour les machines (idée de Romain), affiné par Claude : liens `alternate` et `describedby` dans l'en-tête, lien visible dans le pied de page, `noscript` gardé pour le visiteur sans JavaScript.
- Les fichiers pour machines suivent le site : écrits par la même construction, aux mêmes données, à chaque publication ; un contrôle de Check échoue si l'un manque ou si un lien mène nulle part.
- **Tous les robots autorisés**, entraînement compris (« bloquer, c'est encore une fois déclaratif ; on n'a qu'à les laisser passer ») : le `robots.txt` n'interdit rien.
- Générateur de site (Hugo, Astro) : pas maintenant ; regardé seulement si l'on veut une page par ressource ou si la construction devient pénible, et alors par comparaison mesurée côte à côte.

## Périmètre

1. `site/robots.txt` : tout autorisé, ligne `Sitemap`.
2. `site/sitemap.xml` : les 4 pages (accueil et À propos, en et fr), liens de langue (`xhtml:link`), `lastmod` = date de construction.
3. `site/llms.txt` (anglais) : résumé, chiffres tirés des données, licence, liens vers la liste Markdown en et fr, la sélection, `data.json`, les flux, la page À propos et les sources.
4. `site/index.md` et `site/fr/index.md` : la liste complète en Markdown, tirée de la même fonction que `full-list.md` (mode web : liens absolus, sans icônes ni HTML), en anglais et en français.
5. En-tête des deux accueils : `alternate` Markdown et JSON, `describedby` ; pages À propos : `describedby`.
6. Pied de page commun : « Liste en texte · Données (JSON) ».
7. `noscript` de l'accueil : une ligne visible qui renvoie à la liste en texte et aux données.
8. JSON-LD sur l'accueil : `WebSite` et `Dataset` (licence, version, date, distributions JSON et Markdown).
9. Contrôle dans `scripts/hygiene.py` (lancé par Check après la construction) et tests unitaires.
10. Mesure du rendu à l'avance, sur une copie, sans rien commiter du prototype.

Hors périmètre : une page par ressource ; la négociation de contenu (`Accept: text/markdown`), impossible sur GitHub Pages (aucun en-tête réglable) ; tout changement de l'affichage de l'annuaire.

## Fichiers

`scripts/build.py`, `site-src/index.html`, `site-src/about.html`, `site-src/footer.html`, `site-src/strings.json`, `site-src/style.css`, `scripts/hygiene.py`, `tests/`, `tests/budgets.json` si un budget bouge, `changes/machine-access.md`, `MAINTENANCE.md` (une ligne sur les fichiers pour machines), `dev/`.

Lot parallèle : demande #57 (modèle de publication C, AL-80), en brouillon, touche aussi `scripts/build.py` (numéros de version), `check.yml`, `dev/contexte.md`, `dev/registre.md`. Ce lot ne touche pas `check.yml` ; la seconde fusionnée se reprend sur la première.

## Étalon des contrôles

- Construction normale : tous les fichiers présents, chaque lien vers le site qu'ils portent mène à un fichier construit → aucun constat.
- `llms.txt` qui cite une adresse du site absente, `index.md` supprimé, lien du pied de page cassé → un constat chacun, qui nomme le fichier et l'adresse.
- `full-list.md` et `README.md` inchangés octet pour octet (`build.py --check`).

## Critère de correction écrit d'avance

Se corrigent les constats de relecture qui touchent l'objet du lot (fichiers pour machines, liens, contrôle), l'étalon, une régression de l'affichage ou des fichiers générés, ou la règle de la marque LEGO dans les textes français. Les autres suivent l'étape 3 de la clôture (geste sûr, registre, écart motivé).

## Livraison

Demande #60 (branche `machine-access`), prête le 28/11 à 00 h 30, CI verte sur bfc5dec ; la fusion par la session a été refusée par le classement automatique (28/11, 00 h 31) : Romain fusionne. Vérifié sur l'aperçu (https://3001.club/preview/60/) : `index.md` et `fr/index.md` servis en `text/markdown; charset=utf-8`, `llms.txt` et `robots.txt` en `text/plain`, `sitemap.xml` en `application/xml` ; Chrome affiche la liste Markdown sans la télécharger. Relecture ciblée Sonnet (0 / 2 / 11) et contre-vérification (0 / 0 / 4) : détail dans le corps de la demande.

## Mesure du rendu à l'avance (27/11/2026, 23 h 35 à 23 h 50)

Prototype sur une copie de `site/` (v4.9, 749 fiches), rien de commité : la liste telle que `app.js` la dessine (749 cartes, relevées dans Chrome après 6 s) écrite dans `<div id="list">` ; `app.js` inchangé, qui la redessine en arrivant. Conditions de `scripts/measure_speed.py` (Chrome 4 fois ralenti, 4G lente, gzip, téléphone de 390 px, 5 chargements, médiane) ; fin des scripts et chargement relevés par un script à part dans les mêmes conditions.

| Mesure (en / fr) | Actuel | Rendu à l'avance | Écart |
|---|---|---|---|
| Liste affichée (règle des 10 %) | 1424 / 1447 ms | 371 / 388 ms | −74 % |
| Tâche la plus longue jusqu'à la liste | 303 / 289 ms | 102 / 111 ms | −66 % |
| Tâche la plus longue pendant la lecture | sous 50 ms | 432 / 440 ms | `app.js` redessine tout |
| Fin des scripts (recherche et filtres utilisables) | 1355 / 1458 ms | 2051 / 2111 ms | +51 % |
| Chargement complet | 1799 / 1812 ms | 2154 / 2202 ms | +20 % |
| Poids de l'accueil, brut | 752159 / 768808 octets | 1347602 / 1390970 | +79 % |
| Poids de l'accueil, gzip | 162957 / 167505 octets | 259112 / 268046 | +59 % |
| Budget par fiche (`tests/budgets.json` : 1047 / 1069) | 1004 / 1026 | 1799 / 1857 | dépassé |
| Construction (rendu des cartes en Python, simplifié) | 0.48 s | ≈ +5 ms | négligeable |

Lecture : la liste paraît près de quatre fois plus tôt et les robots qui n'exécutent pas le JavaScript liraient les fiches ; en contrepartie, la recherche et les filtres répondent 0.7 s plus tard (page plus lourde à télécharger avant le script), et un redessin de 0.43 s gèle la page pendant la lecture. Ce redessin disparaîtrait si `app.js` reprenait les cartes déjà là au lieu de les redessiner (travail non mesuré) ; le retard de la recherche, non. La construction ne ralentit pas. Décision laissée à Romain : AL-82.
