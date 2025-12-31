"""
Product Analytics - Data Analysis & Cleaning
Complete EDA and KPI calculation pipeline
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ProductAnalytics:
    """Main analytics class for product metrics"""
    
    def __init__(self, db_path='product_analytics.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def load_data(self, csv_users='users.csv', csv_events='events.csv'):
        """Load and clean data from CSV files"""
        print("📊 Loading data...")
        
        # Load CSVs
        users = pd.read_csv(csv_users)
        events = pd.read_csv(csv_events)
        
        # Data cleaning - Users
        users['signup_date'] = pd.to_datetime(users['signup_date'])
        users = users.drop_duplicates(subset=['user_id'])
        users = users.dropna(subset=['user_id', 'signup_date'])
        
        # Data cleaning - Events
        events['timestamp'] = pd.to_datetime(events['timestamp'])
        events = events.drop_duplicates(subset=['event_id'])
        events = events.dropna(subset=['event_id', 'user_id', 'timestamp'])
        events['session_duration'] = events['session_duration'].fillna(0)
        
        # Save to database
        users.to_sql('users', self.conn, if_exists='replace', index=False)
        events.to_sql('events', self.conn, if_exists='replace', index=False)
        
        print(f"✅ Loaded {len(users)} users and {len(events)} events")
        return users, events
    
    def calculate_dau_mau(self):
        """Calculate Daily and Monthly Active Users"""
        query = """
        SELECT 
            DATE(timestamp) as date,
            COUNT(DISTINCT user_id) as dau
        FROM events
        GROUP BY DATE(timestamp)
        ORDER BY date
        """
        dau = pd.read_sql(query, self.conn)
        dau['date'] = pd.to_datetime(dau['date'])
        dau['month'] = dau['date'].dt.to_period('M')
        
        # Calculate MAU
        mau = dau.groupby('month')['dau'].apply(
            lambda x: pd.read_sql(
                f"SELECT COUNT(DISTINCT user_id) as mau FROM events WHERE strftime('%Y-%m', timestamp) = '{x.name}'",
                self.conn
            )['mau'].iloc[0] if len(x) > 0 else 0
        ).reset_index()
        mau.columns = ['month', 'mau']
        
        return dau, mau
    
    def calculate_retention(self, days=7):
        """Calculate N-day retention rate"""
        query = f"""
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
                AND DATE(e.timestamp) = DATE(f.first_date, '+{days} days')
        )
        SELECT 
            strftime('%Y-%m', first_date) as cohort,
            COUNT(*) as total_users,
            SUM(returned) as retained_users,
            ROUND(100.0 * SUM(returned) / COUNT(*), 2) as retention_rate
        FROM retention_check
        GROUP BY strftime('%Y-%m', first_date)
        """
        return pd.read_sql(query, self.conn)
    
    def calculate_churn(self, inactive_days=30):
        """Calculate churn rate by plan"""
        query = f"""
        WITH user_last_activity AS (
            SELECT 
                user_id,
                MAX(DATE(timestamp)) as last_activity,
                julianday('2024-12-31') - julianday(MAX(DATE(timestamp))) as days_inactive
            FROM events
            GROUP BY user_id
        )
        SELECT 
            u.plan,
            COUNT(*) as total_users,
            SUM(CASE WHEN l.days_inactive > {inactive_days} THEN 1 ELSE 0 END) as churned,
            ROUND(100.0 * SUM(CASE WHEN l.days_inactive > {inactive_days} THEN 1 ELSE 0 END) / COUNT(*), 2) as churn_rate
        FROM users u
        JOIN user_last_activity l ON u.user_id = l.user_id
        GROUP BY u.plan
        """
        return pd.read_sql(query, self.conn)
    
    def feature_adoption(self):
        """Analyze feature usage and adoption"""
        query = """
        SELECT 
            feature,
            COUNT(*) as total_uses,
            COUNT(DISTINCT user_id) as unique_users,
            ROUND(AVG(session_duration), 2) as avg_duration,
            COUNT(DISTINCT DATE(timestamp)) as days_active
        FROM events
        WHERE feature IS NOT NULL
        GROUP BY feature
        ORDER BY total_uses DESC
        """
        return pd.read_sql(query, self.conn)
    
    def user_segmentation(self):
        """Segment users by engagement level"""
        query = """
        SELECT 
            u.user_id,
            u.plan,
            u.country,
            COUNT(e.event_id) as total_events,
            COUNT(DISTINCT DATE(e.timestamp)) as active_days,
            COUNT(DISTINCT e.feature) as features_used,
            ROUND(AVG(e.session_duration), 2) as avg_session_duration,
            CASE 
                WHEN COUNT(e.event_id) > 100 THEN 'High'
                WHEN COUNT(e.event_id) > 20 THEN 'Medium'
                ELSE 'Low'
            END as engagement_level
        FROM users u
        LEFT JOIN events e ON u.user_id = e.user_id
        GROUP BY u.user_id, u.plan, u.country
        """
        return pd.read_sql(query, self.conn)
    
    def cohort_analysis(self):
        """Cohort retention analysis"""
        query = """
        WITH cohorts AS (
            SELECT 
                user_id,
                strftime('%Y-%m', signup_date) as cohort_month
            FROM users
        )
        SELECT 
            c.cohort_month,
            strftime('%Y-%m', e.timestamp) as activity_month,
            COUNT(DISTINCT e.user_id) as active_users
        FROM cohorts c
        JOIN events e ON c.user_id = e.user_id
        GROUP BY c.cohort_month, strftime('%Y-%m', e.timestamp)
        ORDER BY c.cohort_month, activity_month
        """
        return pd.read_sql(query, self.conn)
    
    def generate_summary_report(self):
        """Generate executive summary with key metrics"""
        print("\n" + "="*60)
        print("📈 PRODUCT ANALYTICS SUMMARY REPORT")
        print("="*60 + "\n")
        
        # Total users and events
        total_users = pd.read_sql("SELECT COUNT(*) as cnt FROM users", self.conn)['cnt'].iloc[0]
        total_events = pd.read_sql("SELECT COUNT(*) as cnt FROM events", self.conn)['cnt'].iloc[0]
        
        print(f"👥 Total Users: {total_users:,}")
        print(f"📊 Total Events: {total_events:,}")
        print(f"📈 Events per User: {total_events/total_users:.1f}\n")
        
        # DAU/MAU
        latest_dau = pd.read_sql(
            "SELECT COUNT(DISTINCT user_id) as dau FROM events WHERE DATE(timestamp) = (SELECT MAX(DATE(timestamp)) FROM events)",
            self.conn
        )['dau'].iloc[0]
        
        latest_mau = pd.read_sql(
            "SELECT COUNT(DISTINCT user_id) as mau FROM events WHERE strftime('%Y-%m', timestamp) = (SELECT MAX(strftime('%Y-%m', timestamp)) FROM events)",
            self.conn
        )['mau'].iloc[0]
        
        print(f"📅 Latest DAU: {latest_dau:,}")
        print(f"📆 Latest MAU: {latest_mau:,}")
        print(f"🎯 DAU/MAU Ratio: {latest_dau/latest_mau*100:.1f}%\n")
        
        # Top features
        print("🔥 Top 3 Features:")
        features = self.feature_adoption().head(3)
        for idx, row in features.iterrows():
            print(f"   {idx+1}. {row['feature']}: {row['total_uses']:,} uses ({row['unique_users']:,} users)")
        
        # Plan distribution
        print("\n💼 Plan Distribution:")
        plans = pd.read_sql("SELECT plan, COUNT(*) as cnt FROM users GROUP BY plan", self.conn)
        for _, row in plans.iterrows():
            print(f"   {row['plan']}: {row['cnt']:,} users ({row['cnt']/total_users*100:.1f}%)")
        
        # Retention
        retention = self.calculate_retention(7)
        avg_retention = retention['retention_rate'].mean()
        print(f"\n🔄 Average 7-Day Retention: {avg_retention:.1f}%")
        
        # Churn
        churn = self.calculate_churn(30)
        avg_churn = churn['churn_rate'].mean()
        print(f"⚠️  Average Churn Rate: {avg_churn:.1f}%")
        
        print("\n" + "="*60 + "\n")
    
    def export_for_dashboard(self, output_dir='dashboard_data'):
        """Export processed data for dashboard"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Export all key metrics
        dau, mau = self.calculate_dau_mau()
        dau.to_csv(f'{output_dir}/dau.csv', index=False)
        mau.to_csv(f'{output_dir}/mau.csv', index=False)
        
        self.calculate_retention(7).to_csv(f'{output_dir}/retention.csv', index=False)
        self.calculate_churn(30).to_csv(f'{output_dir}/churn.csv', index=False)
        self.feature_adoption().to_csv(f'{output_dir}/features.csv', index=False)
        self.user_segmentation().to_csv(f'{output_dir}/segments.csv', index=False)
        self.cohort_analysis().to_csv(f'{output_dir}/cohorts.csv', index=False)
        
        print(f"✅ Data exported to {output_dir}/ directory")
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Main execution
if __name__ == "__main__":
    print("🚀 Starting Product Analytics Pipeline\n")
    
    # Initialize analytics
    analytics = ProductAnalytics()
    
    # Load and clean data
    users, events = analytics.load_data('users.csv', 'events.csv')
    
    # Generate summary report
    analytics.generate_summary_report()
    
    # Export data for dashboard
    analytics.export_for_dashboard()
    
    # Close connection
    analytics.close()
    
    print("✅ Analysis complete! Ready for dashboard deployment.")
