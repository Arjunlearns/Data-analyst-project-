-- ============================================================
-- KPI QUERIES
-- Sales & Operations Analytics Dashboard
-- ============================================================
USE delivery_analytics;

-- 1. Headline KPIs: orders, revenue, cancellation rate, avg delivery time
SELECT
    COUNT(*)                                            AS total_orders,
    SUM(CASE WHEN order_status = 'Delivered' THEN 1 ELSE 0 END)               AS delivered_orders,
    SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)               AS cancelled_orders,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                                AS cancellation_rate_pct,
    ROUND(SUM(CASE WHEN order_status = 'Delivered' THEN order_value_inr ELSE 0 END), 2) AS revenue_inr,
    ROUND(AVG(CASE WHEN order_status = 'Delivered' THEN delivery_time_min END), 1)      AS avg_delivery_time_min
FROM orders;


-- 2. Monthly trend: orders, revenue, cancellation rate (window function for MoM change)
WITH monthly AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m')                                  AS order_month,
        COUNT(*)                                                          AS total_orders,
        SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)       AS cancelled_orders,
        SUM(CASE WHEN order_status = 'Delivered' THEN order_value_inr ELSE 0 END) AS revenue_inr
    FROM orders
    GROUP BY order_month
)
SELECT
    order_month,
    total_orders,
    revenue_inr,
    ROUND(cancelled_orders / total_orders * 100, 2)                        AS cancellation_rate_pct,
    ROUND(revenue_inr - LAG(revenue_inr) OVER (ORDER BY order_month), 2)   AS revenue_change_vs_prev_month,
    ROUND((revenue_inr - LAG(revenue_inr) OVER (ORDER BY order_month))
          / LAG(revenue_inr) OVER (ORDER BY order_month) * 100, 1)         AS revenue_growth_pct
FROM monthly
ORDER BY order_month;


-- 3. Revenue & order volume by city and region (JOIN to dimension table)
SELECT
    d.region,
    o.city,
    d.tier,
    COUNT(*)                                                               AS total_orders,
    ROUND(SUM(CASE WHEN o.order_status = 'Delivered'
                    THEN o.order_value_inr ELSE 0 END), 2)                 AS revenue_inr,
    ROUND(SUM(CASE WHEN o.order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                             AS cancellation_rate_pct,
    RANK() OVER (ORDER BY SUM(CASE WHEN o.order_status = 'Delivered'
                                    THEN o.order_value_inr ELSE 0 END) DESC) AS revenue_rank
FROM orders o
JOIN city_dim d ON d.city = o.city
GROUP BY d.region, o.city, d.tier
ORDER BY revenue_inr DESC;


-- 4. Delivery partner performance (top 10 by delivered volume, min 15 orders)
SELECT
    delivery_person_id,
    ROUND(AVG(delivery_person_rating), 2)                                   AS avg_rating,
    COUNT(*)                                                                AS delivered_orders,
    ROUND(AVG(delivery_time_min), 1)                                        AS avg_delivery_time_min,
    ROUND(SUM(order_value_inr), 2)                                          AS revenue_handled_inr
FROM orders
WHERE order_status = 'Delivered'
GROUP BY delivery_person_id
HAVING COUNT(*) >= 15
ORDER BY delivered_orders DESC
LIMIT 10;


-- 5. Order volume by hour of day (peak-hour staffing insight)
SELECT
    HOUR(order_time)                                                        AS order_hour,
    COUNT(*)                                                                AS total_orders,
    ROUND(SUM(CASE WHEN order_status = 'Cancelled' THEN 1 ELSE 0 END)
          / COUNT(*) * 100, 2)                                              AS cancellation_rate_pct
FROM orders
GROUP BY order_hour
ORDER BY order_hour;
