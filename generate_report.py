"""
Automated weekly/monthly reporting script.

Simulates what a Data Analyst would schedule to run on a cadence
(cron / Airflow / Task Scheduler) to replace a manual "pull data,
build a pivot table, email it" workflow.

Reads the raw orders extract (in production: a SQL query result from
the `orders` table) and produces a set of clean summary tables:
  - headline KPIs
  - monthly trend
  - city / region performance
  - cancellation RCA breakdown
  - delivery delay drivers

Each summary is written to its own CSV in /report_output, ready to be
dropped into Excel/Power BI or emailed as an attachment.

Usage:
    python generate_report.py [path_to_orders_csv]
"""
import sys
import pandas as pd
import numpy as np
from pathlib import Path

INPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "../data/delivery_orders.csv"
OUT_DIR = Path("../report_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CITY_REGION = {
    "Bengaluru": "South", "Chennai": "South", "Hyderabad": "South",
    "Mumbai": "West", "Pune": "West", "Delhi": "North", "Kolkata": "East",
}


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["order_date"])
    df["region"] = df["city"].map(CITY_REGION)
    df["is_cancelled"] = df["order_status"].eq("Cancelled")
    df["month"] = df["order_date"].dt.to_period("M").astype(str)
    df["order_hour"] = pd.to_datetime(df["order_time"], format="%H:%M:%S").dt.hour
    return df


def headline_kpis(df: pd.DataFrame) -> pd.DataFrame:
    delivered = df[df.order_status == "Delivered"]
    return pd.DataFrame([{
        "total_orders": len(df),
        "delivered_orders": len(delivered),
        "cancelled_orders": int(df.is_cancelled.sum()),
        "cancellation_rate_pct": round(df.is_cancelled.mean() * 100, 2),
        "revenue_inr": round(delivered.order_value_inr.sum(), 2),
        "avg_order_value_inr": round(delivered.order_value_inr.mean(), 2),
        "avg_delivery_time_min": round(delivered.delivery_time_min.mean(), 1),
    }])


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("month").agg(
        total_orders=("order_id", "count"),
        cancelled_orders=("is_cancelled", "sum"),
        revenue_inr=("order_value_inr", lambda s: s[df.loc[s.index, "order_status"] == "Delivered"].sum()),
    ).reset_index()
    g["cancellation_rate_pct"] = (g.cancelled_orders / g.total_orders * 100).round(2)
    g["revenue_growth_pct"] = (g.revenue_inr.pct_change() * 100).round(1)
    return g


def city_performance(df: pd.DataFrame) -> pd.DataFrame:
    delivered = df[df.order_status == "Delivered"]
    g = df.groupby(["region", "city"]).agg(
        total_orders=("order_id", "count"),
        cancellation_rate_pct=("is_cancelled", lambda s: round(s.mean() * 100, 2)),
    ).reset_index()
    rev = delivered.groupby("city")["order_value_inr"].sum().round(2).rename("revenue_inr")
    g = g.merge(rev, on="city", how="left")
    g["revenue_rank"] = g["revenue_inr"].rank(ascending=False, method="min").astype(int)
    return g.sort_values("revenue_inr", ascending=False)


def rca_cancellations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim in ["road_traffic_density", "weather_conditions", "festival", "city"]:
        g = df.groupby(dim).agg(
            total_orders=("order_id", "count"),
            cancellation_rate_pct=("is_cancelled", lambda s: round(s.mean() * 100, 2)),
        ).reset_index().rename(columns={dim: "segment_value"})
        g.insert(0, "dimension", dim)
        rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["dimension", "cancellation_rate_pct"], ascending=[True, False])


def cancellation_reasons(df: pd.DataFrame) -> pd.DataFrame:
    cancelled = df[df.order_status == "Cancelled"]
    g = cancelled["cancellation_reason"].value_counts().rename_axis("cancellation_reason").reset_index(name="occurrences")
    g["pct_of_cancellations"] = (g.occurrences / g.occurrences.sum() * 100).round(1)
    g["cumulative_pct"] = g["pct_of_cancellations"].cumsum().round(1)
    return g


def delay_drivers(df: pd.DataFrame) -> pd.DataFrame:
    delivered = df[df.order_status == "Delivered"]
    g = delivered.groupby(["road_traffic_density", "multiple_deliveries"]).agg(
        delivered_orders=("order_id", "count"),
        avg_delivery_time_min=("delivery_time_min", lambda s: round(s.mean(), 1)),
    ).reset_index()
    g["delay_rank"] = g["avg_delivery_time_min"].rank(ascending=False, method="min").astype(int)
    return g.sort_values("avg_delivery_time_min", ascending=False)


def peak_hour_volume(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("order_hour").agg(
        total_orders=("order_id", "count"),
        cancellation_rate_pct=("is_cancelled", lambda s: round(s.mean() * 100, 2)),
    ).reset_index()
    return g.sort_values("order_hour")


def main():
    df = load_data(INPUT_PATH)

    reports = {
        "headline_kpis": headline_kpis(df),
        "monthly_trend": monthly_trend(df),
        "city_performance": city_performance(df),
        "rca_cancellations_by_segment": rca_cancellations(df),
        "cancellation_reasons": cancellation_reasons(df),
        "delay_drivers": delay_drivers(df),
        "peak_hour_volume": peak_hour_volume(df),
    }

    for name, table in reports.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False)
        print(f"[saved] {name}.csv  ({len(table)} rows)")

    print("\n--- Headline KPIs ---")
    print(reports["headline_kpis"].to_string(index=False))


if __name__ == "__main__":
    main()
