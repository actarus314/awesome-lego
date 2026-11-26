# Lot entretien — petits correctifs laissés par l'audit du 26/11

*Maintainer's working notes, in French: brief of the maintenance batch.*

Lignes : AL-57, AL-62, AL-59, AL-60, AL-61, AL-64, AL-22, AL-46 de `dev/registre.md`. Après le lot gardes-fous, dont les contrôles trouveront une partie de ce travail. Version mineure si le site change (champs de récurrence affichés, données plus légères), sinon sans numéro.

À décider dans le lot : AL-57, afficher la récurrence d'un événement (« chaque année en juin ») sur sa carte, ou retirer `recurrence_en` et `recurrence_fr` du schéma ; proposition de Claude : l'afficher, puisque 68 fiches la portent et que la revue la tient à jour.

Le reste se fait sans décision : droits de `fixes.yml` séparés par job (AL-62) ; `sources` dans `details.json` (AL-59, à garder seulement si le gain dépasse 10 % sur `scripts/measure_speed.py`, décision du 24/11) ; `data/metrics.json` ignoré par git ou rafraîchi (AL-60) ; doublons entre scripts (AL-61) ; adresses héritées avec une date de retrait, `measure_speed.py` documenté (AL-64) ; `tests/links-sample.json` (AL-22) ; mineurs d'AL-46 qu'un usage a montrés.

Relecture : ciblée Sonnet.
