/*
Q1 — Funnel Analysis (approximation)
Goal:
Estimate customer conversion using available tables. The original project
expected a clickstream `events` table which is not present. Here we
approximate funnel conversion using the customers and orders tables:
 - Total registered customers
 - Customers who ever placed an order
 - Customers with delivered orders
 - Repeat purchasers
*/

WITH
    total_customers AS (
        SELECT COUNT(DISTINCT customer_id) AS cnt FROM customers
    ),

    customers_with_orders AS (
        SELECT COUNT(DISTINCT customer_id) AS cnt
        FROM orders
    ),

    customers_with_delivered AS (
        SELECT COUNT(DISTINCT customer_id) AS cnt
        FROM orders
        WHERE order_status = 'delivered'
    ),

    repeat_customers AS (
        SELECT COUNT(*) AS cnt
        FROM (
            SELECT customer_id, COUNT(DISTINCT order_id) AS orders_count
            FROM orders
            GROUP BY customer_id
            HAVING COUNT(DISTINCT order_id) > 1
        ) t
    )

SELECT
    'Registered customers' AS stage,
    tc.cnt AS customers,
    100.0 AS pct_of_total
FROM total_customers tc

UNION ALL

SELECT
    'Placed any order' AS stage,
    cwo.cnt AS customers,
    ROUND(100.0 * cwo.cnt::NUMERIC / tc.cnt, 2) AS pct_of_total
FROM customers_with_orders cwo CROSS JOIN total_customers tc

UNION ALL

SELECT
    'Delivered order' AS stage,
    cwd.cnt AS customers,
    ROUND(100.0 * cwd.cnt::NUMERIC / tc.cnt, 2) AS pct_of_total
FROM customers_with_delivered cwd CROSS JOIN total_customers tc

UNION ALL

SELECT
    'Repeat purchasers (>1 order)' AS stage,
    rc.cnt AS customers,
    ROUND(100.0 * rc.cnt::NUMERIC / tc.cnt, 2) AS pct_of_total
FROM repeat_customers rc CROSS JOIN total_customers tc
ORDER BY stage;
