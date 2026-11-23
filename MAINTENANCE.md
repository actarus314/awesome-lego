# Maintenance

[English](#english) · [Français](#français)

## English

| What | How | When | Who decides |
|---|---|---|---|
| Activity dates, GitHub stars, archived repositories | `scripts/refresh.py` reads the GitHub API, YouTube channel feeds, subreddit feeds and site feeds into `data/metrics.json` | weekly workflow **Refresh metrics**, as a pull request | the maintainer merges |
| Selection of the best (`featured`) | the refresh pull request lists selected entries that are no longer eligible (no activity for 6 months, archived, weak source) | weekly | the maintainer, with a review pass |
| Broken links | lychee over `data/` and the README files | weekly workflow **Links**, opens an issue | the maintainer |
| Statuses on the site | computed from the last activity date at each build | weekly rebuild of **Pages** | automatic |
| Facts, new resources, selection | review pass with a language model, category by category: every entry read at its source, missing resources searched, `featured` reassessed; result as a pull request with a report | each quarter, and before a submission to the awesome index | the maintainer merges |
| Entries not checked by hand for a year | listed in the refresh pull request | weekly | review pass |

Generated files (`README.md`, `README.fr.md`, `full-list.md`, `liste-complete.md`, `site/`) come from `data/` through `scripts/build.py`; the **Check** workflow fails when they are out of date.

## Français

| Quoi | Comment | Quand | Qui décide |
|---|---|---|---|
| Dates d'activité, étoiles GitHub, dépôts archivés | `scripts/refresh.py` lit l'API GitHub, les flux des chaînes YouTube, des sous-reddits et des sites, et écrit `data/metrics.json` | workflow hebdomadaire **Refresh metrics**, en demande de fusion | la personne qui maintient fusionne |
| Sélection du meilleur (`featured`) | la demande de fusion hebdomadaire liste les entrées sélectionnées qui ne sont plus éligibles (sans activité depuis 6 mois, archivées, source faible) | chaque semaine | la personne qui maintient, avec une passe de revue |
| Liens morts | lychee sur `data/` et les README | workflow hebdomadaire **Links**, qui ouvre un ticket | la personne qui maintient |
| Statuts sur le site | calculés depuis la date de dernière activité à chaque construction | reconstruction hebdomadaire de **Pages** | automatique |
| Faits, nouvelles ressources, sélection | passe de revue par un modèle de langage, catégorie par catégorie : chaque entrée relue à sa source, ressources manquantes cherchées, `featured` réévalué ; résultat en demande de fusion avec un rapport | chaque trimestre, et avant une soumission à l'index awesome | la personne qui maintient fusionne |
| Entrées non vérifiées à la main depuis un an | listées dans la demande de fusion hebdomadaire | chaque semaine | passe de revue |

Les fichiers générés (`README.md`, `README.fr.md`, `full-list.md`, `liste-complete.md`, `site/`) viennent de `data/` par `scripts/build.py` ; le workflow **Check** échoue s'ils ne sont pas à jour.
