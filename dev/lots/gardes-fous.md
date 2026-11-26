# Lot gardes-fous — outillage mécanique de la skill `audit-depot`

*Maintainer's working notes, in French: brief of the batch that sets up mechanical guards.*

Demande de Romain du 26/11/2026 : « je pensais à des gardes-fous et optimisateurs mécaniques » (22 h 10), puis « mettre en place l'outillage pour audit-depot » (23 h 29). Ligne : AL-50 de `dev/registre.md`. Lot sans numéro de version (automatisation), demande de fusion séparée de toute demande qui porte `VERSION`.

## Objet

Ce que l'audit Opus du 26/11 a trouvé à la main et qu'un script sait voir devient un contrôle qui échoue à chaque demande, avec un message qui dit quoi corriger. Rien de probabiliste.

## Contrôles (Check, `scripts/hygiene.py`, rapide)

1. Python : `ruff check` (règles F et E9 : noms inutilisés, imports, erreurs de syntaxe) et `vulture` (code mort, confiance 80 % ou plus) sur `scripts/` et `tests/`, outils épinglés par empreinte dans `tests/requirements-check.txt`.
2. Chaînes de `site-src/strings.json` jamais lues par `app.js`, `header.js`, les gabarits HTML ou `build.py` (les préfixes lus par composition, `st_`, `acc_`, `u_`, `fu_`, `aud_`, `sz_`, `in_lang`, etc., sont déclarés une fois dans le script).
3. Champs de données envoyés à la page et jamais lus par `app.js` (généralise le test de la v4.3).
4. Workflows : chaque job a `timeout-minutes` ; chaque workflow déclenché par `pull_request` qui construit ou contrôle a un groupe `concurrency`.
5. Budgets de poids : `site/index.html`, `site/fr/index.html`, `details.json`, pages À propos, avec leur valeur mesurée et une marge écrites dans `tests/budgets.json` (date de la mesure) ; relever un budget demande une raison écrite dans la demande.

## Contrôles du rendu (Render, `scripts/check_site.py`)

6. Barre de recherche : au plus 2 lignes à 320 px dans chaque langue (sans filtre actif).
7. Champs de saisie et listes : 16 px au moins sous 641 px.
8. CSS : règle dont aucun sélecteur ne s'applique dans aucune vue ni aucun état contrôlé (couverture CSS de Chromium) ; les états non visités se déclarent dans le script.

## Correcteurs (hebdomadaires)

9. Workflow `tidy.yml`, chaque lundi : `ruff --fix`, compression sans perte des PNG de `media/` (`oxipng`), puis une demande « Tidy » par l'application de Data fixes, seulement s'il y a une différence ; ni numéro de version ni fusion automatique.

## Critères de correction (règle « Critère de correction écrit d'avance » de passation)

Se corrigent dans le lot les constats qui touchent ces contrôles, l'étalon (chaque contrôle échoue sur un défaut posé exprès et passe sur `main`) ou une régression ; le reste suit l'étape 3 de la clôture.

## Vérification

Chaque contrôle échoue sur un cas posé exprès (tests dans `tests/test_hygiene.py`) et passe sur `main` ; ce qu'il trouve sur `main` le jour de sa pose est corrigé dans le lot ou écrit en exception avec sa raison. Relecture : ciblée Sonnet. Mises à jour : `MAINTENANCE.md` (section Check et Render, workflow Tidy), `CLAUDE.md` si une règle change.
