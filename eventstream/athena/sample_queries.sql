-- =============================================
-- EventStream — Sample Athena Analytics Queries
-- =============================================

-- 1. Events per hour (time series)
SELECT
    year, month, day, hour,
    COUNT(*) as event_count
FROM eventstream.raw_events
WHERE year = 2026 AND month = 2
GROUP BY year, month, day, hour
ORDER BY year, month, day, hour;

-- 2. Top event types
SELECT
    event_type,
    COUNT(*) as total,
    COUNT(DISTINCT user_id) as unique_users
FROM eventstream.raw_events
WHERE year = 2026
GROUP BY event_type
ORDER BY total DESC
LIMIT 20;

-- 3. User activity heatmap (events by hour of day)
SELECT
    hour,
    COUNT(*) as events,
    COUNT(DISTINCT user_id) as users
FROM eventstream.raw_events
GROUP BY hour
ORDER BY hour;

-- 4. Anomaly detection — events that spike 3x above daily average
WITH daily_counts AS (
    SELECT day, COUNT(*) as daily_total
    FROM eventstream.raw_events
    WHERE year = 2026 AND month = 2
    GROUP BY day
),
stats AS (
    SELECT AVG(daily_total) as avg_daily, STDDEV(daily_total) as std_daily
    FROM daily_counts
)
SELECT d.day, d.daily_total, s.avg_daily,
       (d.daily_total - s.avg_daily) / NULLIF(s.std_daily, 0) as z_score
FROM daily_counts d CROSS JOIN stats s
WHERE (d.daily_total - s.avg_daily) / NULLIF(s.std_daily, 0) > 2.0
ORDER BY z_score DESC;

-- 5. Top sources by volume
SELECT
    source,
    COUNT(*) as events,
    MIN(timestamp) as first_seen,
    MAX(timestamp) as last_seen
FROM eventstream.raw_events
GROUP BY source
ORDER BY events DESC
LIMIT 10;
