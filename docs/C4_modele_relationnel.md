# C4 — Modélisation relationnelle complémentaire (SQLite)

## Périmètre et justification

Le projet conserve neuf tables analytiques dénormalisées, alimentées à partir des CSV préparés par Python/Pandas. Cette organisation est adaptée à la restitution rapide des analyses historiques et du dashboard. Afin de démontrer explicitement la modélisation relationnelle, une couche **complémentaire** de trois tables est construite à partir des données de marques déjà présentes dans `ebay_google_attention_market` et `google_trends_brand_attention`. Aucun nouveau jeu de données n'est collecté ; les neuf tables et les calculs Rolex ne sont pas modifiés.

## MCD (modèle conceptuel)

Une **Marque** possède un segment de marché et est associée à une observation agrégée **Inventaire eBay** et à une observation agrégée **Attention Google Trends**, dans l'extraction actuelle. Cardinalités : Marque (1,1) — (0,1) Inventaire eBay ; Marque (1,1) — (0,1) Attention Google Trends. Ce modèle est un **instantané agrégé par marque**, non un historique temporel et non un inventaire de montres individuelles.

## MLD (modèle logique)

- `dim_brand` : `brand_id INTEGER PRIMARY KEY`, `brand_name TEXT NOT NULL UNIQUE`, `market_segment TEXT NOT NULL`.
- `fact_ebay_market` : `brand_id INTEGER PRIMARY KEY REFERENCES dim_brand(brand_id)`, `ebay_listing_count INTEGER NOT NULL CHECK >= 0`, `ebay_median_price REAL CHECK >= 0`, `ebay_avg_price REAL CHECK >= 0`.
- `fact_brand_attention` : `brand_id INTEGER PRIMARY KEY REFERENCES dim_brand(brand_id)`, `trend_score REAL`, `relative_attention_score REAL`.

La clé primaire de chaque table de faits est également une clé étrangère : **une seule observation par marque dans cet instantané**. Un index sur `dim_brand(market_segment)` illustre l'indexation ; son gain de performance est limité sur huit marques. L'intégrité référentielle est activée par `PRAGMA foreign_keys=ON` et vérifiée par `PRAGMA foreign_key_check`.

## Requête SQL JOIN vérifiable

```sql
SELECT b.brand_name, b.market_segment,
       e.ebay_listing_count, e.ebay_median_price,
       a.trend_score, a.relative_attention_score
FROM dim_brand AS b
JOIN fact_ebay_market AS e ON e.brand_id = b.brand_id
JOIN fact_brand_attention AS a ON a.brand_id = b.brand_id
ORDER BY e.ebay_listing_count DESC;
```

## Contrôles et limites

Le script `src/build_relational_model.py` vérifie les doublons de marques, les correspondances exactes de marques entre sources, la cohérence des segments et les violations de clés étrangères. Une évolution vers des captures multi-dates exigerait l'ajout d'un identifiant de collecte et d'une clé composée. Le nombre de résultats eBay correspond à une **fenêtre de récupération plafonnée**, pas à une part de marché totale ; Google Trends mesure une attention relative, pas des ventes.

## Exécution

```bash
python src/store.py
python src/build_relational_model.py
python -m unittest discover -s tests -v
```

La création des trois tables est une étape indépendante et optionnelle : elle ne change pas les endpoints FastAPI et n'alimente pas directement les graphiques Streamlit existants. Après une actualisation eBay, il faut relancer `python src/build_relational_model.py` pour mettre à jour cet instantané complémentaire.
