-- ============================================================
-- ROOT CAUSE ANALYSIS (RCA) QUERIES
-- Business question: "Why is the cancellation rate rising, and
-- what's driving delivery delays?"
-- ============================================================
USE delivery_analytics;

-- 1. Cancellation rate by traffic density (is congestion a driver?)
SELECT
    road_traffic_density,
    COUNT(*)                                                              AS total_orders,
    SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)           AS cancelled_orders,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                            AS cancellation_rate_pct
FROM orders
GROUP BY road_traffic_density
ORDER BY cancellation_rate_pct DESC;


-- 2. Cancellation rate by weather condition
SELECT
    weather_conditions,
    COUNT(*)                                                              AS total_orders,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                            AS cancellation_rate_pct
FROM orders
GROUP BY weather_conditions
ORDER BY cancellation_rate_pct DESC;


-- 3. Festival-day effect: does order volume spike while cancellations also spike?
SELECT
    festival,
    COUNT(*)                                                              AS total_orders,
    ROUND(COUNT(*) / (SELECT COUNT(DISTINCT order_date) FROM orders o2
                       WHERE o2.festival = o1.festival), 1)               AS avg_orders_per_day,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                            AS cancellation_rate_pct
FROM orders o1
GROUP BY festival;


-- 4. Cancellation reason breakdown, ranked, with cumulative share (window function)
WITH reason_counts AS (
    SELECT
        cancellation_reason,
        COUNT(*) AS occurrences
    FROM orders
    WHERE order_status = 'Cancelled'
    GROUP BY cancellation_reason
)
SELECT
    cancellation_reason,
    occurrences,
    ROUND(occurrences / SUM(occurrences) OVER () * 100, 1)                AS pct_of_cancellations,
    ROUND(SUM(occurrences) OVER (ORDER BY occurrences DESC) 
          / SUM(occurrences) OVER () * 100, 1)                            AS cumulative_pct
FROM reason_counts
ORDER BY occurrences DESC;


-- 5. Combined driver view: traffic x weather cancellation heatmap
SELECT
    road_traffic_density,
    weather_conditions,
    COUNT(*)                                                              AS total_orders,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                            AS cancellation_rate_pct
FROM orders
GROUP BY road_traffic_density, weather_conditions
HAVING COUNT(*) >= 20
ORDER BY cancellation_rate_pct DESC
LIMIT 15;


-- 6. Delivery delay drivers: avg delivery time by traffic + multiple_deliveries
-- (only successful deliveries have a delivery_time_min)
SELECT
    road_traffic_density,
    multiple_deliveries,
    COUNT(*)                                                              AS delivered_orders,
    ROUND(AVG(delivery_time_min), 1)                                      AS avg_delivery_time_min,
    RANK() OVER (ORDER BY AVG(delivery_time_min) DESC)                    AS delay_rank
FROM orders
WHERE order_status = 'Delivered'
GROUP BY road_traffic_density, multiple_deliveries
ORDER BY avg_delivery_time_min DESC;


-- 7. City-level RCA: which cities have both high cancellation AND long delivery times?
SELECT
    city,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                            AS cancellation_rate_pct,
    ROUND(AVG(CASE WHEN order_status = 'Delivered' THEN delivery_time_min END), 1) AS avg_delivery_time_min
FROM orders
GROUP BY city
ORDER BY cancellation_rate_pct DESC;
