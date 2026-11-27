# Awesome LEGO — lignes closes du registre

*Maintainer's working notes, in French: closed items of `dev/registre.md`.*

Lignes closes de `dev/registre.md`, la plus récente en tête ; un identifiant n'existe qu'une fois sur les deux fichiers ; AL-66 n'a jamais été attribué. Le détail des lignes closes avant le 26/11/2026 est dans le journal gelé du projet claude.ai « lego » (claude/archive/awesome-lego-journal-2026-11-26.md, section « Ouvert »).

| ID | P | Objet | Statut |
|---|---|---|---|
| AL-69 | P4 | Rangement de la racine dans `.github/` | abandonné : décision de Romain le 27/11 à 01 h 18 (gain faible, liens extérieurs cassés) |
| AL-54 | P4 | Notes des versions GitHub v1.0 à v4.2 encore longues | fait 27/11 : demande #33 (Release remet les notes de chaque version à son entrée de `CHANGELOG.md` à chaque changement de celui-ci) fusionnée à 01 h 09 ; Release lancé à la main par Claude à 01 h 10 : 14 versions reprises (v4.0 : 7854 → 551 signes), plus aucun écart à 01 h 11 |
| AL-70 | P3 | Règle Renovate qui retient le Python de `tidy.yml` sous 3.14 (pyoxipng 9.1.1 n'a de roue que pour Python 3.13, vérifié le 27/11 à 01 h 02) | fait 27/11 : accord de Romain à 01 h 03, demande #32 fusionnée à 01 h 07 (`renovate.json`, `MAINTENANCE.md`, section Tidy) |
| AL-55 | P4 | Branche `v4.3` poussée par erreur le 26/11 | fait 27/11 : supprimée par Romain ; absente de la liste des branches du dépôt à 01 h 08 |
| AL-34 | P3 | Application « Claude Design Import » installée sur le dépôt, usage inconnu | fait 27/11 : retirée par Romain (dit par Romain à 01 h 06, non revérifié : la session ne lit pas les installations) |
| AL-50 | P3 | Gardes-fous mécaniques (skill `audit-depot`) | fait 27/11 : demande #31 fusionnée à 01 h 03 (d63bc99) : `scripts/hygiene.py` dans Check (ruff, vulture, chaînes et champs non lus, `timeout-minutes` et `concurrency`, budgets de poids), barre et champs du téléphone et CSS mort dans Render, calibrés sur `tests/phone-fixture.html`, workflow Tidy du lundi ; relecture Sonnet : 2 bloquants et 8 à corriger, corrigés en 0ba4d35 ; veille : AL-71 ; règle Renovate du Python de Tidy : AL-70 |
| AL-52 | P3 | Cartes de skills du 26/11 (document-versionne, interface-outil, audit-depot, passation, correction de citation de document-versionne) | fait 27/11 : toutes enregistrées par Romain (vues dans la copie synchronisée à 01 h 05) |
| AL-67 | P2 | Lignes RM du registre invisibles pour la revue mensuelle | fait 26/11 : consigne de `dev/consigne-revue.md` (lecture de `CLAUDE.md`, `dev/contexte.md` et des lignes RM, version seule si aucune autre demande ne la porte, devenir des lignes RM dans la demande) recollée dans la tâche à 23 h 31 sur « Mets la consigne à jour » de Romain ; l'ancienne copie du projet claude.ai renvoie désormais ici |
| AL-48 | P2 | Où vivent contexte, registre et cahiers | fait 26/11 : `dev/` du dépôt, en français (décision de Romain, 23 h 13), demande #29 fusionnée à 23 h 26 ; reste à Romain : la ligne des instructions du projet claude.ai qui désigne claude/awesome-lego.md |
| AL-56 | P2 | v4.3, demande #28 : marque dépliée, filtres gardés ouverts, résultats par catégorie, passe d'optimisation, CHANGELOG court | fait v4.3 : fusionnée par Romain le 26/11 à 23 h 04 (c912e1f) ; Release v4.3 créée ; Check, Render, Pages, CodeQL, zizmor verts sur c912e1f ; site servi en v4.3 et aperçu #28 retiré (vérifiés à 23 h 08) |
| AL-31 | P3 | Façon de travailler (commit direct, demandes avec aperçu, pas de branche `dev`) | fait v4.3 : branche `dev` et déclencheur `delete` des aperçus retirés |
| AL-33 | P3 | Cartes des skills `document-versionne` et `interface-outil` du 25/11 | fait 26/11 : enregistrées par Romain (vues dans la copie synchronisée) ; les cartes du 26/11 sont AL-52 |
| AL-47 | P2 | Demande #27 (v4.2, titre des pages À propos) | fait v4.2 |
| AL-44 | P4 | Libellé du filtre « ★ Sélection » | abandonné : gardé tel quel par Romain le 26/11 à 8 h 58 |
| AL-42 | P2 | Passe UX, changements de structure S1 à S6, Q11, Q13 | fait v4.0 |
| AL-41 | P2 | Demande #25 (page À propos) | fait v4.1 |
| AL-39 | P2 | Render de la #24 bloqué | fait v4.0 : cause (polices au miroir Ubuntu lent) corrigée par la #26 |
| AL-37 | P3 | Consigne v4.0 de la revue mensuelle | fait 25/11 : recollée dans la tâche |
| AL-36 | P3 | Consigne de la revue mensuelle dans la tâche | fait 25/11 |
| AL-32 | P3 | Demande #20 (zizmor, Scorecard) | fait 25/11 : fusionnée |
| AL-30 | P4 | Statistiques de visite | abandonné : aucune pour l'instant (Romain, 25/11 à 11 h 30) ; signal pour rouvrir : une décision qui attend un chiffre |
| AL-29 | P3 | Demande #18 | fait v3.4 |
| AL-28 | P3 | Public visé et phrase d'accroche | fait v4.0 |
| AL-27 | P3 | Image du README | fait 25/11 : #21 fusionnée |
| AL-26 | P3 | Demande #17 | fait v3.5 |
| AL-25 | P3 | Demande #16 | fait v3.2 |
| AL-23 | P4 | Axe de « Dernier signe de vie » sur téléphone | fait v4.0 |
| AL-21 | P3 | Sélection du README après les rangs | fait v3.2 |
| AL-20 | P3 | Gestes d'après fusion du lot 3c | fait v3.1 |
| AL-17 | P3 | Consigne de la revue mensuelle | fait 25/11 |
| AL-16 | P3 | Décisions issues des audits du 24/11 | fait v3.2 |
| AL-12 | P4 | Quota Perplexity épuisé le 23/11 | abandonné : sans objet |
| AL-11 | P4 | Dépôt lego en anglais | abandonné : propre au Carnet de briques, renvoyé à son contexte |
| AL-10 | P3 | Contributions en anglais seulement | fait v3.2 |
| AL-07 | P3 | Licences | fait v3.0 |
| AL-04 | P3 | BrickLink hors ligne | fait v3.2 |
| AL-02 | P4 | Soumission à l'index awesome | abandonné : Romain, 24/11 à 11 h 02 |
