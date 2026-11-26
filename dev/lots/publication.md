# Lot publication — numéro de version et CHANGELOG écrits à la fusion

*Maintainer's working notes, in French: brief of the release batch.*

Lignes : AL-49, AL-51, AL-63 de `dev/registre.md`. Proposé le 26/11 après la mesure des reprises (17 commits, 9 fusions en conflit sur les demandes #13 à #27, `dev/contexte.md`, section « Conflits »).

Principe : une demande ne touche plus `VERSION`, `CHANGELOG.md`, `README.md`, `full-list.md` ni les images du README ; elle dépose `changes/<branche>.md` (type : majeure, mineure ou aucune ; entrée de deux phrases). Après la fusion, un workflow assemble les fragments, monte la version, reconstruit les fichiers générés et l'image du README, commite sur `main` avec l'application de Data fixes, puis Release étiquette. Prérequis de Romain : ajouter l'application aux exceptions du ruleset de `main`. À prévoir : l'aperçu montre la version d'avant ; `Check` contrôle le fragment au lieu de l'entrée du CHANGELOG.

Avec : AL-51 (Render, polices installées sans `--with-deps`, deux jobs parallèles, à mesurer) et AL-63 (`lockFileMaintenance` de Renovate, une demande de plus par semaine). Relecture : complète Opus (change la façon de publier).
