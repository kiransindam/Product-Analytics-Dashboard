"""
Product Analytics Dashboard - Plotly Dash
Interactive dashboard with real-time metrics
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime

# Initialize app
app = dash.Dash(__name__, title='Product Analytics Dashboard')
server = app.server  # For deployment

# Database connection
DB_PATH = 'product_analytics.db'

def get_db_connection():
    """Create database connection"""
    return sqlite3.connect(DB_PATH)

def load_metrics():
    """Load all metrics from database"""
    conn = get_db_connection()
    
    metrics = {
        'dau': pd.read_sql("""
            SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as value
            FROM events GROUP BY DATE(timestamp) ORDER BY date
        """, conn),
        'mau': pd.read_sql("""
            SELECT strftime('%Y-%m', timestamp) as month, COUNT(DISTINCT user_id) as value
            FROM events GROUP BY month ORDER BY month
        """, conn),
        'features': pd.read_sql("""
            SELECT feature, COUNT(*) as total_uses, COUNT(DISTINCT user_id) as unique_users
            FROM events WHERE feature IS NOT NULL GROUP BY feature ORDER BY total_uses DESC
        """, conn),
        'retention': pd.read_sql("""
            WITH first_activity AS (
                SELECT user_id, MIN(DATE(timestamp)) as first_date FROM events GROUP BY user_id
            ),
            retention_check AS (
                SELECT f.user_id, f.first_date,
                CASE WHEN e.timestamp IS NOT NULL THEN 1 ELSE 0 END as returned
                FROM first_activity f
                LEFT JOIN events e ON f.user_id = e.user_id 
                AND DATE(e.timestamp) = DATE(f.first_date, '+7 days')
            )
            SELECT strftime('%Y-%m', first_date) as cohort,
            COUNT(*) as total, SUM(returned) as retained,
            ROUND(100.0 * SUM(returned) / COUNT(*), 2) as rate
            FROM retention_check GROUP BY cohort
        """, conn),
        'churn': pd.read_sql("""
            WITH last_activity AS (
                SELECT user_id, MAX(DATE(timestamp)) as last_date,
                julianday('2024-12-31') - julianday(MAX(DATE(timestamp))) as days_inactive
                FROM events GROUP BY user_id
            )
            SELECT u.plan, COUNT(*) as total,
            SUM(CASE WHEN l.days_inactive > 30 THEN 1 ELSE 0 END) as churned,
            ROUND(100.0 * SUM(CASE WHEN l.days_inactive > 30 THEN 1 ELSE 0 END) / COUNT(*), 2) as rate
            FROM users u JOIN last_activity l ON u.user_id = l.user_id
            GROUP BY u.plan
        """, conn),
        'plans': pd.read_sql("""
            SELECT plan, COUNT(*) as count FROM users GROUP BY plan
        """, conn),
        'engagement': pd.read_sql("""
            SELECT 
                CASE 
                    WHEN COUNT(e.event_id) > 100 THEN 'High'
                    WHEN COUNT(e.event_id) > 20 THEN 'Medium'
                    ELSE 'Low'
                END as level,
                COUNT(DISTINCT u.user_id) as users
            FROM users u LEFT JOIN events e ON u.user_id = e.user_id
            GROUP BY level
        """, conn)
    }
    
    conn.close()
    return metrics

# Load initial data
data = load_metrics()

# Calculate KPIs
total_users = pd.read_sql("SELECT COUNT(*) as cnt FROM users", get_db_connection())['cnt'].iloc[0]
total_events = pd.read_sql("SELECT COUNT(*) as cnt FROM events", get_db_connection())['cnt'].iloc[0]
latest_dau = data['dau']['value'].iloc[-1] if len(data['dau']) > 0 else 0
latest_mau = data['mau']['value'].iloc[-1] if len(data['mau']) > 0 else 0
avg_retention = data['retention']['rate'].mean() if len(data['retention']) > 0 else 0

# Color scheme
colors = {
    'primary': '#3B82F6',
    'secondary': '#8B5CF6',
    'success': '#10B981',
    'warning': '#F59E0B',
    'danger': '#EF4444',
    'background': '#F9FAFB',
    'card': '#FFFFFF'
}

# Dashboard layout
app.layout = html.Div(style={'backgroundColor': colors['background'], 'minHeight': '100vh', 'padding': '20px'}, children=[
    
    # Header
    html.Div(style={'marginBottom': '30px'}, children=[
        html.H1('📊 Product Analytics Dashboard', 
                style={'color': '#1F2937', 'marginBottom': '5px', 'fontSize': '36px'}),
        html.P('Real-time insights into user behavior and product performance',
               style={'color': '#6B7280', 'fontSize': '16px'})
    ]),
    
    # KPI Cards
    html.Div(style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))', 
                    'gap': '20px', 'marginBottom': '30px'}, children=[
        
        # Total Users
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.Div('👥 Total Users', style={'color': '#6B7280', 'fontSize': '14px', 'marginBottom': '8px'}),
            html.Div(f'{total_users:,}', style={'color': colors['primary'], 'fontSize': '32px', 'fontWeight': 'bold'})
        ]),
        
        # DAU
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.Div('📅 Daily Active Users', style={'color': '#6B7280', 'fontSize': '14px', 'marginBottom': '8px'}),
            html.Div(f'{latest_dau:,}', style={'color': colors['secondary'], 'fontSize': '32px', 'fontWeight': 'bold'})
        ]),
        
        # MAU
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.Div('📆 Monthly Active Users', style={'color': '#6B7280', 'fontSize': '14px', 'marginBottom': '8px'}),
            html.Div(f'{latest_mau:,}', style={'color': colors['success'], 'fontSize': '32px', 'fontWeight': 'bold'})
        ]),
        
        # Retention
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.Div('🔄 Avg Retention (7d)', style={'color': '#6B7280', 'fontSize': '14px', 'marginBottom': '8px'}),
            html.Div(f'{avg_retention:.1f}%', style={'color': colors['warning'], 'fontSize': '32px', 'fontWeight': 'bold'})
        ]),
        
        # Total Events
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.Div('📊 Total Events', style={'color': '#6B7280', 'fontSize': '14px', 'marginBottom': '8px'}),
            html.Div(f'{total_events:,}', style={'color': colors['danger'], 'fontSize': '32px', 'fontWeight': 'bold'})
        ])
    ]),
    
    # Charts Row 1
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '2fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
        
        # DAU Trend
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H3('Daily Active Users Trend', style={'color': '#1F2937', 'marginBottom': '15px', 'fontSize': '18px'}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Scatter(x=data['dau']['date'], y=data['dau']['value'],
                                   mode='lines+markers', line=dict(color=colors['primary'], width=2),
                                   marker=dict(size=6), fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)')],
                    layout=go.Layout(
                        xaxis=dict(title='Date', showgrid=False),
                        yaxis=dict(title='Active Users', showgrid=True, gridcolor='#E5E7EB'),
                        margin=dict(l=40, r=20, t=20, b=40),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        hovermode='x unified'
                    )
                ),
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ]),
        
        # Plan Distribution
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H3('User Plan Distribution', style={'color': '#1F2937', 'marginBottom': '15px', 'fontSize': '18px'}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Pie(labels=data['plans']['plan'], values=data['plans']['count'],
                               marker=dict(colors=[colors['primary'], colors['secondary'], colors['success']]),
                               hole=0.4, textinfo='label+percent')],
                    layout=go.Layout(
                        margin=dict(l=20, r=20, t=20, b=20),
                        showlegend=False,
                        paper_bgcolor='white'
                    )
                ),
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ]),
    
    # Charts Row 2
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '20px'}, children=[
        
        # Feature Usage
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H3('Feature Adoption', style={'color': '#1F2937', 'marginBottom': '15px', 'fontSize': '18px'}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(x=data['features']['feature'], y=data['features']['unique_users'],
                               marker=dict(color=colors['secondary']))],
                    layout=go.Layout(
                        xaxis=dict(title='Feature', showgrid=False),
                        yaxis=dict(title='Unique Users', showgrid=True, gridcolor='#E5E7EB'),
                        margin=dict(l=40, r=20, t=20, b=60),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                ),
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ]),
        
        # Retention Rate
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H3('7-Day Retention by Cohort', style={'color': '#1F2937', 'marginBottom': '15px', 'fontSize': '18px'}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(x=data['retention']['cohort'], y=data['retention']['rate'],
                               marker=dict(color=colors['success']), text=data['retention']['rate'],
                               texttemplate='%{text:.1f}%', textposition='outside')],
                    layout=go.Layout(
                        xaxis=dict(title='Cohort Month', showgrid=False),
                        yaxis=dict(title='Retention Rate (%)', showgrid=True, gridcolor='#E5E7EB'),
                        margin=dict(l=40, r=20, t=20, b=60),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                ),
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ]),
    
    # Charts Row 3
    html.Div(style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px'}, children=[
        
        # Churn by Plan
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H3('Churn Rate by Plan', style={'color': '#1F2937', 'marginBottom': '15px', 'fontSize': '18px'}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(x=data['churn']['plan'], y=data['churn']['rate'],
                               marker=dict(color=colors['danger']), text=data['churn']['rate'],
                               texttemplate='%{text:.1f}%', textposition='outside')],
                    layout=go.Layout(
                        xaxis=dict(title='Plan', showgrid=False),
                        yaxis=dict(title='Churn Rate (%)', showgrid=True, gridcolor='#E5E7EB'),
                        margin=dict(l=40, r=20, t=20, b=60),
                        plot_bgcolor='white',
                        paper_bgcolor='white'
                    )
                ),
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ]),
        
        # User Engagement
        html.Div(style={'backgroundColor': colors['card'], 'padding': '20px', 'borderRadius': '12px',
                       'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'}, children=[
            html.H3('User Engagement Levels', style={'color': '#1F2937', 'marginBottom': '15px', 'fontSize': '18px'}),
            dcc.Graph(
                figure=go.Figure(
                    data=[go.Funnel(y=data['engagement']['level'], x=data['engagement']['users'],
                                  marker=dict(color=[colors['success'], colors['warning'], colors['danger']]))],
                    layout=go.Layout(
                        margin=dict(l=20, r=20, t=20, b=20),
                        paper_bgcolor='white'
                    )
                ),
                config={'displayModeBar': False},
                style={'height': '300px'}
            )
        ])
    ]),
    
    # Footer
    html.Div(style={'marginTop': '40px', 'textAlign': 'center', 'color': '#6B7280', 'fontSize': '14px'}, children=[
        html.P('Built with Plotly Dash • Data updated in real-time'),
        html.P('Product Analytics Dashboard © 2024')
    ])
])

# Run server
if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)