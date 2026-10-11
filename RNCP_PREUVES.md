# RNCP37827BC01 — Index des preuves techniques

Ce document complète le rapport PDF remis au jury. Il distingue les preuves disponibles dans le code, les vérifications effectuées sur les données locales et les limites de reproductibilité d'un clone public.

| Compétence (consignes de formation) | Éléments du dépôt | Démonstration |
| --- | --- | --- |
| C1 — Collecter les données de manière automatisée | `src/collect_ebay.py`, `src/collect_google_trends.py`, `src/collect.py` | API eBay, Google Trends, parsing de fichiers HTML Chrono24 sauvegardés localement. |
| C2 — Préparer les données pour leur première utilisation | `src/prepare.py`, `src/prepare_ebay_attention.py` | Harmonisation de colonnes, conversion de prix, gestion des valeurs manquantes et préparation des entrées. |
| C3 — Mettre en œuvre des règles d’agrégation de données | `src/prepare_ebay_attention.py`, `notebooks/` | Agrégation par marque, rapprochement des indicateurs d'inventaire et d'attention. |
| C4 — Créer une base de données | `src/store.py`, `src/build_relational_model.py`, `docs/C4_modele_relationnel.md`, `docs/sql_queries.sql` | SQLite analytique et couche relationnelle complémentaire avec PK/FK ; requêtes SQL sur les données historiques. |
| C5 — Mettre à disposition les données via une API | `api/main.py`, `tests/`, `/docs` (Swagger local) | FastAPI, endpoints de lecture et rafraîchissement eBay. Vérifier la version du code déployée pour le contrôle d'accès du POST. |

## Vérifications sur données locales

- Jeu historique `Watches.csv` : **284 491 lignes** avant et après préparation ; **14 665** valeurs de prix non convertibles ou absentes après conversion (**5,15 %**) ; **43 152** références absentes.
- Échantillon eBay CSV examiné : **964 lignes**, toutes conservées dans le contrôle décrit dans le rapport, sans doublon d'`item_url` dans cet instantané.
- Rafraîchissement eBay distinct réalisé le **9 octobre 2026** : **925 annonces**. Ces deux chiffres ne correspondent pas à la même extraction.
- Requêtes sur `global_watch_market` dans la base SQLite locale : Rolex **68 798**, Omega **38 909**, Seiko **18 887**, Breitling **17 019**, Cartier **15 877** annonces avec prix valide.
- Les fichiers CSV historiques et les scripts de préparation utilisés pour ces contrôles étaient identiques dans les deux archives du **7 et du 9 octobre 2026** ; le fichier SQLite, lui, différait.

Les requêtes SQL reproductibles sont dans [`sql_queries.sql`](sql_queries.sql). Leurs résultats nécessitent la base SQLite locale correctement alimentée : la base et les CSV volumineux ne sont pas publiés dans le dépôt.

## Limites et lecture des indicateurs

- Les annonces ne constituent pas des transactions réalisées.
- Le classement de marques sur 15 marques et les KPI ciblés sur 8 marques n'ont pas le même périmètre.
- La couche relationnelle complémentaire contient trois tables et une ligne par marque dans l'instantané courant ; sa reconstruction requiert l'exécution explicite de `python src/build_relational_model.py` après mise à jour de SQLite.
- Les URL Rolex répétées à des dates différentes peuvent représenter des observations temporelles valides ; elles ne doivent pas être automatiquement confondues avec des doublons de lignes.
- Les prix catalogue Rolex proviennent d'une table tierce pouvant contenir plusieurs prix par référence ; les primes calculées restent exploratoires.

## Exécution et sécurité

Depuis la racine du dépôt, une fois les dépendances et données locales installées :

```bash
python src/store.py
python src/build_relational_model.py
python -m unittest discover -s tests -v
python -m uvicorn api.main:app --reload
```

Ne jamais versionner `.env`, les clés eBay ou la base SQLite locale. Le contrôle d'accès du POST `/refresh-ebay-market` doit être vérifié dans le code actuellement présent sur la branche soumise : les archives de travail et le dépôt distant peuvent différer.
