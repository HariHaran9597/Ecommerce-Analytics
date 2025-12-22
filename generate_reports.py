import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / 'outputs'
OUT.mkdir(exist_ok=True)

con = duckdb.connect(database=':memory:')

# load csvs
con.execute("CREATE TABLE customers AS SELECT * FROM read_csv_auto('data/customers.csv')")
con.execute("CREATE TABLE orders AS SELECT * FROM read_csv_auto('data/orders.csv')")
con.execute("CREATE TABLE payments AS SELECT * FROM read_csv_auto('data/payments.csv')")
con.execute("CREATE TABLE order_items AS SELECT * FROM read_csv_auto('data/order_items.csv')")

# 1) Funnel approximation
funnel_q = '''
WITH
    total_customers AS (SELECT COUNT(DISTINCT customer_id) AS cnt FROM customers),
    customers_with_orders AS (SELECT COUNT(DISTINCT customer_id) AS cnt FROM orders),
    customers_with_delivered AS (SELECT COUNT(DISTINCT customer_id) AS cnt FROM orders WHERE order_status = 'delivered'),
    repeat_customers AS (SELECT COUNT(*) AS cnt FROM (SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(DISTINCT order_id) > 1) t)
SELECT 'Registered customers' AS stage, tc.cnt AS customers, 100.0 AS pct_of_total FROM total_customers tc
UNION ALL
SELECT 'Placed any order' AS stage, cwo.cnt AS customers, ROUND(100.0 * cwo.cnt::NUMERIC / tc.cnt, 2) AS pct_of_total FROM customers_with_orders cwo CROSS JOIN total_customers tc
UNION ALL
SELECT 'Delivered order' AS stage, cwd.cnt AS customers, ROUND(100.0 * cwd.cnt::NUMERIC / tc.cnt, 2) AS pct_of_total FROM customers_with_delivered cwd CROSS JOIN total_customers tc
UNION ALL
SELECT 'Repeat purchasers (>1 order)' AS stage, rc.cnt AS customers, ROUND(100.0 * rc.cnt::NUMERIC / tc.cnt, 2) AS pct_of_total FROM repeat_customers rc CROSS JOIN total_customers tc
ORDER BY stage;'''

funnel_df = con.execute(funnel_q).df()
funnel_df.to_csv(OUT / 'funnel_summary.csv', index=False)

# 2) Retention (cohort heatmap)
ret_q = '''
WITH customer_first_purchase AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_purchase_timestamp))::DATE AS cohort_month FROM orders GROUP BY customer_id
), customer_purchase_months AS (
    SELECT customer_id, DATE_TRUNC('month', order_purchase_timestamp)::DATE AS purchase_month FROM orders
), cohort_activity AS (
    SELECT f.customer_id, f.cohort_month, p.purchase_month,
    (EXTRACT(YEAR FROM p.purchase_month) - EXTRACT(YEAR FROM f.cohort_month))*12 + (EXTRACT(MONTH FROM p.purchase_month) - EXTRACT(MONTH FROM f.cohort_month)) AS month_number
    FROM customer_first_purchase f JOIN customer_purchase_months p ON f.customer_id = p.customer_id
)
SELECT cohort_month, month_number, COUNT(DISTINCT customer_id) AS active_customers FROM cohort_activity GROUP BY cohort_month, month_number ORDER BY cohort_month, month_number;
'''
ret_df = con.execute(ret_q).df()
ret_df.to_csv(OUT / 'retention_cohort_counts.csv', index=False)

# pivot for heatmap (limit cohorts to first 12 months for readability)
pivot = ret_df.pivot(index='cohort_month', columns='month_number', values='active_customers').fillna(0)
# sort by cohort
pivot = pivot.sort_index()
# save pivot
pivot.to_csv(OUT / 'retention_cohort_pivot.csv')

plt.figure(figsize=(12,8))
sns.heatmap(pivot.iloc[:24, :12], cmap='YlGnBu', linewidths=.5)
plt.title('Cohort retention heatmap (counts)')
plt.tight_layout()
plt.savefig(OUT / 'retention_heatmap.png')
plt.close()

