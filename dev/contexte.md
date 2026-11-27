# Awesome LEGO — contexte (révisé en place le 26/11/2026 à 23 h 30 ; v4.3 en ligne, notes dans `dev/` depuis la #29)

*Maintainer's working notes, in French (state, decisions, pitfalls). The open items are in `dev/registre.md`.*

Annuaire public du monde de la brique, né d'une mesure du 23/11/2026 faite pour le Carnet de briques (dépôt actarus314/lego). Dépôt public **actarus314/awesome-lego**, site **https://actarus314.github.io/awesome-lego/** (anglais) et **/fr/**. Ce document porte l'état, les décisions, les pièges et le savoir ; **tout ce qui reste à faire est dans `dev/registre.md`** (identifiants AL-n), les lignes closes dans `dev/registre-clos.md`. Depuis le 26/11/2026 (décision de Romain, 23 h 13), ces notes vivent dans `dev/` du dépôt, en français, contrôlées par `dev/outils/passation.sh` ; avant, dans les documents du projet claude.ai « lego », où le journal détaillé jusqu'à la v4.2 reste gelé (claude/archive/awesome-lego-journal-2026-11-26.md).

## Savoir
- Notes du mainteneur dans le dépôt et leurs contrôles (registre, contexte, section « Savoir », carte des fichiers) : `passation.conf`, `dev/outils/passation.sh`, `CLAUDE.md` ; vérifié 27/11/2026
- Fonctionnement du dépôt, workflows, horaires, tâches du mainteneur : `MAINTENANCE.md` ; vérifié 27/11/2026
- Règles des données (champs, `audience`, rangs, dates abrégées) : `data/SCHEMA.md` ; règle de sélection : `contributing.md`, `site-src/about.json` ; vérifié 27/11/2026
- Cahiers des lots 2 et 3, tri des audits du 24/11 : projet claude.ai « lego », claude/awesome-lego-lot-2.md, claude/awesome-lego-lot-3.md, claude/audit-24-11-tri.md ; vérifié 26/11/2026
- Consigne de la revue mensuelle (texte de la tâche planifiée) : `dev/consigne-revue.md` ; vérifié 26/11/2026
- Nom de domaine du site (recherche ouverte le 26/11 par une autre conversation) : projet claude.ai, claude/awesome-lego-nom-de-domaine.md ; vérifié 26/11/2026
- Statistiques de visite (outils comparés, décision de n'en rien poser) : projet claude.ai, claude/awesome-lego-statistiques.md ; vérifié 25/11/2026
- Reprises des demandes #13 à #27 (causes mesurées) et durée des workflows : section « Conflits » ci-dessous (mesure d'un sous-agent par l'API, 26/11) ; vérifié 26/11/2026
- Audit tous azimuts du 26/11 (34 constats) : corps de la demande #28 pour ce qui est corrigé, lignes AL-57 à AL-64 de `dev/registre.md` pour le reste ; gardes-fous mécaniques : skill `audit-depot` (enregistrée le 26/11) ; vérifié 26/11/2026
- Journal détaillé jusqu'à la v4.2 : projet claude.ai, claude/archive/awesome-lego-journal-2026-11-26.md ; vérifié 26/11/2026
- Gardes-fous mécaniques et correcteur hebdomadaire (ce que chaque contrôle voit, ses listes blanches, ses pages de calibrage) : `MAINTENANCE.md`, sections Check, Render et Tidy ; cahier du lot : `dev/lots/gardes-fous.md` ; vérifié 27/11/2026
- Réglages GitHub à poser, Renovate, uv, contrôles à géométrie variable : skill `document-versionne`, « Travaillé dans GitHub » et « Dépôt sur GitHub » ; vérifié 26/11/2026

## État
- **En ligne : v4.4** (7eef29a, demande #30 fusionnée par Romain le 27/11 à 00 h 24) : la page À propos garde sa position au changement de langue ; « toujours d'actualité » sur une ligne ; flux nommé « Awesome LEGO », sans entrées d'agenda ; bouton « Tout » de la barre sous 440 px. v4.3 : c912e1f (bandeau de marque déplié, filtres gardés ouverts, résultats par catégorie, CHANGELOG court et contrôlé). 749 ressources en 12 catégories et 54 groupes.
- **Gardes-fous mécaniques** (demande #31, d63bc99, fusionnée le 27/11 à 01 h 03, sans numéro : la v4.5 la citera) : `scripts/hygiene.py` dans Check, sondes du téléphone et du CSS mort dans Render, workflow Tidy du lundi ; plafonds de poids mesurés sur la v4.4 (+5 %) ; outils Python installés en roues seules (`--only-binary=:all:`) ; Tidy en Python 3.13, seule version où pyoxipng a une roue, règle de Renovate qui le retient dans la demande #32 (AL-70). Premier Tidy le 30/11 (AL-71).
- **Pertinence de la recherche** : score MiniSearch (BM25), champs nom ×4, marques ×3, catégorie ×3, groupe ×2, puis résumé, forces, faiblesses, pays, ville, taille ; préfixe et approximation (20 % de la longueur du mot) ; tous les mots exigés ; pays du visiteur ×1.15.
- **Jeton Globalping** : posé par Romain le 26/11 ; essai à blanc de Links le 26/11 à 13 h 24 : 28 liens sur 29 relus, 9 cassés (AL-19).
- **Onglet Sécurité** (lu le 26/11 dans le Chrome de Romain) : 3 alertes ouvertes, toutes de Scorecard (Maintained, Branch-Protection, CII-Best-Practices ; AL-53) ; zizmor 10 et 11 fermées comme corrigées ; Code-Review et Fuzzing écartées.
- **Scorecard 6.8/10** au 25/11 ; ce qui manque est attendu pour un dépôt d'une personne.
- **Workflows** (655 passages lus par l'API le 26/11) : Render est seul sur le chemin critique d'une demande (passage médian ≈ 140 s depuis la #26, ≈ 190 s avant ; le job seul ≈ 126 s), puis CodeQL (≈ 50 s), Check (≈ 35 s) ; attente en file 3 à 4 s.
- **Exécutions planifiées** (horaires : `MAINTENANCE.md`) : environ 10 h de retard, jamais sautées pour Pages, Links et Data fixes ; Data report, Workflow audit et Scorecard pas encore vus en planifié (AL-01). Revue mensuelle par Claude : tâche trig_01FfntrWbosebDjkMh4MhNAm, consigne identique à `dev/consigne-revue.md` (26/11, 13 h 09) ; elle ne lit que le dépôt : `dev/` lui devient lisible, mais sa consigne ne le cite pas encore (AL-67) ; après la fusion d'une revue, la conversation suivante met ce document et le registre à jour.
- **Branches** : `main`, `history` (une mesure par jour, à ne jamais supprimer : historique des tendances), `auto/tidy` dès le premier Tidy ; `v4.3` supprimée par Romain le 27/11.
- **Réglages** : posés le 25/11 selon la skill `document-versionne` (« Dépôt sur GitHub ») ; application Claude Design Import retirée par Romain le 27/11 (AL-34).
- **Licences** : contenu CC BY-NC-SA 4.0, code PolyForm Noncommercial 1.0.0, REUSE ; mention de marque LEGO sur la page À propos.
- **Numérotation** : mineure à chaque changement de contenu ou de site, majeure si la structure ou le format des données change ; rien pour l'automatisation seule (citée par l'entrée suivante). Release étiquette à la fusion, versions immuables (titre et notes restent modifiables).

## Façon de travailler (Romain, 25/11 à 10 h 52, complété le 26/11)
- Commit direct sur `main` pour ce qui ne change pas le site (contournement administrateur) ; demande de fusion avec aperçu pour ce qui se voit ; branche dédiée en brouillon pour un dossier long ou incertain ; pas de branche `dev`.
- **Une seule demande à la fois porte `VERSION`, `CHANGELOG.md` et les fichiers générés** ; jamais de demande empilée sur une branche non fusionnée (constats du 26/11, ci-dessous).
- Chrome de Romain : dépannage pour un acte unique, jamais un geste régulier (24/11, 13 h 25) ; « si tu peux le faire autrement (via Chrome par exemple), fais-le » (25/11, 5 h 51).

## Conflits entre demandes (mesure du 26/11 sur #13 à #27)
17 commits de reprise sur 9 demandes, 9 fusions en conflit, ≈ 12 % du temps d'exécution de Check, Render, Preview et CodeQL. Causes : demandes empilées puis fusion par squash de la base (5 des 9 conflits, dont les 2 seuls vrais conflits de code, tous dans la #25) ; `VERSION` et `CHANGELOG.md` dans chaque demande (un tiers des reprises, 3 renumérotations) ; `MAINTENANCE.md` touché par 25 des 107 commits des demandes (4 conflits) ; fichiers générés commités (`full-list.md`, images du README, verrou Python) ; branches longues en parallèle. La file de fusion de GitHub n'est pas offerte aux dépôts d'un compte personnel (documentation GitHub, « Managing a merge queue », lue par le sous-agent le 26/11). Remède en place : règles du `CLAUDE.md` ; remède structurel proposé : AL-49. La file de fusion n'aurait pas évité ces reprises (constat du 26/11, 23 h 10) : une demande en conflit n'y entre pas.

## Pièges
- (27/11) Une modification de `renovate.json` qui retient une version a été refusée à la session sans accord explicite de Romain ; posée après son accord, demande #32 (AL-70).
- (26/11, 23 h 15) La fusion par squash ne garde que le titre de la demande : les blocs `Relecture:`, `Constats:`, `Registre:` et `Savoir:` de `passation` vont dans le corps de la demande, et `passation.conf` n'a pas de `LIVRABLES` (contrôle des commits étiquetés impossible).
- Fusion par squash et branche qui a reçu la branche fusionnée : fusionner le dernier commit de la branche fusionnée (arbre identique au squash, vérifié par `git diff`), puis `git merge -s ours origin/main` ; jamais `ours` sans cette vérification.
- Un workflow `pull_request` ne part pas tant que la demande est en conflit : un contrôle absent se lit d'abord comme un conflit.
- Une branche ne porte jamais le nom d'une version (`v4.3`) : Release crée l'étiquette du même nom.
- Un renommage de section se reporte dans le `<title>` et la description de la page (#27).
- Tout bloc de données affiché se vérifie par script sur toutes les fiches ; `check_site.py` se lance aussi avec `--dejavu` ; toute page livrée passe aussi `controle-rendu.py` de `document-versionne` (plafond de longueur de ligne).
- Un `<details>` réécrit par `innerHTML` perd la cible d'un clic : écouter en phase de capture (v4.3, panneau de filtres).
- Renovate `config:recommended` ignore `**/tests/**` : `ignorePaths` redéfini (f88cf66).
- Deux conversations peuvent pousser sur la même branche : lire le retour de `git push` ; un refus se reprend par `git rebase origin/<branche>` sur ses propres commits, jamais par une poussée forcée.

## Accès de la session (vérifiés du 24 au 26/11)
- `gh api` en REST (GraphQL refusé) : demandes, commentaires, lancement de workflow (`workflow_dispatch`), relance (`rerun-failed-jobs`), journaux des jobs ; **suppression d'une branche distante refusée** (proxy, 26/11) ; fusion, poussée forcée, annulation d'un passage refusées.
- Ajout du dépôt en écriture refusé si Romain ne l'a pas demandé ; lecture du dépôt public sans ajout.
- Onglet Sécurité lu dans le Chrome de Romain ; **écarter une alerte d'analyse de code refusé par le classement automatique** (26/11, alerte 12) ; réglages du dépôt lus et posés dans son Chrome avec son accord.
- Tâches planifiées modifiables sur demande explicite qui nomme la consigne (« Mets la consigne à jour »).
- Reddit illisible partout (Arctic Shift à la place) ; lego.com refuse curl, lisible par Exa ; r.jina.ai refusé ; `npx @mermaid-js/mermaid-cli` refusé (vérifier un diagramme avec `mermaid` dans Playwright).
- Un serveur local lancé en arrière-plan s'arrête quelques minutes après une réponse ; clone superficiel : `git fetch --depth=50` avant toute fusion de `main`.
- Les sous-agents ont l'outil des documents du projet claude.ai (lecture et écriture vues le 26/11).

## Décisions de Romain (une ligne chacune ; le détail est dans les demandes et l'historique)
- 26/11, 13 h 18 (demande de la conversation) : bandeau de marque déplié sauf sur mobile ; filtres gardés ouverts après réouverture et action, grand écran seulement ; pertinence et catégories combinées, « je te laisse juger » ; règles à généraliser ; audits automatisés « de sorte que je n'aie plus à y penser » ; passe d'optimisation ; conflits des demandes à expliquer ; workflows encore plus rapides sans perte de qualité ? ; CHANGELOG illisible ; jeton Globalping posé ; propositions de skills ; mise en conformité `passation`. Fait dans la #28 (v4.3) et dans le projet (registre, contexte réécrit, cartes de skills AL-52).
- 26/11, 23 h 10 et 23 h 13 : notes du mainteneur dans `dev/` du dépôt public, **en français** (l'outil `passation.sh` lit ses colonnes et statuts en français ; exception à « tout le reste en anglais » limitée à `dev/`) ; audit : « je pensais à des gardes-fous et optimisateurs mécaniques » (skill `audit-depot` réécrite en ce sens, enregistrée par Romain) ; question sur la file de fusion (indisponible pour un compte personnel, vérifié dans la documentation de GitHub).
- 26/11, 23 h 26 : #29 fusionnée (notes dans `dev/`).
- 26/11, 23 h 04 : #28 fusionnée (v4.3).
- 26/11, 13 h 03 et 13 h 09 : consigne de la revue mensuelle mise à jour pour la page À propos.
- 26/11, 12 h 06, 12 h 42, 12 h 54 : #23 (v4.0), #25 (v4.1), #27 (v4.2) fusionnées ; 11 h 42 : #26 (Render accéléré).
- 26/11, 9 h 11 à 11 h 44 : passe UX (S2 Retour du navigateur, S3 barre repliée à toute largeur, S5 « Par où commencer » repliable sur téléphone, S6 pays du visiteur en tête, Q11 chiffres en une rangée, Q13 Observatoire sur téléphone) ; `--faint` gardé à 5.6:1, exception de l'annuaire à la règle 3 à 4:1 d'`interface-outil` (« On garde en l'état »).
- 26/11, 8 h 27 à 8 h 58 : accueil propre au téléphone seulement (S1) ; page À propos : « Participer », « Être mis en avant », « ★ Sélection me convient ».
- 25/11, 21 h 17 et 20 h 21 : page À propos pour les non-développeurs ; contact par GitHub seul pour l'instant ; MAINTENANCE.md plus visuel.
- 25/11, 20 h 14 : mois abrégés partout (remplace « sans abréviation » du 24/11 à 10 h 43) ; passe UX petits formats ; changement de langue qui garde la place.
- 25/11, 18 h 57 : en-tête sur une ligne, menu ⚙ Réglages.
- 25/11, 16 h 54 : pas d'application installable (PWA) ; signal : usage répété hors connexion.
- 25/11, 16 h 48 : public élargi aux enfants, sans DUPLO, nouvelle accroche (v4.0).
- 25/11, 16 h 34 : les demandes avec aperçu valent pour un dépôt public ; socle allégé pour un dépôt privé.
- 25/11, 11 h 38 à 11 h 43 : image du README en avertissement, jamais en échec ; contrôles à géométrie variable ; outils Python épinglés par empreinte ; Pillow corrigé.
- 25/11, 11 h 30 : aucune statistique de visite pour l'instant ; signal : une décision qui attend un chiffre.
- 25/11, 11 h 11 : quatre réglages renforcés, zizmor et Scorecard.
- 25/11, 11 h 05 : applications GitHub généralistes ; Renovate plutôt que Dependabot.
- 25/11, 8 h 31 à 8 h 34 : aperçu de chaque demande sur GitHub avant fusion, image du README par script mais pas chaque jour.
- 25/11, 7 h 38 à 8 h 08 : « Qui fabrique », réglage nouvel onglet, mode marque, remonter en haut, lien « Proposer une ressource » (v3.4, v3.5).
- 24/11, 13 h 40 et 12 h 55 : lot 3 en trois conversations ; « Par où commencer » en besoins ; rang 1 à 5 par fiche, sélection = rang 1 mondial de chaque groupe.
- 24/11, 12 h 38 à 12 h 41 : on ne refait pas l'existant (3 à 5 par pays ou langue) ; exhaustifs : lieux uniques et marques qui vendent des sets en Europe.
- 24/11, 12 h 29 : une fiche par service d'un même site, reliées par « Du même site ».
- 24/11, 12 h 12 à 12 h 28 : rôle de chaque élément d'une carte ; codes de langue sans infobulle.
- 24/11, 11 h 58 : bandeau de marque avec logo, LEGO compris.
- 24/11, 11 h 41 à 11 h 57 : liens revérifiés par Globalping ; rapport mensuel la veille de la revue ; onglet Sortir supprimé.
- 24/11, 10 h 13 et 10 h 48 : règle de la marque LEGO en français (étendue au Carnet).
- 24/11, 10 h 17 à 10 h 56 : villes au nom usuel de chaque langue ; source du site découpée ; REUSE ; vitesse gardée à 10 % de gain.
- 24/11, 9 h 18 : WCAG 2.2 AA n'est pas un objectif, axe-core reste un garde-fou ; 8 h 51 : trois régimes ; 7 h 56 : « être à jour de tout partout tout le temps, modulo quelques jours pour vérifier, sauf les correctifs de sécurité ».
- 24/11, 3 h 21 : « je ne devrais pas avoir à te reprendre là-dessus » (contrôle de rendu par script).
- 24/11, 0 h 55 à 1 h 20 : mode marque, carte dessinée par le site, filière en trois listes.
- 23/11, 16 h 19 à 23 h 17 : dépôts, licences non commerciales, README brut et beau site, Romain seul maître du dépôt, site seul bilingue, revue mensuelle, MiniSearch, thème Bleu jour, documents annexes toujours à jour, sources lisibles par machine, LLM par API dans GitHub Actions seulement avec une activité communautaire, pas de comparaison de fiches, extraction de valeur tranchée (agenda, fiche marque, carte, indépendance, fiabilité, tendances, filière).
