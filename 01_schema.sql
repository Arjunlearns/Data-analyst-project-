-- ============================================================
-- Sales & Operations Analytics Dashboard
-- Schema: delivery_analytics
-- Target: MySQL 8.0+ (window functions & CTEs require 8.0+)
-- ============================================================

CREATE DATABASE IF NOT EXISTS delivery_analytics;
USE delivery_analytics;

DROP TABLE IF EXISTS orders;

CREATE TABLE orders (
    order_id                VARCHAR(15)     PRIMARY KEY,
    delivery_person_id      VARCHAR(20)     NOT NULL,
    delivery_person_age     TINYINT UNSIGNED,
    delivery_person_rating  DECIMAL(2,1),
    city                    VARCHAR(30)     NOT NULL,
    order_date              DATE            NOT NULL,
    order_time              TIME            NOT NULL,
    weather_conditions      VARCHAR(20),
    road_traffic_density    VARCHAR(10),
    vehicle_condition       TINYINT UNSIGNED,
    type_of_order           VARCHAR(15),
    type_of_vehicle         VARCHAR(20),
    multiple_deliveries     TINYINT UNSIGNED,
    festival                ENUM('Yes','No') DEFAULT 'No',
    distance_km             DECIMAL(5,2),
    order_value_inr         DECIMAL(8,2)    NOT NULL,
    payment_type            VARCHAR(10),
    order_status            ENUM('Delivered','Cancelled') NOT NULL,
    cancellation_reason     VARCHAR(40),
    delivery_time_min       DECIMAL(5,1),

    INDEX idx_order_date (order_date),
    INDEX idx_city (city),
    INDEX idx_status (order_status),
    INDEX idx_traffic (road_traffic_density),
    INDEX idx_weather (weather_conditions)
);

-- Small dimension table so KPI/RCA queries can demonstrate joins
DROP TABLE IF EXISTS city_dim;

CREATE TABLE city_dim (
    city    VARCHAR(30) PRIMARY KEY,
    region  VARCHAR(15) NOT NULL,
    tier    TINYINT UNSIGNED NOT NULL   -- 1 = metro, 2 = large city
);

INSERT INTO city_dim (city, region, tier) VALUES
    ('Bengaluru', 'South', 1),
    ('Chennai',   'South', 1),
    ('Hyderabad', 'South', 1),
    ('Mumbai',    'West',  1),
    ('Pune',      'West',  2),
    ('Delhi',     'North', 1),
    ('Kolkata',   'East',  1);

-- Load data (run from the MySQL client, adjust path as needed):
-- LOAD DATA LOCAL INFILE 'delivery_orders.csv'
-- INTO TABLE orders
-- FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 ROWS
-- (order_id, delivery_person_id, delivery_person_age, delivery_person_rating,
--  city, order_date, order_time, weather_conditions, road_traffic_density,
--  vehicle_condition, type_of_order, type_of_vehicle, multiple_deliveries,
--  festival, distance_km, order_value_inr, payment_type, order_status,
--  cancellation_reason, @delivery_time_min)
-- SET delivery_time_min = NULLIF(@delivery_time_min, '');
