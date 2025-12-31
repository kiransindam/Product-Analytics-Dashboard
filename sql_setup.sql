-- ============================================
-- Product Analytics Database Setup
-- ============================================

-- Create Users Table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    signup_date DATE NOT NULL,
    country VARCHAR(10),
    plan VARCHAR(20) CHECK (plan IN ('Free', 'Pro', 'Enterprise'))
);

-- Create Events Table
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50),
    feature VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    session_duration INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for better query performance
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_feature ON events(feature);
CREATE INDEX idx_users_signup ON users(signup_date);

-- ============================================
-- ANALYTICS QUERIES
-- ============================================

-- 1. Daily Active Users (DAU)
CREATE VIEW vw_daily_active_users AS
SELECT 
    DATE(timestamp) as activity_date,
    COUNT(DISTINCT user_id) as dau
FROM events
GROUP BY DATE(timestamp)
ORDER BY activity_date;

-- 2. Monthly Active Users (MAU)
CREATE VIEW vw_monthly_active_users AS
SELECT 
    strftime('%Y-%m', timestamp) as month,
    COUNT(DISTINCT user_id) as mau
FROM events
GROUP BY strftime('%Y-%m', timestamp)
ORDER BY month;

-- 3. Feature Usage Analytics
CREATE VIEW vw_feature_usage AS
SELECT 
    feature,
    COUNT(*) as total_events,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(session_duration) as avg_session_duration
FROM events
WHERE feature IS NOT NULL
GROUP BY feature
ORDER BY total_events DESC;

-- 4. User Retention (7-day)
WITH first_activity AS (
    SELECT 
        user_id,
        MIN(DATE(timestamp)) as first_date
    FROM events
    GROUP BY user_id
),
retention_check AS (
    SELECT 
        f.user_id,
        f.first_date,
        CASE WHEN e.timestamp IS NOT NULL THEN 1 ELSE 0 END as returned
    FROM first_activity f
    LEFT JOIN events e 
        ON f.user_id = e.user_id 
        AND DATE(e.timestamp) = DATE(f.first_date, '+7 days')
)
SELECT 
    strftime('%Y-%m', first_date) as cohort_month,
    COUNT(*) as total_users,
    SUM(returned) as retained_users,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) as retention_rate
FROM retention_check
GROUP BY strftime('%Y-%m', first_date)
ORDER BY cohort_month;

-- 5. Churn Analysis
WITH user_last_activity AS (
    SELECT 
        user_id,
        MAX(DATE(timestamp)) as last_activity_date,
        julianday('2024-12-31') - julianday(MAX(DATE(timestamp))) as days_since_last_activity
    FROM events
    GROUP BY user_id
)
SELECT 
    u.plan,
    COUNT(*) as total_users,
    SUM(CASE WHEN l.days_since_last_activity > 30 THEN 1 ELSE 0 END) as churned_users,
    ROUND(100.0 * SUM(CASE WHEN l.days_since_last_activity > 30 THEN 1 ELSE 0 END) / COUNT(*), 2) as churn_rate
FROM users u
JOIN user_last_activity l ON u.user_id = l.user_id
GROUP BY u.plan;

-- 6. User Engagement Score
SELECT 
    e.user_id,
    u.plan,
    COUNT(*) as total_events,
    COUNT(DISTINCT DATE(e.timestamp)) as active_days,
    COUNT(DISTINCT e.feature) as features_used,
    AVG(e.session_duration) as avg_session_duration,
    -- Engagement score: weighted combination of metrics
    ROUND(
        (COUNT(*) * 0.3) + 
        (COUNT(DISTINCT DATE(e.timestamp)) * 2) + 
        (COUNT(DISTINCT e.feature) * 5) +
        (AVG(e.session_duration) / 60 * 0.5)
    , 2) as engagement_score
FROM events e
JOIN users u ON e.user_id = u.user_id
GROUP BY e.user_id, u.plan
ORDER BY engagement_score DESC
LIMIT 100;

-- 7. Cohort Analysis
SELECT 
    strftime('%Y-%m', u.signup_date) as signup_month,
    COUNT(DISTINCT u.user_id) as cohort_size,
    COUNT(DISTINCT e.user_id) as active_users,
    ROUND(100.0 * COUNT(DISTINCT e.user_id) / COUNT(DISTINCT u.user_id), 2) as activation_rate
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id 
    AND DATE(e.timestamp) >= DATE(u.signup_date)
    AND DATE(e.timestamp) <= DATE(u.signup_date, '+7 days')
GROUP BY strftime('%Y-%m', u.signup_date)
ORDER BY signup_month;

-- 8. Plan Performance
SELECT 
    u.plan,
    COUNT(DISTINCT u.user_id) as total_users,
    COUNT(DISTINCT e.user_id) as active_users,
    COUNT(e.event_id) as total_events,
    ROUND(AVG(e.session_duration), 2) as avg_session_duration,
    ROUND(COUNT(e.event_id) * 1.0 / COUNT(DISTINCT u.user_id), 2) as events_per_user
FROM users u
LEFT JOIN events e ON u.user_id = e.user_id
GROUP BY u.plan
ORDER BY total_users DESC;