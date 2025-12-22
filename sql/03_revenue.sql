/*
Q3 — Revenue Contribution Analysis
Goal:
Understand revenue concentration and the role of repeat customers
*/

-- Use payments.payment_value as authoritative revenue per order
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        ROUND(SUM(p.payment_value)::NUMERIC, 2) AS total_revenue
    FROM orders o
    JOIN payments p ON o.order_id = p.order_id
    GROUP BY o.customer_id
),

ranked_customers AS (
    SELECT
        customer_id,
        total_orders,
        total_revenue,
        NTILE(5) OVER (ORDER BY total_revenue DESC) AS revenue_quintile
    FROM customer_revenue
),

revenue_summary AS (
    SELECT
        revenue_quintile,
        COUNT(*) AS customers,
        ROUND(SUM(total_revenue)::NUMERIC, 2) AS total_revenue
    FROM ranked_customers
    GROUP BY revenue_quintile
)

SELECT
    revenue_quintile,
    customers,
    total_revenue,
    ROUND((total_revenue / SUM(total_revenue) OVER ()) * 100, 2) AS pct_of_total_revenue
FROM revenue_summary
ORDER BY revenue_quintile;
