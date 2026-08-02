# Sales & Operations Analytics Dashboard

A food/ride-delivery operations analytics project — SQL + Python + Excel —
built around the same KPIs, RCA, and reporting workflow described in the
Rapido Data Analyst Intern role.

## Dataset

`data/delivery_orders.csv` — 6,000 synthetic orders (Mar–Jun 2026) across 7
Indian cities, modeled on the schema from a public food-delivery dataset
(delivery person rating, weather, traffic density, festival days, multiple
deliveries, etc.), extended with business fields — order value, payment
type, order status, and cancellation reason — so it supports revenue and
cancellation analysis, not just delivery-time prediction.

> This is a synthetic dataset built to realistic distributions (e.g. traffic
> jams and stormy weather roughly double the cancellation rate). Swap in a
> real orders export and every query/formula below still works unchanged.

## What's in this project

| File | Purpose |
|---|---|
| `python/generate_dataset.py` | Generates the synthetic orders dataset |
| `sql/01_schema.sql` | MySQL 8+ schema: `orders` table + `city_dim` lookup table |
| `sql/02_kpi_queries.sql` | Headline KPIs, monthly trend, city revenue, delivery-partner performance, peak-hour volume |
| `sql/03_rca_queries.sql` | Root cause analysis: cancellation drivers by traffic/weather/festival, cancellation-reason Pareto, delay drivers, city-level RCA |
| `python/generate_report.py` | Pandas automation script — regenerates all KPI/RCA summary tables from the raw data in one run (the "automate recurring reports" piece) |
| `Sales_Operations_Analytics_Dashboard.xlsx` | Excel dashboard — KPI cards, monthly trend, city performance, RCA breakdowns, cancellation Pareto, delay drivers — all formula-driven (SUMIFS/COUNTIFS/AVERAGEIFS/VLOOKUP/RANK), recalculates if the raw data changes |

## Key findings (from this dataset)

- **Cancellation rate: 9.47%** overall, but **18.6% during traffic jams** vs
  6.9% in low-traffic conditions — traffic density is the single strongest
  cancellation driver.
- **Stormy weather (17.7%) and sandstorms (15.3%)** roughly double the
  baseline cancellation rate.
- **Festival days: 15.9% cancellation rate** vs 9.1% on normal days, despite
  higher order volume — a capacity/staffing gap on high-demand days.
- **Bengaluru** drives the most revenue (₹4.05L) but also has one of the
  higher cancellation rates — worth a deeper city-level RCA.
- Delivery delays compound: **Jam + 2-3 simultaneous deliveries** pushes
  average delivery time to ~56 minutes, vs ~22 minutes in low-traffic,
  single-delivery orders.

## How to reproduce / extend

```bash
# 1. Regenerate the dataset
python python/generate_dataset.py

# 2. Load into MySQL
mysql -u root -p < sql/01_schema.sql
# then LOAD DATA the CSV per the instructions at the bottom of 01_schema.sql

# 3. Run the KPI / RCA queries
mysql -u root -p delivery_analytics < sql/02_kpi_queries.sql
mysql -u root -p delivery_analytics < sql/03_rca_queries.sql

# 4. Regenerate the automated report tables
cd python && python generate_report.py

# 5. Rebuild the Excel dashboard
python build_dashboard.py
```

