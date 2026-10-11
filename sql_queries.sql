-- brand_top
SELECT brand, COUNT(*) AS listings, ROUND(AVG(price),2) AS avg_price FROM global_watch_market WHERE brand IS NOT NULL AND price IS NOT NULL GROUP BY brand HAVING COUNT(*) >= 1000 ORDER BY listings DESC LIMIT 10;

-- brand_rank
WITH totals AS (SELECT brand, COUNT(*) AS n FROM global_watch_market WHERE brand IS NOT NULL GROUP BY brand) SELECT brand, n, RANK() OVER (ORDER BY n DESC) AS rank_position FROM totals ORDER BY rank_position LIMIT 10;

-- price_brackets
SELECT CASE WHEN price < 1000 THEN '<1000' WHEN price < 5000 THEN '1000-4999' WHEN price < 10000 THEN '5000-9999' ELSE '10000+' END AS price_bracket, COUNT(*) AS n FROM global_watch_market WHERE price IS NOT NULL AND price > 0 GROUP BY price_bracket ORDER BY n DESC;