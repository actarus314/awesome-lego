# Awesome LEGO — registre d'avancement

*Maintainer's working notes, in French: what is left to do, check, decide or watch.*

Seul registre de ce qui reste à faire, à vérifier, à décider ou à surveiller pour l'annuaire (skill `passation`) ; contexte : `dev/contexte.md`. Une ligne ne disparaît jamais : `fait vX.Y`, `abandonné : raison` ou `fusionné → ID` ; à la clôture d'un lot, les lignes closes descendent dans `dev/registre-clos.md`. Identifiants `AL-n` : 1 à 47 reprennent l'ancienne liste « Ouvert » (projet claude.ai) ; AL-57 à AL-64 viennent de l'audit Opus du 26/11 (34 constats : 18 corrigés dans la #28, 15 rangés ici, 1 écarté : Scorecard à chaque poussée sur `main`, sans coût d'attente). Mis à jour le 27/11/2026 à 0 h 55 (demandes #30 et #31 ouvertes).

Priorités : P0 sécurité ou perte, P1 fausse une décision, P2 fiabilité, P3 confort, P4 à l'occasion, V veille. Exécutant : C (Claude), CC (Claude dans le Chrome de Romain), R (Romain), RM (revue mensuelle planifiée).

## Carte des fichiers

| Fichiers | Rôle |
|---|---|
| `data/`, `site-src/`, `scripts/`, `tests/`, `.github/`, `CHANGELOG.md`, `VERSION`, `MAINTENANCE.md`, `contributing.md`, `CLAUDE.md`, `passation.conf`, `dev/contexte.md`, `dev/registre.md`, `dev/consigne-revue.md` | source |
| `README.md`, `full-list.md`, `media/`, `package-lock.json` | détail : générés ou verrouillés (README, liste, images, verrou npm) ; les logos et icônes de `media/` sont des sources |
| `dev/registre-clos.md`, `dev/lots/` | détail : lignes closes, cahiers des lots |
| `changes/` | source : fragments des demandes fusionnées (type et entrée), assemblés puis supprimés par le workflow Version |
| `dev/outils/` | source : copies des outils de la skill `outils-versionnement`, remplacées à chaque reprise |
| `LICENSE`, `LICENSE-CODE.md`, `LICENSES/`, `REUSE.toml`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.editorconfig`, `.gitignore`, `package.json`, `renovate.json` | source : licences, règles du dépôt, configuration |

## Lots

| Lot | Items | Fichiers | Prérequis | Statut |
|---|---|---|---|---|
| notes-dev | AL-48, AL-67 | `dev/`, `passation.conf`, `CLAUDE.md`, `REUSE.toml` | — | fait 26/11 : demande #29 fusionnée par Romain à 23 h 26 ; arrivé : `dev/contexte.md`, `passation.conf` |
| gardes-fous | AL-50 | `scripts/hygiene.py`, `scripts/check_site.py`, `scripts/tidy.py`, `tests/`, `.github/workflows/check.yml`, `.github/workflows/render.yml`, `.github/workflows/tidy.yml`, `MAINTENANCE.md` | — | fait 27/11 : `dev/lots/gardes-fous.md` ; demande #31 fusionnée par Romain à 01 h 03 (d63bc99, sans numéro de version) ; arrivé : `dev/contexte.md` |
| entretien | AL-22, AL-46, AL-57, AL-59, AL-60, AL-61, AL-62, AL-64 | `scripts/`, `site-src/`, `data/SCHEMA.md`, `.github/workflows/fixes.yml` | — | fait v4.5 : demande #35 fusionnée par Romain le 27/11 à 03 h 25 (47ddb7b) ; AL-59 abandonné, AL-46 laissé en veille |
| vitesse | AL-58 | `site-src/app.js` | — | fait v4.5 : même demande #35 |
| publication | AL-49, AL-51, AL-63 | `.github/workflows/`, `scripts/changes.py`, `renovate.json`, `CLAUDE.md` | — | fait 27/11 : `dev/lots/publication.md` ; demande #34 fusionnée par Romain à 03 h 42 (b4e0a0f, sans numéro : fragment `none`) ; variante sans écriture directe sur `main` (l'application n'est pas dans les exceptions du ruleset) ; arrivé : `dev/contexte.md` |
| rangement | AL-69 | `contributing.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `renovate.json` | accord de Romain ; après publication | abandonné : décision de Romain le 27/11 à 01 h 18 (gain faible) ; cahier `dev/lots/rangement.md` gardé |

## Gestes et décisions de Romain

| ID | P | Objet | Exécutant | Lot | Statut |
|---|---|---|---|---|---|
| AL-72 | P3 | Code sous GNU AGPL 3.0 au lieu de PolyForm Noncommercial, contenu inchangé (CC BY-NC-SA 4.0) : décision de Romain du 27/11 à 03 h 21 (« Code seul »), variante « only » choisie par Claude ; demande #36 ; ensuite, critère `floss_license` du badge OpenSSF (projet 17176) à passer à Met dans le Chrome de Romain | R (fusion), puis C | — | ouverte : #36 en brouillon, à fusionner après #34 |
| AL-74 | P4 | Décisions laissées par la v4.5 : date de retrait des adresses héritées (1er juin 2027, proposée par Claude) ; Render qui lit les mesures du site publié (`--from-site-only`) ; index de recherche gardé sur la mesure de la première prise de focus (il ne change pas le temps de la liste) | R | — | ouverte : en vigueur tant que Romain ne dit pas autre chose |
| AL-53 | P3 | Alertes Scorecard : Branch-Protection (#12) écartée par Romain (vue « Dismissed » le 27/11 à 01 h 20) ; Maintained (#17) se ferme seule quand le dépôt a 90 jours (vers le 21/02/2027) ; CII-Best-Practices (#19) : badge OpenSSF rempli par Claude dans le Chrome de Romain le 27/11 (projet 17176, 97 %), mais le niveau « passing » est hors d'atteinte : il exige une licence libre, et PolyForm Noncommercial et CC BY-NC-SA ne le sont pas ; Scorecard donne 2/10 à un badge en cours, 5 au niveau passing : l'alerte #19 reste ouverte tant que le score est sous 10 | R | — | ouverte : écarter #19 « won't fix » (geste de Romain), ou la laisser ouverte |
| AL-19 | P2 | Ticket « Broken links » #10 : essai à blanc du 26/11 (jeton Globalping actif, 28 liens sur 29 relus) : 9 cassés de partout, dont la page Lidl de Playtive Clippys ajoutée en v4.0 (404), l'article du Manila Times (source de Brickseum, v3.2), le flux de nifeliz, un PDF du Bundesgerichtshof, toy-links.com/mouldking, mocbrickland.com, bricksinbits.com | R | — | ouverte : lire le ticket après Links du mercredi 02/12/2026 |
| AL-68 | P3 | Nom de domaine grand public pour le site (dépôt gardé en « awesome-lego ») : recherche ouverte par Romain le 26/11 à 13 h 40 dans une autre conversation ; détail : projet claude.ai, claude/awesome-lego-nom-de-domaine.md | R, avec C | — | ouverte : pistes à juger par Romain |
| AL-15 | P4 | Coffre : glissés tactiles et son non vérifiés sur un vrai téléphone | R | — | ouverte : à essayer par Romain sur son téléphone |
| AL-08 | P4 | Idées gardées : distinguer par la forme ce que la couleur seule distingue ; langues d'interface allemande et italienne | R | — | ouverte : en attente d'une demande de Romain |
| AL-09 | P4 | Archivage des sources (copie datée de chaque page citée) : non mis en place | R | — | ouverte : en attente d'une demande de Romain |

## À l'occasion

| ID | P | Objet | Exécutant | Lot | Statut |
|---|---|---|---|---|---|
| AL-46 | P4 | Mineurs laissés par les relectures de la v4.0 : cercles de « Dernier signe de vie » petits au doigt, libellés des chiffres à 1.5 px du bord à 320 px, graphique entre 480 et 640 px, survol d'onglet sur l'en-tête des aperçus, lien de catégorie gris, `:has()` avant Firefox 121, étiquettes `pt` et `es`, `#` vide du bouton de langue de la page À propos | C | — | ouverte : si un usage le montre |

## À décider

| ID | P | Objet | Exécutant | Lot | Statut |
|---|---|---|---|---|---|
| AL-63 | P4 | Renovate sans `lockFileMaintenance` : dépendances npm indirectes figées entre deux mises à jour directes. Essayé dans #34 puis retiré : avec le délai global de 3 jours (`minimumReleaseAge`), la maintenance des verrous n'a pas de date de publication et ne s'ouvrirait jamais (documentation de Renovate, relecture de #34) ; la faire marcher demande de lever ce délai pour elle, donc d'accepter des dépendances indirectes sans délai | R | — | ouverte : à décider (garder le délai partout, ou l'exception pour les verrous) |

## Revue mensuelle

Lignes que la revue du 5 lit et traite (consigne : `dev/consigne-revue.md`) ; la conversation qui suit sa fusion met leur statut à jour.

| ID | P | Objet | Exécutant | Lot | Statut |
|---|---|---|---|---|---|
| AL-75 | P4 | Brick Fan Event : sa récurrence porte des dates (« next dates 20 and 21 Mar 2027 in Charlotte ») à côté de « Next edition: 6 Feb 2027 » : texte qui se périme (relecture de #35) | RM | — | ouverte |
| AL-05 | P3 | Données laissées à la revue mensuelle (régimes, French'Brick IDF, steine-kanal, confiance basse, TechLUG, abonnés divergents, paliers Patreon, publicités, BrickFair et Brickworld au 03/04/2027, sources à deux dates, Vanha Palikka et Latericius illisibles, r/legostorage, Brickfall, Brick Budget, LEGO Certified Professionals 19/22/27, Japan Brickfest, dates Fan CoLab d'Océanie et d'Asie, tailles Arctic Shift, `last_activity` de r/lego) | RM | — | ouverte : revue du 05/12/2026 |
| AL-06 | P3 | Filière : indépendance des sources comptée par site ; 16 marques sans fabricant établi (IAMBRICK, JAKI, INSOON, Stone Heap, Build Army sans fabricant déclaré) ; Eikee fondée en 2022 ou 2024 | RM | — | ouverte |
| AL-13 | P3 | Coordonnées non publiées à la source ; courriels de LEGOLAND Shanghai et du Discovery Centre de Hong Kong trop longs pour 320 px | RM | — | ouverte |
| AL-18 | P3 | Relectures à la source : Brick Haus, Coffee & Bricks Limburg, Brickjournal, Brick Train Awards, prix sans mention des taxes, `ships_to_france` de 9 boutiques, `brands` de 10 fiches, 3 adresses en http, notes de fiabilité rédigées comme des étapes, statuts déclarés divergents, Steingemachtes | RM | — | ouverte |
| AL-24 | P4 | Reddit illisible même par les navigateurs : rangs des sous-reddits sur les chiffres d'Arctic Shift | RM | — | ouverte |
| AL-38 | P3 | Public enfant, suites : chaînes YouTube françaises et allemandes, magazines Blue Ocean France et Immediate Media, Snapology et autres illisibles, réseaux polonais non lus, LEGO League (fiche en 2027), Discovery Centres sans fiche propre, 13 marques sans fiche qui les cite | RM | — | ouverte |

## Veille

| ID | P | Objet | Signal pour agir | Qui regarde | Statut |
|---|---|---|---|---|---|
| AL-73 | V | Fuzzing hebdomadaire (ClusterFuzzLite, Atheris) des fonctions qui lisent des pages et flux tiers : décision de Romain du 27/11 à 03 h 17 ; coût visé : nul sur les demandes, une séance bornée par semaine | un plantage trouvé (le corriger avec un test qui le rejoue) ; une séance au-delà de sa durée ; retour : retirer le workflow et `.clusterfuzzlite/` | C | ouverte : demande en préparation |
| AL-71 | V | Gardes-fous mécaniques (#31) : décidés par Claude le 26/11 sur la demande de Romain ; risques : un faux positif qui bloque Check sur une demande saine, un Tidy qui ouvre une demande chaque semaine ; porteurs : `scripts/hygiene.py`, `scripts/check_site.py`, `.github/workflows/tidy.yml`, `tests/css-states.txt`, `tests/vulture-allow.py`, `tests/budgets.json` | un constat d'un garde-fou que la correction ne justifie pas (le nommer dans la liste blanche du contrôle), ou un Tidy les lundis 30/11 et 07/12 qui ne se vide pas après fusion ; retour : annuler d63bc99, ou retirer l'étape « Mechanical guards » de `check.yml` | C à chaque demande, R pour Tidy | ouverte : premier Tidy le 30/11 |
| AL-03 | V | Tendances dans l'Observatoire ; changements de statut dans le flux | deux fenêtres de 90 jours dans `history` | C, à la conversation qui suit le 23/05/2027 | ouverte : échéance 23/05/2027 |
| AL-14 | V | Lecture d'activité en parallèle | un rapport mensuel qui diverge | C, à la lecture du rapport du 4 | ouverte |
| AL-35 | V | Renovate et les verrous Python (`pip-compile`) | première demande de Renovate sur un outil Python : verrou recompilé avec empreintes, sinon recompilation par une session | R (la demande arrive chez lui), puis C | ouverte |
| AL-43 | V | Revue mensuelle et page À propos | la demande du 05/12 dit « about page unchanged » ou ce qui a changé ; avec #34, elle dépose un fragment au lieu de monter `VERSION` (consigne recopiée dans la tâche le 27/11 à 02 h 58, avec un repli devenu inutile) | R à la lecture, C ensuite | ouverte : échéance 05/12/2026 |
| AL-45 | V | Render accéléré (#26) : décidé par Claude le 26/11 (demande de Romain) ; risque : constats instables sous la charge de plusieurs navigateurs | un Render au-delà de 3 min, un constat qui apparaît et disparaît sans changement du site, un avertissement de quota de cache ; retour : `--jobs 1` dans `render.yml`, ou annuler a298cc2 | C à chaque demande | ouverte |
| AL-65 | V | Check annule le passage précédent d'une même demande (v4.3) : décidé par Claude le 26/11 ; risque : le contrôle requis affiché « annulé » sur un ancien commit | une demande bloquée par un contrôle annulé ; retour : retirer `concurrency` de `check.yml` | C à chaque demande | ouverte : en place depuis la v4.3 (26/11, 23 h 04) |
| AL-01 | V | Exécutions planifiées (clos le 25/11 : en retard d'environ 10 h, jamais sautées pour Pages, Links et Data fixes ; Data report, Workflow audit et Scorecard pas encore vus en planifié) | une exécution planifiée sautée (ligne « Watch the scheduled runs » de `MAINTENANCE.md`) ; premier Data report le 04/12 | C | ouverte : vérifier le 04/12/2026 |
| AL-40 | V | Contact par GitHub seul (Romain, 25/11) | des visiteurs qui disent ne pas pouvoir écrire faute de compte | R | ouverte |

## Clos

Les lignes closes sont dans `dev/registre-clos.md`.
