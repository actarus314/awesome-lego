# Lot À propos — refonte de la page, aperçus par commit

*Maintainer's working notes, in French: brief of the about page redesign (demande #61) and of the previews per commit (demande #62).*

Lignes : AL-84 et AL-85 de `dev/registre.md`. Ouvert le 28/11/2026 à 04 h 08 (demande vocale de Romain : la page « fait trop IA généré », dans le fond comme dans la forme). Type : mineur (#61), aucun numéro (#62). Relecture : Opus en contexte neuf.

## Constat de départ (v4.10 en ligne)

- Toutes les informations y sont, mais la page est tassée, trop dense : chaque bloc dans une carte de même poids (quatre tuiles de chiffres, cinq cartes d'étapes reliées par des flèches, quatre cartes de rythme, trois jauges, quatre cartes de participation), barres jaunes sur chaque titre, étiquettes en majuscules à chasse fixe. Texte : redites (« le mainteneur accepte chaque correction » trois fois), formules toutes faites, énumération des onze catégories.
- Skill de création employée : `frontend-design` (ajoutée par Romain le 28/11).

## Historique des versions comparées par Romain (28/11, vocal de 05 h 00 à 05 h 50)

- **Publiée** : v4.10.
- **Retouche 1** (ec11f33) : plus de cartes, chiffres dans la phrase d'ouverture, tableau quand / par qui / quoi, plaque d'un tenon par ressource. Gardée en artefact : https://claude.ai/artifact/7iyeehCCmA4fUFGeTguyMt.
- **Retouche 2** (975b03a) : corrections de la relecture Opus (liens de « Participer » hors du clavier, pastilles fausses, faits imprécis).
- **Synthèse**, en deux variantes à comparer : A (d908d82, brique à côté de l'ouverture) et B (a5e8814, les quatre rectangles de chiffres de l'accueil à côté de l'ouverture, « Pourquoi 3001 » en section à part).

## Décisions de Romain (28/11/2026, vocal)

- Les deux retouches desserrent bien la page ; l'en-tête de la retouche 1 est préféré (chiffres en gras dans la phrase, ligne « Gratuit, sans publicité ni lien d'affiliation » à part). Brique ou quatre rectangles : pas d'avis arrêté, « tu me fais les 2 versions ».
- Date « Données du … » dans la police de l'accueil (oubli de la retouche 1 : rétablie, règle partagée avec `.hero .fresh`).
- Cinq étapes : visuellement appréciées ; un mélange avec le paragraphe : rangée légère de cinq étapes numérotées, sans cartes ni flèches, au-dessus du paragraphe.
- Tableau « Ce qui le tient à jour » : préféré, plus simple et plus clair.
- Plaque : « sympa, pas indispensable » ; la légende chiffrée de la retouche 2 crée la confusion (deux séries de trois chiffres) : légende sans chiffres.
- Listes « ce qui entre / ce qui reste dehors » : retirer l'évident (« utile pour construire à tout âge », « public ») ; la règle des pages lisibles seulement avec un compte peut écarter BrickLink ou Brickset : reformulée en « quelque chose d'utile lisible sans compte » (page) et dans `contributing.md` (une partie utile sans compte suffit, `access` le dit).
- « Être classé » : se lire au survol ; l'essentiel d'abord (les 5 meilleures, montrées dans « Par où commencer »), le poids du rang à la ligne, dans la même police (pas de texte plus petit : le défaut de la version publiée).
- « Participer » : les quatre encarts reviennent. Mode sombre : sans blocs, tout est presque noir, rien ne se détache du fond comme sur l'annuaire et l'Observatoire ; règle retenue : le texte reste sur le fond, ce qui se lit d'un coup d'œil ou se manipule (tableau, plaque, encarts) reprend un fond de carte.
- « Licences et marques » : bien mieux dans les deux retouches.
- **Petit écran** : ne pas régresser sur téléphone pour gagner sur grand écran ; le responsive avait été poussé plus loin que d'habitude (par exemple le bloc de l'Observatoire qui change de forme). Règle : **chaque bloc se conçoit à part pour le petit écran (une autre forme si besoin, pas une version plus petite), et se compare à la version publiée de 320 à 390 px, élément par élément.** Pour cette page : brique petite à côté du titre (A) ou du texte (B), bande unique en trois longueurs proportionnelles au lieu de la plaque, listes repliées par défaut sur téléphone et dépliées sans bouton sur grand écran (mécanisme de l'accueil), encarts compacts, étapes sans traits.
- **Aperçus par commit** (#62) : chaque commit d'une demande qui change le site garde son aperçu ; pas d'aperçu pour un commit qui ne change pas le site construit (notes, scripts, tests) ; dix au plus par demande, garde-fou qui ne devrait pas jouer ; supprimés à la fermeture comme aujourd'hui.
- Suite : le même audit pour l'annuaire et l'Observatoire (AL-86), avec la même règle du petit écran.

## Vérifications

- Contrôles du dépôt à chaque commit (`build.py --check`, tests, `hygiene.py`, `check_site.py` avec et sans `--dejavu`) ; captures à 1280 et 390 px, clair et sombre, éléments du téléphone isolés.
- `--dejavu` a trouvé un débordement de la colonne « Par qui » à 320 px (variante A) : lignes du tableau en flex sur téléphone.
