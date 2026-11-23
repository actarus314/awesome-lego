# Contributing / Contribuer

[English](#english) · [Français](#français)

## English

This list aims to be complete, accurate and current. Every entry is checked at its source and written in English and French.

**Suggest without editing files:** open an issue with the [Add a resource](../../issues/new?template=add-resource.yml) or [Fix an entry](../../issues/new?template=fix-entry.yml) form. A maintainer writes the entry.

**Edit the data yourself:**
1. Edit the TOML file of the category in [`data/`](data/), following [`data/SCHEMA.md`](data/SCHEMA.md). `README.md`, `README.fr.md`, `full-list.md`, `liste-complete.md` and `data/metrics.json` are generated: do not edit them by hand.
2. Run `python3 scripts/build.py` (Python 3.11 or later, no dependency) and commit the regenerated files with the data.
3. Open a pull request. Checks validate the data, build the site and test the links.

**Selection:** the README lists only entries marked `featured = true`, the best of each group; the [full list](full-list.md) keeps every entry, inactive and dead ones included. See [MAINTENANCE.md](MAINTENANCE.md).

**What gets in:** resources useful to adult builders of official LEGO or compatible bricks, publicly reachable, active or still a reference. Shops must state their delivery terms; brands must have an official site. Each entry needs at least one source with a date.

**What stays out:** affiliate or referral links, link shorteners, pages that require an account to read, copies of copyrighted instructions, sellers of counterfeit sets presented as official LEGO, self-promotion without substance.

**Writing:** factual and short, no marketing words; decimal point, no thousands separator; prices including taxes; no abbreviations except proper names and technical terms.

By contributing, you agree that your contribution is published under the licenses of the repository (content: CC BY-NC-SA 4.0; code: PolyForm Noncommercial 1.0.0). Everyone follows the [code of conduct](CODE_OF_CONDUCT.md).

## Français

Cette liste se veut complète, exacte et à jour. Chaque entrée est vérifiée à sa source et rédigée en anglais et en français.

**Proposer sans toucher aux fichiers :** ouvrir un ticket avec le formulaire [Ajouter une ressource](../../issues/new?template=add-resource.yml) ou [Corriger une entrée](../../issues/new?template=fix-entry.yml). L'entrée est rédigée par la personne qui maintient le dépôt.

**Modifier les données soi-même :**
1. Modifier le fichier TOML de la catégorie dans [`data/`](data/), selon [`data/SCHEMA.md`](data/SCHEMA.md). `README.md`, `README.fr.md`, `full-list.md`, `liste-complete.md` et `data/metrics.json` sont générés : ne pas les modifier à la main.
2. Lancer `python3 scripts/build.py` (Python 3.11 ou plus, sans dépendance) et commiter les fichiers régénérés avec les données.
3. Ouvrir une demande de fusion (pull request). Les contrôles valident les données, construisent le site et testent les liens.

**Sélection :** le README ne liste que les entrées marquées `featured = true`, le meilleur de chaque groupe ; la [liste complète](liste-complete.md) garde toutes les entrées, inactives et mortes comprises. Voir [MAINTENANCE.md](MAINTENANCE.md).

**Ce qui entre :** les ressources utiles aux adultes qui construisent en LEGO officiel ou en briques compatibles, accessibles publiquement, actives ou restées une référence. Une boutique publie ses conditions de livraison ; une marque a un site officiel. Chaque entrée porte au moins une source datée.

**Ce qui reste dehors :** liens d'affiliation ou de parrainage, raccourcisseurs d'adresses, pages lisibles seulement avec un compte, copies d'instructions protégées, vendeurs de contrefaçons présentées comme du LEGO officiel, autopromotion sans contenu.

**Rédaction :** factuelle et courte, sans mots de vente ; point décimal, sans séparateur de milliers ; prix taxes comprises ; pas d'abréviations hors noms propres et termes techniques.

Contribuer vaut accord pour publier la contribution sous les licences du dépôt (contenu : CC BY-NC-SA 4.0 ; code : PolyForm Noncommercial 1.0.0). Le [code de conduite](CODE_OF_CONDUCT.fr.md) s'applique à tous.
