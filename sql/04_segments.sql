/*
Q4 — Customer Segmentation
Goal:
Create simple, interpretable customer segments for business actions
Segments enable targeted retention, upsell, and win-back strategies
*/

WITH customer_metrics AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id) AS total_orders,
        ROUND(SUM(p.payment_value)::NUMERIC, 2) AS total_revenue,
        MAX(o.order_purchase_timestamp)::DATE AS last_purchase_date,
        MIN(o.order_purchase_timestamp)::DATE AS first_purchase_date
    FROM orders o
    JOIN payments p ON o.order_id = p.order_id
    GROUP BY o.customer_id
),

benchmarks AS (
    SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_revenue) AS median_revenue,
        AVG(total_revenue) AS avg_revenue,
        CURRENT_DATE - INTERVAL '3 months' AS active_threshold
    FROM customer_metrics
)

SELECT
    cm.customer_id,
    cm.total_orders,
    cm.total_revenue,
    cm.last_purchase_date,

    CASE
        WHEN cm.total_orders = 1 THEN 'New Customer'
        WHEN cm.total_orders >= 3 THEN 'Loyal Repeat'
        ELSE 'Occasional Repeat'
    END AS customer_lifecycle,

    CASE
        WHEN cm.total_revenue >= b.avg_revenue THEN 'High Value'
        WHEN cm.total_revenue >= b.median_revenue THEN 'Medium Value'
        ELSE 'Low Value'
    END AS spending_tier,

    CASE
        WHEN cm.last_purchase_date >= (b.active_threshold::DATE) THEN 'Active'
        WHEN cm.last_purchase_date >= (CURRENT_DATE - INTERVAL '6 months') THEN 'At Risk'
        ELSE 'Inactive'
    END AS engagement_status,

    CASE
        WHEN cm.total_orders >= 3 AND cm.total_revenue >= b.avg_revenue
             AND cm.last_purchase_date >= (b.active_threshold::DATE)
            THEN 'VIP - Retain & Grow'
        WHEN cm.total_orders >= 2 AND cm.total_revenue >= b.median_revenue
             AND cm.last_purchase_date >= (CURRENT_DATE - INTERVAL '6 months')
            THEN 'Core - Nurture'
        WHEN cm.total_orders = 1 AND cm.last_purchase_date >= (b.active_threshold::DATE)
            THEN 'New - Convert to Repeat'
        WHEN cm.total_revenue >= b.avg_revenue AND cm.last_purchase_date < (CURRENT_DATE - INTERVAL '6 months')
            THEN 'Churned VIP - Win Back'
        ELSE 'Standard - Engage'
    END AS action_segment

FROM customer_metrics cm
CROSS JOIN benchmarks b
ORDER BY cm.total_revenue DESC;
