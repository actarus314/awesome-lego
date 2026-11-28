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
- **Synthèse**, en deux variantes à comparer : A (d908d82, brique à côté de l'ouverture) et B (a5e8814, les quatre rectangles de chiffres de l'accueil à côté de l'ouverture, « Pourquoi 3001 » en section à part, phrase d'ouverture sans chiffres pour ne pas les redire) ; reprises après la relecture Opus : A en 21c23c7, B en e8be8a0.

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

## Choix de Romain (28/11/2026, vocal de 08 h 50 à 09 h 13, devant les aperçus côte à côte)

- Variante **A** gardée (la brique et les chiffres en gras dans la phrase d'ouverture) ; B retirée.
- Les **40 pays et 25 langues en gras** aussi dans la phrase d'ouverture.
- L'**espace vide autour du titre** « À propos de l'annuaire » fait beaucoup pour la facilité de lecture : à garder.
- « **Participer** » : les quatre encarts retirés, retour aux liens dans le texte, sur le fond de la page.
- **Fond de carte du tableau et de la plaque en thème sombre seulement** : sur fond clair, ils se lisaient bien sans ; en sombre, la page sans bloc était presque noire. Fait par une couleur `light-dark()` et une ombre autour du bloc, pour que rien ne bouge d'un thème à l'autre.
- **Cinq étapes** : les cinq points numérotés « ne servent pas à grand-chose » ; deux versions à comparer : la version 1 (c5c30f4), une pile qui gagne une brique à chaque étape (une sous l'autre sur téléphone), et la version 2 (1684e26), sans rangée d'étapes, le paragraphe racontant le chemin d'une fiche (comme la retouche 1).

## Choix de Romain (28/11/2026, vocal de 09 h 40 à 09 h 57)

- **Cinq étapes** : seule la rangée change entre les versions 1 et 2 ; le fond du problème, le bloc « Comment est fait l'annuaire » redit en partie le tableau. Il est **remplacé** : soit une seule phrase (964b5db), soit un **schéma en briques**, simple et exact, avec d'autres pièces que la 2×4, et au plus une ligne de texte qui dit autre chose (4bc86ba). Le tableau reste à part.
- Schéma fait : quatre petites constructions dans la projection de la brique 3001 du pied de page (`way()` de `scripts/build.py`, proportions réelles : tenon 4.8 × 1.7 mm, brique 9.6 mm, plaque et tuile 3.2 mm) : pièces en vrac (chercher), une brique sur trois plaques (lire à la source, 1 à 3 sources), la brique posée sur la plaque de sa catégorie (écrire la fiche), trois tuiles imprimées site, liste, flux (construire) ; tenons cachés sous une pièce non dessinés, un seul tenon en symbole (poids). La vérification « à chaque changement » reste au tableau, pour ne pas la redire.
- **Légende « un tenon par ressource » retirée** (évidente), et « longueurs proportionnelles » du téléphone avec elle, de même nature.
- **Phrase « L'annuaire renvoie aux listes… » déplacée** sous la plaque, au-dessus des trois blocs chiffrés.
- Passe sur le texte qui ne sert à rien : les deux légendes ci-dessus et l'ancien paragraphe de méthode ; signalé à Romain, non coupé : la phrase déplacée redit en partie les trois blocs qu'elle annonce.

## Vérifications

- Relecture Opus en contexte neuf des deux demandes (28/11) : #61, trait parasite des `details` du site sous les listes, phrase de `contributing.md` qui citait BrickLink et `access` (catégorie sans `access`), fragment faux pour B, colonne étroite de B à 320 px, cotes illisibles de la brique réduite ; #62, remontée dans `main` sans base commune, aucun garde-fou de durée, chiffre faux de MAINTENANCE.md, tests manquants, tête nommée par un commit de notes : tout corrigé ; laissés : critères du rang écrits sur la page seulement (déjà dans la version publiée), sémantique de tableau sous Safari avec des lignes en flex, contraste des tenons jaunes sur la plaque (chiffres dans le libellé et le texte).

- Versions phrase et schéma (28/11, 10 h) : contrôles du dépôt passés, captures 1280, 375 et 320 px, clair et sombre ; test `test_way_draws_each_step_at_one_scale` ; budget des pages À propos remesuré (70148 et 71013 octets) ; écart de la note sous la carte sombre corrigé au passage.
- Contrôles du dépôt à chaque commit (`build.py --check`, tests, `hygiene.py`, `check_site.py` avec et sans `--dejavu`) ; captures à 1280 et 390 px, clair et sombre, éléments du téléphone isolés.
- `--dejavu` a trouvé un débordement de la colonne « Par qui » à 320 px (variante A) : lignes du tableau en flex sur téléphone.
