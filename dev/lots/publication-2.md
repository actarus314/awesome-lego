# Lot publication 2 — ce qui est en ligne est ce qui se télécharge

**Décision de Romain (27/11, 23 h 03)** : modèle C, avec une numérotation à trois niveaux (le troisième chiffre seulement s'il n'est pas nul), pour l'annuaire et pour toutes les skills. Un lot est une demande ; la demande `vX.Y` disparaît. Mise en œuvre : demande « publish-c ».

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
- **Passages planifiés et `workflow_run`** : toujours avec le fichier de workflow de la branche par défaut (Pages quotidien, Links, Data fixes, Tidy, Fuzzing, Scorecard) ; un passage qui doit construire autre chose doit le récupérer lui-même ; un correctif de workflow n'agit qu'une fois sur la branche par défaut ([événements](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)).
- **Pages depuis une étiquette** : possible si l'environnement `github-pages` l'autorise (motifs d'étiquettes depuis le 06/10/2023), mais hors du chemin documenté, avec des échecs rapportés ([changelog](https://github.blog/changelog/2023-10-06-actions-secure-deployment-rollouts-to-protected-environments-based-on-select-tag-patterns/) ; [discussion 39054](https://github.com/orgs/community/discussions/39054), dernier message du 13/01/2026).
- **Environnement à approbation** : relecteurs requis disponibles pour un dépôt public gratuit ; le seul mainteneur doit laisser « Prevent self-review » coupé ([environnements](https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-deployments/managing-environments-for-deployment)).
- **Renovate** : `baseBranchPatterns` (ancien `baseBranches`), par exemple `["next"]` ; la configuration se lit sur la branche par défaut ([documentation](https://docs.renovatebot.com/configuration-options/#basebranchpatterns)).
- **Changer la base d'une demande** : `PATCH /repos/{o}/{r}/pulls/{n}` avec `base` (présent dans la référence actuelle « Update a pull request », relu par la relecture du 27/11) ; l'événement produit est `pull_request` de type `edited`, absent des types par défaut ; relance des contrôles non documentée ([changer la base](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/changing-the-base-branch-of-a-pull-request)).
- **Téléchargement** : clone et « Download ZIP » prennent la branche par défaut (déduit, non écrit dans la page lue) ; la page Releases offre les sources de chaque étiquette ; `/releases/latest` est un lien stable documenté ([liens vers les versions](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)).
- **Pratiques** : release-please et changesets mettent la production sur une étiquette, la publication étant un workflow à part ([release-please](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md) ; [changesets](https://github.com/changesets/changesets/blob/main/docs/versioning-apps.md), page dite périmée) ; git-flow la met sur la branche `main`, étiquetée ; aucun projet nommé trouvé qui publie Pages depuis une étiquette.

Conséquence qui structure tout : sur GitHub, **la branche par défaut sert à la fois au téléchargement et de base par défaut aux demandes**. E1 veut que la branche par défaut soit la production ; la simplicité des contributions veut qu'elle soit la branche d'intégration. Deux modèles le tranchent (A redirige les demandes, B renvoie le téléchargement vers la page Releases) ; le modèle C, trouvé par la relecture, l'évite : une seule branche, et chaque fusion devient aussitôt une version publiée.

## 3. Quatre modèles, notés sur les mêmes exigences

**Modèle C — une branche, chaque fusion est une version publiée (ajouté après la relecture contradictoire du 27/11).**
- Une seule branche `main`, par défaut ; les demandes la visent comme aujourd'hui ; les fragments restent (E3).
- Après chaque fusion, Version écrit directement sur `main` le commit numéroté (`VERSION`, `CHANGELOG.md`, README, liste, images), avec l'application de Data fixes placée dans la liste de contournement du ruleset ; Release l'étiquette. Ce passage est déjà décrit dans `MAINTENANCE.md` (« To write on `main` directly instead ») ; la garde de Version contre deux fusions rapprochées existe (`version.yml`, « main moved outside dev/ ») : la fusion suivante attend et une seule version couvre les deux.
- **Pages ne publie à la poussée que le commit de Version** (celui qui change `VERSION`) ; le passage quotidien publie toujours l'état de `main` (activité, E8). Le site affiche donc toujours un état numéroté, étiqueté, identique au clone.
- Une fusion qui change le site sans fragment numéroté (Data fixes, Renovate d'un paquet servi par le site comme MiniSearch) reçoit un numéro de correctif (`4.9.1`) ; l'automatisation et les notes seules ne changent rien en ligne et n'en reçoivent pas.
- **L'aperçu de chaque demande est construit sur sa fusion avec `main`** (le commit de fusion que GitHub calcule), et refait à chaque poussée sur `main` : c'est exactement ce que sa fusion mettra en ligne (E2). Valider la nouvelle version, c'est fusionner la demande : un clic, pas deux ; la demande `vX.Y` et la tâche « Accept vX.Y » disparaissent.

**Modèle A — deux branches, `next` pour intégrer, `main` pour la production.** Les demandes visent `next` ; Version ouvre `vX.Y` vers `next` ; sa fusion déclenche Publish, qui avance `main` en avance rapide avec l'application ; Pages et Release ne changent pas ; ce qui vise `main` est rebasculé.

**Modèle B — une branche `main`, production = dernière étiquette.** Demandes et fragments comme aujourd'hui ; la demande `vX.Y` gagne son aperçu ; sa fusion étiquette ; Pages, lancé sur `main`, récupère lui-même l'étiquette dans ses trois modes. Clone et ZIP restent en avance sur le site.

**Modèle 0 — aujourd'hui (référence)**, avec la pastille « v4.8+ » proposée le 27/11 pour E7.

| Exigence | C (chaque fusion publiée) | A (`next` + `main`) | B (étiquette) | 0 (aujourd'hui) |
|---|---|---|---|---|
| E1 téléchargé = en ligne | oui, sauf la minute entre une fusion et son commit de version, où le clone a un commit d'avance | oui | partiel : Releases seulement | partiel : clone oui, dernière version non |
| E2 aperçu de ce qui part en ligne | oui : chaque demande, construite sur sa fusion avec `main` | oui : demande `vX.Y`, par lot | oui : demande `vX.Y`, par lot | non |
| E3 pas de conflit | oui : fragments, Version seul à écrire les fichiers de version | oui, si `main` n'avance qu'en avance rapide | oui | oui |
| E4 demande ordinaire | inchangée (≈ 2 min 30) | inchangée | inchangée | inchangée |
| E4 urgence, de la demande à l'écran | ≈ 4 min, un clic | ≈ 5 à 6 min, deux clics | ≈ 5 min, deux clics | ≈ 3 min, un clic |
| E5 réplicable | oui ; une entrée de ruleset décrite et posée par script | oui ; deux rulesets, Renovate | oui | oui |
| E6 rien à retenir | oui : aucune règle d'ordre ni de branche | non sans parades : `--base next`, jamais de demande de `next` vers `main`, attendre Version, notes sur `next` | partiel : « attendre la fin de Version » reste | partiel : idem |
| E7 numéro = contenu | oui | oui | oui | approché |
| E8 activité quotidienne | oui | oui | oui | oui |
| Coût | 4 à 5 fichiers (Version, Pages, Preview, Check, `changes.py`) et une entrée de ruleset | 8 à 10 fichiers, 2 rulesets, Renovate, règles de session | 3 workflows, README | dix lignes |
| Décisions réglées rouvertes | « rien pour l'automatisation » ne change pas ; un numéro de correctif est neuf | « pas de branche `dev` », « ruleset plus strict » | aucune | aucune |

Écartés : **git-flow complet** (deux voies vers `main`, donc fusions en retour) ; **environnement à approbation** sur Pages (portail sans aperçu d'ensemble, une approbation par passage quotidien) ; **B**, dominé par C (même machinerie d'étiquette, E1 et E6 moins bons) ; **0**, qui ne tient ni E1 ni E2.

## 4. Recommandation, défauts restants et parades

**Modèle C.** Il tient E1, E2 et E7 sans seconde branche, sans redirection et sans règle à retenir ; il retire un clic et une tâche récurrente à Romain (« Accept vX.Y ») ; il coûte le moins. Ce qu'il abandonne : le lot, c'est-à-dire retenir plusieurs fusions pour les regarder et les publier ensemble ; chaque fusion reste vue en aperçu dans l'état exact où elle partira. Si Romain veut ce lot, la voie est A, avec les corrections listées en section 5.

| N° | Défaut restant de C | Parade |
|---|---|---|
| C1 | Une minute entre une fusion et son commit de version : le clone a un commit d'avance sur le site | Pages ne publie que le commit de Version ; le décalage ne touche que le clone, une minute ; écrit dans `MAINTENANCE.md` |
| C2 | Si Version échoue (clé de l'application expirée, par exemple), la fusion reste sans numéro et le passage quotidien la publierait sans numéro | Version en échec ouvre un ticket ; le passage quotidien publie quand même (E8) et le dit dans son résumé ; la réparation est écrite dans `MAINTENANCE.md` |
| C3 | L'application écrit sur `main` sans demande | contournement réservé à cette application ; Version n'écrit que ses fichiers, après contrôle du correctif sans jeton (déjà en place) ; Check tourne sur ce commit après coup |
| C4 | Deux fusions rapprochées | la garde de Version fait publier le passage le plus récent ; une version couvre les deux ; l'aperçu de la seconde a été refait sur la première |
| C5 | Les aperçus doivent être refaits à chaque poussée sur `main` | Preview se relance à la poussée sur `main` pour les demandes ouvertes (≈ 20 s chacune) |
| C6 | Numéro de correctif neuf (`4.9.1`) ; l'automatisation et les notes n'en reçoivent pas, donc le clone peut avoir des commits de workflows ou de notes d'avance sur la dernière étiquette, sans effet sur le site | donné par Version seul, quand les fichiers servis par le site changent sans fragment numéroté ; écrit dans `MAINTENANCE.md` |
| C7 | Les demandes de Renovate et de Data fixes ont aussi leur aperçu, aujourd'hui sauté pour les robots | garde-fou levé pour les branches du dépôt (jamais pour une demande extérieure) |
| C8 | Combinaison du ruleset (historique linéaire, demande requise) avec une application en contournement : non documentée | premier geste du lot : un essai de poussée de l'application sur une branche jetable couverte par une copie du ruleset |

## 5. Relecture contradictoire

Relecture en contexte neuf (sous-agent Opus, 27/11, 21 h 05), chargée de casser le modèle A recommandé dans la première version de ce cahier ; ses constats, vérifiés sur les fichiers cités, et ce qu'ils ont changé :

| Constat | Gravité | Suite |
|---|---|---|
| A publierait une `vX.Y` périmée si Romain la fusionne pendant qu'une autre fusion relance Version (fusions à quelques minutes l'une de l'autre le 27/11) ; seul garde-fou : une règle à retenir | bloquant pour A | parade si A : Publish compare le commit fusionné à la tête de la demande ; sans objet en C |
| En A, seules les versions numérotées atteignent `main` : Renovate, Data fixes, Tidy, correctifs de workflows et de sécurité dorment sur `next`, alors que les passages planifiés lisent `main` | bloquant pour A | parade si A : une demande de publication dès que `next` diffère de `main` ; sans objet en C |
| La branche par défaut servirait à chaque session des consignes (`CLAUDE.md`, notes) plus anciennes que `next` | à corriger pour A | sans objet en C |
| Réflexe des deux branches : « Compare & pull request » de `next` vers `main`, écrasement, suppression de `next` (suppression des branches fusionnées active) | à corriger pour A | sans objet en C |
| Rebascule des demandes extérieures : `pull_request_target`, signalé par zizmor | à corriger pour A | sans objet en C |
| Le garde-fou des robots est à trois endroits (`preview.yml` deux fois, `previews.py`) ; les aperçus construisent la tête de la branche, pas sa fusion | à corriger | repris en C5 et C7 |
| Le cache des polices de Render n'est enregistré que depuis `main` | à corriger pour A | sans objet en C (Render reste sur `main`) |
| Le risque des déploiements Pages depuis une étiquette ne touche pas B, qui lance Pages sur `main` | équité | corrigé en section 3 |
| Les passages `workflow_run` lisent aussi la branche par défaut | fait | corrigé en section 2 |
| Modèle C : une seule branche, chaque fusion devient une version publiée | proposition | retenu, section 4 |

Verdict de la relecture : C, ou A avec les corrections de la colonne « Suite ». Ce cahier recommande C.
