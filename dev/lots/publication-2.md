# Lot publication 2 — ce qui est en ligne est ce qui se télécharge

*Maintainer's working notes, in French: brief of the publication model, to be decided by the maintainer before any code.*

Ligne : AL-80 de `dev/registre.md`. Ouvert le 27/11/2026 (échange vocal de Romain, 20 h 15 à 20 h 49). Romain : « je veux que ce soit vraiment la dernière fois que l'on modifie cette architecture de publication ». Méthode convenue : exigences d'abord, sans solution ; comparaison de modèles éprouvés sur les mêmes exigences ; relecture en contradicteur, en contexte neuf ; une décision de Romain, une seule fois, avec la liste des défauts restants et leur parade. Aucun code avant cette décision.

## 1. Exigences (sans solution)

| N° | Exigence | D'où elle vient |
|---|---|---|
| E1 | Ce qui est en ligne est exactement ce qu'obtient un visiteur qui télécharge le projet : clone de la branche par défaut, bouton « Download ZIP », dernière version des Releases | Romain, 27/11 (vocal) : « ce qui est en production soit ce qui est téléchargeable par quelqu'un qui passe par là » |
| E2 | Un aperçu de ce qui va partir en ligne, tout ensemble, avant chaque publication | Romain, 27/11 (vocal) |
| E3 | Pas de conflit entre demandes ouvertes en même temps | mesure du 26/11 (`dev/contexte.md`, « Conflits ») ; raison des fragments (#34) |
| E4 | Durée : une demande ordinaire pas plus lente qu'aujourd'hui (≈ 2 min 30) ; une publication et une urgence en quelques minutes | Romain, 27/11 (vocal) |
| E5 | Réplicable : tout ce qui fait tourner la publication vit dans le dépôt (workflows, configuration, réglages décrits ou posés par script) | Romain, 27/11 (vocal) |
| E6 | Aucune règle à retenir de tête : le mauvais bouton est impossible, ou sans effet, ou rattrapé seul | Romain, 27/11 (vocal) ; trois refontes nées de défauts trouvés en route |
| E7 | Le numéro affiché par le site est celui du contenu affiché | constat du 27/11 : brique et page 404 en ligne sous « v4.8 » |
| E8 | L'activité relevée chaque jour (statuts, dernières nouvelles, dates passées) continue d'arriver en ligne chaque jour, sans version | décision du 23/11 (revue quotidienne), `MAINTENANCE.md` |

Contraintes du dépôt, vérifiées le 27/11 :
- un seul mainteneur, compte personnel gratuit ; fusion par écrasement seule (`allow_squash_merge` seul permis) ; file de fusion indisponible pour un compte personnel (`dev/contexte.md`) ;
- ruleset `main` (lu par l'API le 27/11) : pas de suppression ni de poussée forcée, historique linéaire, demande obligatoire (0 approbation), contrôle `check` requis ; contournement : rôle administrateur, toujours ;
- réglé par Romain, à ne rouvrir qu'avec une raison nouvelle : « pas de branche `dev` » (25/11) ; « pas de relecture obligatoire ni de ruleset plus strict » (`CLAUDE.md`) ;
- ce qui écrit aujourd'hui vers `main` : les demandes de Romain et de Claude, Renovate, Data fixes (`auto/data-fixes`), Tidy (`auto/tidy`), Version (`auto/version`), la revue mensuelle ; les notes `dev/` par poussée directe (contournement administrateur) ;
- ce qui publie le site, toujours depuis la branche par défaut : chaque poussée sur `main`, le passage quotidien de 04:17 UTC, chaque aperçu (Preview relance Pages en mode « aperçus », qui reconstruit aussi le site), le lancement à la main ;
- durées médianes des 10 derniers passages réussis (API, 27/11) : Render 141 s, Check 44 s, Version 50 s, Pages 30 s, Preview 22 s, Release 12 s ;
- la demande de version n'a pas d'aperçu : Preview saute ses jobs pour une demande ouverte par un robot (vu sur #54).

Le site en ligne n'est pas un instantané pur du dépôt : chaque jour, les mesures d'activité sont relues et ajoutées à la construction (`data/metrics.json`, ignoré par git ; l'historique est gardé sur la branche `history`). E1 porte donc sur les sources (code, textes, données, version) ; les mesures du jour se refont en lançant `scripts/refresh.py`.

## 2. Faits de GitHub qui décident

Recherche du 27/11 (sous-agent, pages lues le 27/11 sauf mention) ; ce qui n'est pas établi est dit tel.

- **Aucune fusion en avance rapide** (fast-forward) dans l'interface ni l'API des demandes : fusion avec commit, par écrasement ou « rebase and merge », qui réécrit les empreintes des commits ([documentation, méthodes de fusion](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github)) ; demande ouverte depuis le 13/07/2021, sans réponse de GitHub ([discussion 4618](https://github.com/orgs/community/discussions/4618)). Seule voie : `git push origin next:main` depuis un workflow ou une console ; Git le refuse si `main` a bougé ([eScience Center, 21/02/2025](https://blog.esciencecenter.nl/posts/2025-02-21---fast-forward-merges-on-github)).
- **Écrasement entre deux branches longues** : les commits écrasés n'entrent jamais dans l'historique de la cible, les deux branches divergent et chaque passage suivant reconflit, sauf fusion en retour ou avance rapide ([discussion 23249](https://github.com/orgs/community/discussions/23249)).
- **Rulesets** (gratuits sur un dépôt public) : « Restrict updates » réserve les poussées aux acteurs de la liste de contournement ; une application GitHub peut y figurer ; le jeton `GITHUB_TOKEN` d'un workflow n'y est mentionné nulle part (non établi) ([règles disponibles](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)). Combinaison « Restrict updates » et historique linéaire avec une application en contournement : non documentée, déduite ; **à vérifier en premier** si ce modèle est retenu.
- **Jeton et événements** : ce qui est fait avec `GITHUB_TOKEN` ne lance pas d'autre workflow, sauf `workflow_dispatch` et `repository_dispatch` ; une demande ouverte avec le jeton d'une application lance bien les workflows `pull_request` ([documentation](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow) ; [peter-evans, guide](https://github.com/peter-evans/create-pull-request/blob/main/docs/concepts-guidelines.md)). L'application de Data fixes, qui ouvre déjà la demande de version, convient.
- **Passages planifiés** : toujours sur le dernier commit de la branche par défaut ; un passage quotidien qui doit construire autre chose doit le récupérer lui-même ([événements](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- **Pages depuis une étiquette** : possible si l'environnement `github-pages` l'autorise (motifs d'étiquettes depuis le 06/10/2023), mais hors du chemin documenté, avec des échecs rapportés ([changelog](https://github.blog/changelog/2023-10-06-actions-secure-deployment-rollouts-to-protected-environments-based-on-select-tag-patterns/) ; [discussion 39054](https://github.com/orgs/community/discussions/39054), dernier message du 13/01/2026).
- **Environnement à approbation** : relecteurs requis disponibles pour un dépôt public gratuit ; le seul mainteneur doit laisser « Prevent self-review » coupé ([environnements](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment)).
- **Renovate** : `baseBranchPatterns` (ancien `baseBranches`), par exemple `["next"]` ; la configuration se lit sur la branche par défaut ([documentation](https://docs.renovatebot.com/configuration-options/#basebranchpatterns)).
- **Changer la base d'une demande** : `PATCH /repos/{o}/{r}/pulls/{n}` avec `base` ([changelog de 2016](https://developer.github.com/changes/2016-08-23-change-base)), pas revu dans la référence actuelle ; l'événement produit est `pull_request` de type `edited`, absent des types par défaut ; relance des contrôles non documentée ([changer la base](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/changing-the-base-branch-of-a-pull-request)).
- **Téléchargement** : clone et « Download ZIP » prennent la branche par défaut (déduit, non écrit dans la page lue) ; la page Releases offre les sources de chaque étiquette ; `/releases/latest` est un lien stable documenté ([liens vers les versions](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)).
- **Pratiques** : release-please et changesets mettent la production sur une étiquette, la publication étant un workflow à part ([release-please](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md) ; [changesets](https://github.com/changesets/changesets/blob/main/docs/versioning-apps.md), page dite périmée) ; git-flow la met sur la branche `main`, étiquetée ; aucun projet nommé trouvé qui publie Pages depuis une étiquette.

Conséquence qui structure tout : sur GitHub, **la branche par défaut sert à la fois au téléchargement et de base par défaut aux demandes**. E1 veut que la branche par défaut soit la production ; la simplicité des contributions veut qu'elle soit la branche d'intégration. Aucun modèle n'échappe à ce choix : il se règle soit en redirigeant les demandes (modèle A), soit en renvoyant le téléchargement vers la page Releases (modèle B).

## 3. Trois modèles, notés sur les mêmes exigences

**Modèle A — deux branches, `next` pour intégrer, `main` pour la production (production = branche).**
- Les demandes (Romain, Claude, Renovate, Data fixes, Tidy, revue mensuelle) visent `next`, fusionnées par écrasement comme aujourd'hui. Les fragments restent (E3).
- Version ouvre la demande `vX.Y` vers `next` ; son aperçu est autorisé (garde-fou des robots levé pour la seule branche `auto/version`) : c'est `next` plus le numéro, exactement ce qui partira (E2).
- **Publier = fusionner la demande `vX.Y`**, le geste d'aujourd'hui. Un workflow Publish voit cette fusion sur `next`, attend `check` vert sur ce commit, puis avance `main` jusqu'à `next` (`git push origin next:main`, jeton de l'application). Pas de bouton dans l'onglet Actions, pas d'écrasement possible vers `main`.
- `main` reste la branche par défaut : clone, ZIP et dernière étiquette donnent la production (E1). Pages ne change pas : il construit déjà la branche par défaut, à la poussée, chaque jour et pour les aperçus (E8). Release étiquette `main` comme aujourd'hui (E7).
- Les commits de `main` sont ceux de `next` (mêmes empreintes) : Check et Render, déjà passés sur `next`, ne se relancent pas ; leurs déclencheurs passent de `main` à `next`.
- Ce qui vise `main` par erreur est rebasculé vers `next` par un petit workflow (API, sans lire le code de la demande), avec un commentaire.

**Modèle B — une branche `main`, production = dernière étiquette.**
- Demandes et fragments comme aujourd'hui ; la demande `vX.Y` gagne son aperçu ; sa fusion étiquette, puis Pages construit l'étiquette.
- Pages doit récupérer lui-même la dernière étiquette dans ses trois modes (poussée, quotidien, aperçus), et Release le relancer (une étiquette posée avec `GITHUB_TOKEN` ne lance rien).
- Clone et ZIP donnent `main`, en avance sur la production ; le README pointerait vers `/releases/latest` (E1 partiel).

**Modèle 0 — aujourd'hui (référence)**, avec la pastille « v4.8+ » proposée le 27/11 pour E7.

| Exigence | A (`next` + `main`) | B (étiquette) | 0 (aujourd'hui) |
|---|---|---|---|
| E1 téléchargé = en ligne | oui : clone, ZIP, Releases | partiel : Releases seulement ; clone et ZIP en avance | partiel : clone et ZIP oui, dernière version non |
| E2 aperçu de l'ensemble avant publication | oui : demande `vX.Y` | oui : demande `vX.Y` | non : tout est déjà en ligne à la fusion |
| E3 pas de conflit | oui : fragments ; `main` n'avance qu'en avance rapide | oui : fragments | oui : fragments |
| E4 durée d'une demande | inchangée (≈ 2 min 30) | inchangée | inchangée |
| E4 publication, après le clic | ≈ 1 min 30 : Check sur `next` (44 s), avance (≈ 10 s), Pages (30 s) | ≈ 1 min : Release (12 s), Pages (30 s) | ≈ 30 s, mais sans clic de version |
| E4 urgence, de la demande à l'écran | ≈ 5 à 6 min, deux clics | ≈ 5 min, deux clics | ≈ 3 min, un clic |
| E5 réplicable | oui ; rulesets décrits et posés par script | oui | oui |
| E6 rien à retenir | oui si `main` n'accepte que l'application (voir défaut A2) | oui | oui |
| E7 numéro = contenu | oui | oui | approché (pastille) |
| E8 activité quotidienne | oui, sans changement | oui, Pages récupère l'étiquette | oui |
| Coût de mise en place | 7 à 8 workflows, 2 rulesets, Renovate, documents | 3 workflows, README | une dizaine de lignes |
| Décisions réglées rouvertes | « pas de branche `dev` », « ruleset plus strict » | aucune | aucune |

Écarté :
- **git-flow complet** (branches de version et de correctif) : deux voies vers `main`, donc fusions en retour et conflits, ce que A évite en n'ayant qu'une voie.
- **Environnement à approbation** sur Pages : un portail, mais sans aperçu de l'ensemble ni téléchargement aligné ; ajoute une approbation à chaque passage quotidien.

## 4. Recommandation, défauts restants et parades

**Modèle A.** C'est le seul qui tienne E1 au sens de Romain (« quelqu'un qui passe par là » clone ou télécharge le ZIP) ; il ne change rien au geste de publication (fusionner `vX.Y`), il ne fait rien construire depuis une étiquette, et il supprime des contrôles redondants. B est plus léger et plus courant, mais laisse le clone en avance sur le site : c'est précisément le défaut relevé par Romain.

| N° | Défaut restant de A | Parade |
|---|---|---|
| A1 | Une urgence publie aussi tout ce qui attend sur `next` | `next` toujours publiable : chaque demande y arrive contrôlée et vue en aperçu ; un changement à retenir se retire par une demande d'annulation |
| A2 | Si Romain fusionne une demande dans `main` (contournement administrateur), `main` diverge et Publish échoue | `main` n'accepte que l'application (ruleset : historique linéaire, avance rapide, contournement réservé à l'application, administrateur retiré) ; c'est plus strict que le réglé « pas de ruleset plus strict » : **à décider** ; sinon Publish refuse, alerte et la réparation est écrite dans `MAINTENANCE.md` |
| A3 | Ce qui attend sur `next` dort tant que la version n'est pas fusionnée | la demande `vX.Y` ouverte rappelle ; alerte si `next` a plus de 7 jours d'avance |
| A4 | Les corrections de Data fixes (fragment `none`) attendent la version suivante | **à décider** : Data fixes passe en `minor` (un numéro par semaine), ou ses corrections attendent la revue mensuelle, toujours `minor` |
| A5 | Une demande extérieure ouverte sur `main` | rebasculée vers `next` par un workflow (jeton de l'application, type `edited` filtré sur le changement de base pour relancer les contrôles) ; `contributing.md` le dit |
| A6 | La combinaison « Restrict updates » et application en contournement n'est pas documentée | premier geste du lot : essai sur une branche jetable, avant toute bascule |
| A7 | La consigne de la revue mensuelle vise `main` | à recopier dans la tâche planifiée, sur demande explicite de Romain |
| A8 | La migration touche 7 à 8 workflows | un seul lot, à valider par Romain (déclencheurs, droits, rulesets) ; retour arrière : `next` supprimé, déclencheurs remis sur `main` |

## 5. Relecture contradictoire

(à écrire)
