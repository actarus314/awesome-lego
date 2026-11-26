# Lot vitesse — chargement et première recherche

*Maintainer's working notes, in French: brief of the speed batch.*

Ligne : AL-58 de `dev/registre.md`. Mesuré par l'audit du 26/11 sur un téléphone ralenti 4 fois : 11895 éléments au chargement, tâche la plus longue de 422 à 485 ms ; index de recherche construit à la première prise de focus (358 à 423 ms). Pistes : dessiner la liste par catégorie au fil du défilement, construire l'index pendant que le navigateur est au repos. Gardé seulement si `scripts/measure_speed.py` mesure 10 % de gain ou plus (décision du 24/11) ; `openEntry`, le changement de langue et le retour du navigateur supposent aujourd'hui que toutes les cartes existent : à revoir avec. Version mineure. Relecture : ciblée Sonnet, captures à 320, 390 et 1440 px.