# 3) Revenue quintiles
rev_q = '''
WITH customer_revenue AS (
    SELECT o.customer_id, COUNT(DISTINCT o.order_id) AS total_orders, ROUND(SUM(p.payment_value)::NUMERIC,2) AS total_revenue FROM orders o JOIN payments p ON o.order_id = p.order_id GROUP BY o.customer_id
), ranked AS (
    SELECT customer_id, total_orders, total_revenue, NTILE(5) OVER (ORDER BY total_revenue DESC) AS revenue_quintile FROM customer_revenue
)
SELECT revenue_quintile, COUNT(*) AS customers, ROUND(SUM(total_revenue)::NUMERIC,2) AS total_revenue FROM ranked GROUP BY revenue_quintile ORDER BY revenue_quintile;
'''
rev_df = con.execute(rev_q).df()
rev_df.to_csv(OUT / 'revenue_quintiles.csv', index=False)

plt.figure(figsize=(8,5))
sns.barplot(x='revenue_quintile', y='total_revenue', data=rev_df)
plt.title('Revenue by customer quintile')
plt.xlabel('Quintile (1 = top)')
plt.ylabel('Total revenue')
plt.tight_layout()
plt.savefig(OUT / 'revenue_by_quintile.png')
plt.close()

# 4) Segments summary
seg_q = '''
WITH customer_metrics AS (
    SELECT o.customer_id, COUNT(DISTINCT o.order_id) AS total_orders, ROUND(SUM(p.payment_value)::NUMERIC,2) AS total_revenue, MAX(o.order_purchase_timestamp)::DATE AS last_purchase_date FROM orders o JOIN payments p ON o.order_id = p.order_id GROUP BY o.customer_id
), benchmarks AS (
    SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_revenue) AS median_revenue, AVG(total_revenue) AS avg_revenue, CURRENT_DATE - INTERVAL '3 months' AS active_threshold FROM customer_metrics
)
SELECT cm.customer_id, cm.total_orders, cm.total_revenue, cm.last_purchase_date,
CASE WHEN cm.total_orders = 1 THEN 'New Customer' WHEN cm.total_orders >= 3 THEN 'Loyal Repeat' ELSE 'Occasional Repeat' END AS customer_lifecycle,
CASE WHEN cm.total_revenue >= b.avg_revenue THEN 'High Value' WHEN cm.total_revenue >= b.median_revenue THEN 'Medium Value' ELSE 'Low Value' END AS spending_tier,
CASE WHEN cm.last_purchase_date >= (b.active_threshold::DATE) THEN 'Active' WHEN cm.last_purchase_date >= (CURRENT_DATE - INTERVAL '6 months') THEN 'At Risk' ELSE 'Inactive' END AS engagement_status,
CASE WHEN cm.total_orders >= 3 AND cm.total_revenue >= b.avg_revenue AND cm.last_purchase_date >= (b.active_threshold::DATE) THEN 'VIP - Retain & Grow'
WHEN cm.total_orders >= 2 AND cm.total_revenue >= b.median_revenue AND cm.last_purchase_date >= (CURRENT_DATE - INTERVAL '6 months') THEN 'Core - Nurture'
WHEN cm.total_orders = 1 AND cm.last_purchase_date >= (b.active_threshold::DATE) THEN 'New - Convert to Repeat'
WHEN cm.total_revenue >= b.avg_revenue AND cm.last_purchase_date < (CURRENT_DATE - INTERVAL '6 months') THEN 'Churned VIP - Win Back' ELSE 'Standard - Engage' END AS action_segment
FROM customer_metrics cm CROSS JOIN benchmarks b ORDER BY cm.total_revenue DESC;
'''
seg_df = con.execute(seg_q).df()
seg_df.to_csv(OUT / 'customer_segments.csv', index=False)

# summary counts by action_segment
action_counts = seg_df.groupby('action_segment').size().reset_index(name='count').sort_values('count', ascending=False)
action_counts.to_csv(OUT / 'action_segment_counts.csv', index=False)

plt.figure(figsize=(10,6))
sns.barplot(y='action_segment', x='count', data=action_counts)
plt.title('Customer counts by action segment')
plt.tight_layout()
plt.savefig(OUT / 'action_segment_counts.png')
plt.close()

print('Reports and charts saved to', OUT)
