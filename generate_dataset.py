"""
Generates a realistic synthetic food/ride-delivery orders dataset,
modeled on the schema used in the uploaded Kaggle-style delivery-time
notebook (Delivery_person_Age, Weatherconditions, Road_traffic_density,
multiple_deliveries, Festival, City, Time_taken(min), etc.), extended
with business fields (order value, payment type, order status,
cancellation reason) so it supports sales + operations analytics
(RCA, KPIs, dashboards) rather than only a delivery-time regression.

Output: /home/claude/sales_ops_dashboard/data/delivery_orders.csv
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(42)

N = 6000
START_DATE = datetime(2026, 3, 1)
DAYS = 122  # Mar 1 - Jun 30 2026

CITIES = ["Bengaluru", "Mumbai", "Delhi", "Chennai", "Hyderabad", "Pune", "Kolkata"]
CITY_WEIGHTS = [0.24, 0.18, 0.16, 0.12, 0.12, 0.10, 0.08]

WEATHER = ["Sunny", "Cloudy", "Fog", "Windy", "Stormy", "Sandstorms"]
WEATHER_W = [0.38, 0.24, 0.10, 0.14, 0.09, 0.05]

TRAFFIC = ["Low", "Medium", "High", "Jam"]
TRAFFIC_W = [0.30, 0.36, 0.24, 0.10]

ORDER_TYPE = ["Meal", "Snack", "Drinks", "Buffet"]
VEHICLE_TYPE = ["motorcycle", "scooter", "electric_scooter", "bicycle"]
VEHICLE_W = [0.52, 0.28, 0.14, 0.06]
PAYMENT = ["UPI", "Cash", "Card", "Wallet"]
PAYMENT_W = [0.55, 0.20, 0.15, 0.10]

CANCEL_REASONS = [
    "Customer Cancelled", "Restaurant Delay", "Delivery Partner Unavailable",
    "Weather Disruption", "Traffic Delay",
]

# Festival days sprinkled through the window (raises order volume & cancellations)
festival_days = set(rng.choice(range(DAYS), size=6, replace=False))

rows = []
for i in range(N):
    day_offset = int(rng.integers(0, DAYS))
    order_date = START_DATE + timedelta(days=day_offset)
    is_festival = day_offset in festival_days

    city = rng.choice(CITIES, p=CITY_WEIGHTS)
    weather = rng.choice(WEATHER, p=WEATHER_W)
    traffic = rng.choice(TRAFFIC, p=TRAFFIC_W)
    order_type = rng.choice(ORDER_TYPE)
    vehicle_type = rng.choice(VEHICLE_TYPE, p=VEHICLE_W)
    payment_type = rng.choice(PAYMENT, p=PAYMENT_W)

    delivery_person_age = int(np.clip(rng.normal(29, 6), 18, 55))
    delivery_person_rating = round(float(np.clip(rng.normal(4.4, 0.35), 2.5, 5.0)), 1)
    vehicle_condition = int(rng.integers(0, 4))
    multiple_deliveries = int(rng.choice([0, 1, 2, 3], p=[0.55, 0.30, 0.11, 0.04]))

    distance_km = round(float(np.clip(rng.exponential(4.5) + 0.8, 0.5, 25)), 2)

    hour_w = np.array([0.5,0.3,0.2,0.2,0.2,0.3,0.6,1.2,1.8,2.0,2.5,4.5,
                        6.5,4.0,2.2,2.0,2.5,3.5,6.0,7.5,7.0,5.0,3.0,1.5])
    hour_w = hour_w / hour_w.sum()
    order_hour = int(rng.choice(range(24), p=hour_w))
    order_time = f"{order_hour:02d}:{int(rng.integers(0,60)):02d}:00"

    order_value = round(float(np.clip(rng.gamma(4.5, 70), 80, 3500)), 2)

    # --- cancellation probability model ---
    p_cancel = 0.05
    if traffic == "Jam": p_cancel += 0.10
    elif traffic == "High": p_cancel += 0.05
    if weather in ("Stormy", "Sandstorms"): p_cancel += 0.09
    elif weather == "Fog": p_cancel += 0.04
    if is_festival: p_cancel += 0.06
    if multiple_deliveries >= 2: p_cancel += 0.03
    p_cancel = min(p_cancel, 0.55)

    is_cancelled = rng.random() < p_cancel

    if is_cancelled:
        weights = np.array([0.32, 0.22, 0.16, 0.18, 0.12])
        if traffic in ("High", "Jam"):
            weights = weights + np.array([0, 0, 0, 0, 0.15])
        if weather in ("Stormy", "Sandstorms", "Fog"):
            weights = weights + np.array([0, 0, 0, 0.15, 0])
        weights = weights / weights.sum()
        cancellation_reason = rng.choice(CANCEL_REASONS, p=weights)
        delivery_time_min = np.nan
    else:
        cancellation_reason = ""
        base = 18 + distance_km * 1.6
        traffic_add = {"Low": 0, "Medium": 4, "High": 9, "Jam": 16}[traffic]
        weather_add = {"Sunny": 0, "Cloudy": 1, "Windy": 2, "Fog": 6,
                        "Stormy": 10, "Sandstorms": 9}[weather]
        multi_add = multiple_deliveries * 4.5
        festival_add = 6 if is_festival else 0
        noise = rng.normal(0, 3.5)
        delivery_time_min = round(float(np.clip(
            base + traffic_add + weather_add + multi_add + festival_add + noise, 10, 90
        )), 1)

    rows.append({
        "order_id": f"ORD{100000+i}",
        "delivery_person_id": f"{city[:3].upper()}RES{rng.integers(1,45):02d}DEL{rng.integers(1,9):02d}",
        "delivery_person_age": delivery_person_age,
        "delivery_person_rating": delivery_person_rating,
        "city": city,
        "order_date": order_date.strftime("%Y-%m-%d"),
        "order_time": order_time,
        "weather_conditions": weather,
        "road_traffic_density": traffic,
        "vehicle_condition": vehicle_condition,
        "type_of_order": order_type,
        "type_of_vehicle": vehicle_type,
        "multiple_deliveries": multiple_deliveries,
        "festival": "Yes" if is_festival else "No",
        "distance_km": distance_km,
        "order_value_inr": order_value,
        "payment_type": payment_type,
        "order_status": "Cancelled" if is_cancelled else "Delivered",
        "cancellation_reason": cancellation_reason,
        "delivery_time_min": delivery_time_min,
    })

df = pd.DataFrame(rows)
df = df.sort_values(["order_date", "order_time"]).reset_index(drop=True)

out_path = "/home/claude/sales_ops_dashboard/data/delivery_orders.csv"
df.to_csv(out_path, index=False)

print(df.shape)
print(df["order_status"].value_counts())
print(f"Cancellation rate: {(df['order_status']=='Cancelled').mean():.2%}")
print(f"Saved to {out_path}")
