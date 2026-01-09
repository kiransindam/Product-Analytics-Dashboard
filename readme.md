# 📊 Product Analytics Dashboard

A comprehensive, production-ready analytics dashboard built with **SQL, Python, and Plotly Dash** to analyze product usage, user behavior, and business metrics.

![Dashboard Preview](https://img.shields.io/badge/Status-Live-success)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 Project Overview

This project demonstrates end-to-end data analytics skills including:
- SQL database design and complex queries
- Python data analysis with Pandas
- Interactive dashboard development
- Cloud deployment and DevOps
- Business intelligence and KPI tracking


## 📈 Key Features

### Analytics Metrics
- **Daily Active Users (DAU)** - Track daily engagement trends
- **Monthly Active Users (MAU)** - Monitor monthly growth
- **DAU/MAU Ratio** - Measure stickiness and retention
- **7-Day Retention** - Cohort-based retention analysis
- **Churn Analysis** - Identify at-risk user segments
- **Feature Adoption** - Understand which features drive engagement
- **User Segmentation** - High/Medium/Low engagement levels

### Technical Highlights
- ✅ **SQL:** Complex CTEs, window functions, optimized joins
- ✅ **Python:** Pandas for data cleaning & EDA
- ✅ **Visualization:** Interactive Plotly charts
- ✅ **Deployment:** Free cloud hosting on Render
- ✅ **Scalable:** Designed for real production data

## 🖼️ Dashboard Screenshots

### Main Dashboard
*KPI cards showing key metrics at a glance*

### DAU Trend Analysis
*Line chart tracking daily active users over time*

### Feature Adoption
*Bar chart revealing which features users love*

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.11+
pip (Python package manager)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/product-analytics-dashboard.git
cd product-analytics-dashboard
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Generate sample data**
- Use the data generator (see DEPLOYMENT_GUIDE.md)
- Or use your own `users.csv` and `events.csv`

5. **Run analysis pipeline**
```bash
python data_analysis.py
```

6. **Launch dashboard**
```bash
python app.py
```

7. **Open browser**
```
http://localhost:8050
```

## 📁 Project Structure

```
product-analytics-dashboard/
│
├── app.py                    # Main dashboard application
├── data_analysis.py          # Analytics & data processing
├── database_setup.sql        # SQL schema & queries
├── requirements.txt          # Python dependencies
├── render.yaml              # Deployment configuration
│
├── users.csv                # Sample user data
├── events.csv               # Sample event data
├── product_analytics.db     # SQLite database
│
├── DEPLOYMENT_GUIDE.md      # Detailed deployment steps
└── README.md                # This file
```

## 💾 Database Schema

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    signup_date DATE NOT NULL,
    country VARCHAR(10),
    plan VARCHAR(20)
);
```

### Events Table
```sql
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    event_type VARCHAR(50),
    feature VARCHAR(50),
    timestamp TIMESTAMP NOT NULL,
    session_duration INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

## 📊 Sample SQL Queries

### Calculate DAU
```sql
SELECT 
    DATE(timestamp) as date,
    COUNT(DISTINCT user_id) as dau
FROM events
GROUP BY DATE(timestamp)
ORDER BY date;
```

### 7-Day Retention
```sql
WITH first_activity AS (
    SELECT user_id, MIN(DATE(timestamp)) as first_date
    FROM events GROUP BY user_id
),
retention_check AS (
    SELECT f.user_id, f.first_date,
    CASE WHEN e.timestamp IS NOT NULL THEN 1 ELSE 0 END as returned
    FROM first_activity f
    LEFT JOIN events e ON f.user_id = e.user_id 
    AND DATE(e.timestamp) = DATE(f.first_date, '+7 days')
)
SELECT 
    strftime('%Y-%m', first_date) as cohort,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) as retention_rate
FROM retention_check
GROUP BY cohort;
```

## 🌐 Deployment

### Deploy to Render (Free)

1. Push code to GitHub
2. Connect GitHub repo to [Render](https://render.com)
3. Configure as Web Service:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:server`
4. Deploy!

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## 🛠️ Technologies

| Category | Technology |
|----------|-----------|
| **Database** | SQLite (production: PostgreSQL) |
| **Backend** | Python 3.11, Pandas, NumPy |
| **Frontend** | Plotly Dash, HTML/CSS |
| **Deployment** | Render, Gunicorn |
| **Version Control** | Git, GitHub |

## 📚 Key Learnings

This project demonstrates:
- ✅ SQL database design and optimization
- ✅ Data cleaning and ETL pipelines
- ✅ Exploratory Data Analysis (EDA)
- ✅ KPI definition and tracking
- ✅ Interactive data visualization
- ✅ Cloud deployment and DevOps
- ✅ Business intelligence best practices

## 🎓 Skills Demonstrated

### For Product Analyst Roles
- User behavior analysis
- Retention and churn metrics
- Feature adoption tracking
- Cohort analysis
- Data-driven storytelling

### For Data Analyst Roles
- SQL query optimization
- Python data pipelines
- Statistical analysis
- Dashboard development
- Stakeholder communication

## 📈 Future Enhancements

- [ ] Real-time data streaming
- [ ] User authentication system
- [ ] A/B testing framework
- [ ] Predictive churn model (ML)
- [ ] Email report automation
- [ ] Mobile responsive design
- [ ] Export to PDF functionality

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👤 Author

**Your Name**
- Portfolio: https://kiransindam-39lyhoe.gamma.site/
- LinkedIn: https://www.linkedin.com/in/kiransindam/
- GitHub: @kiransindam

## 🙏 Acknowledgments

- Built as part of FlatUI Product Analyst application
- Inspired by real-world product analytics needs
- Data visualization powered by Plotly

---

⭐ **Star this repo if you found it helpful!**

📧 **Questions?** Open an issue or reach out on LinkedIn!
