# Consigne commune — recherche « où vit chaque donnée d'un carnet idéal », étendue à tout le web

Date : 24/11/2026. Langue du rendu : français. Contexte : un « carnet » aide un adulte à choisir puis acheter un set de briques de construction pour adultes, de marque LEGO ou de marques alternatives (Mould King, CaDA, Cobi, Pantasy, Lumibricks, BlueBrixx, Reobrix, Xingbao…), livré en France.

Un recensement existe déjà : `/home/claude/awesome-lego-doc/carnet-donnees.md` (lis-le d'abord, en entier). Il a été fait seulement à partir d'un annuaire de 523 ressources et d'un inventaire. **Ta tâche : trouver, pour les données de ta famille (consigne propre ci-dessous), les sources qui n'y sont pas**, partout sur le web, et combler les lignes marquées ✗ ou ?.

## Ce qui compte comme source
- Toute ressource qui détient la donnée : site, base, API, fichier ouvert (CSV, JSON, Wikidata, Kaggle, Hugging Face, dépôt GitHub), flux, extension de navigateur, application, forum ou fil qui la tient à jour, fournisseur commercial de données, règle officielle.
- Couvre aussi les sources communautaires (forums, Reddit, X, issues et discussions GitHub, dépôts tiers, blogs, Discord indexé) : elles portent souvent les retours d'usage et les outils que l'officiel ne dit pas.
- Hors France aussi (Allemagne, Pays-Bas, Pologne, Chine, États-Unis), tant que la donnée sert un acheteur en France.

## Pour chaque source trouvée
Rends une entrée JSON :
`{"donnee": "...", "nom": "...", "url": "...", "ce_quelle_donne": "...", "acces": "ouvert|cle|payant|accord|page|inconnu", "conditions": "ce que disent les conditions sur la lecture automatique, si lu", "couvre": "LEGO|alternatives|les deux", "fraicheur": "date de la donnée ou de la page (AAAA-MM-JJ)", "verifie": true|false, "preuve": "ce que tu as lu, où", "rang": "officiel|lu-a-la-source|tiers|forum"}`
- `verifie: true` seulement si tu as lu la page ou la documentation dans cette recherche ; sinon `false` avec la raison.
- Une donnée sans aucune source après recherche : une entrée `{"donnee": "...", "aucune_source": true, "recherches": ["requêtes faites"]}`.

## Règles d'accès (impératives)
- Outils : WebSearch, et pour lire une page Exa (`web_fetch_exa`), Brave, Perplexity ; WebFetch peut être refusé aux sous-agents, passe alors à Exa. Relaie les outils si les résultats sont mauvais, sans relancer les mêmes requêtes sur chacun.
- Jamais de clé, jeton ou identifiant trouvé en chemin ; aucun contournement de défi anti-robot, de paywall ou de contrôle d'accès ; aucun mode furtif. Une page qui résiste se rend comme « résistante », sans contenu supposé.
- Ne crée aucun compte, ne remplis aucun formulaire.
- Une affirmation non lue se marque non vérifiée ; n'invente aucune source ni aucun chiffre.

## Rendu
- Écris le JSON (liste d'entrées) dans le fichier indiqué par ta consigne propre.
- Réponds en 300 mots au plus : les 5 trouvailles qui changent le plus le recensement (une donnée ✗ qui trouve une source, un accès ouvert là où l'on croyait qu'il fallait un accord), ce qui a résisté, et ton niveau de confiance.
- Budget : environ 40 recherches et lectures au plus.
