/*
Q2 — Retention & Cohort Analysis
Goal:
Measure customer retention over time using first-purchase-month cohorts
*/

-- Note: customers.csv does not contain signup timestamps in this dataset.
-- We build cohorts based on customers' first purchase month (first-order cohort).

WITH customer_first_purchase AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(order_purchase_timestamp))::DATE AS cohort_month
    FROM orders
    GROUP BY customer_id
),

customer_purchase_months AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', order_purchase_timestamp)::DATE AS purchase_month
    FROM orders
),

cohort_activity AS (
    SELECT
        f.customer_id,
        f.cohort_month,
        p.purchase_month,
        (EXTRACT(YEAR FROM p.purchase_month) - EXTRACT(YEAR FROM f.cohort_month)) * 12 +
        (EXTRACT(MONTH FROM p.purchase_month) - EXTRACT(MONTH FROM f.cohort_month)) AS month_number
    FROM customer_first_purchase f
    JOIN customer_purchase_months p
        ON f.customer_id = p.customer_id
)

SELECT
    cohort_month,
    month_number,
    COUNT(DISTINCT customer_id) AS active_customers
FROM cohort_activity
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number;
