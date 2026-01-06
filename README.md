Ecommerce Analytics — Funnel, Retention, Revenue & Segments
===========================================================

Summary
-------
This project analyzes an ecommerce dataset to answer four business questions:

- Funnel approximation (registration → orders → delivered → repeat)
- Retention by first-purchase cohorts (cohort heatmap)
- Revenue concentration (customer revenue quintiles)
- Customer segmentation (actionable segments for retention and growth)

I fixed and refactored the original SQL to run on the provided CSV files,
produced reproducible outputs (CSV) and visualizations (PNG) in `outputs/`.

Key results (examples)
----------------------
- Top customer quintile accounts for ~53% of total revenue (see `outputs/revenue_quintiles.csv`).
- Cohort retention and counts are saved in `outputs/retention_cohort_pivot.csv` and visualized in `outputs/retention_heatmap.png`.
- Actionable segments produced; majority fall into `Standard - Engage`, with a notable `Churned VIP - Win Back` segment (see `outputs/action_segment_counts.csv`).

Files & structure
-----------------
- `data/` — source CSV files (customers, orders, payments, order_items, ...)
- `sql/` — SQL analysis files (01_funnel.sql, 02_retention.sql, 03_revenue.sql, 04_segments.sql)
- `run_queries.py` — lightweight runner using DuckDB to run all SQL files
- `generate_reports.py` — runs queries, saves CSV outputs, and creates PNG charts
- `outputs/` — generated CSVs and PNGs (created by `generate_reports.py`)

Quick reproduction (recommended: DuckDB + Python)
-----------------------------------------------
1) Install dependencies:

```powershell
python -m pip install --user duckdb pandas matplotlib seaborn
```

2) Run the report script (this loads CSVs and creates `outputs/`):

```powershell
python generate_reports.py
```

3) View outputs in `outputs/` (CSV and PNG files).

Methodology notes
-----------------
- Funnel: dataset lacks a clickstream `events` table; funnel is approximated from `customers` + `orders` (registration → placed order → delivered → repeat purchasers).
- Revenue: `payments.payment_value` used as authoritative order revenue; multi-payment orders are aggregated by `order_id`.
- Retention: cohorts defined by customers' first purchase month; retention counts are monthly offsets from cohort.
- Segments: median/mean revenue benchmarks produce `High/Medium/Low Value` tiers and action-oriented labels.



Contact / Reproduce
-------------------
See `generate_reports.py` to reproduce outputs locally. For a resume-ready package I can add an `analysis.ipynb` and `resume_summary.md` with explicit numbers and copyable bullets.

Files updated by me: `sql/*.sql`, `generate_reports.py`, `run_queries.py`, and outputs generated under `outputs/`.

File: [README.md](README.md)
