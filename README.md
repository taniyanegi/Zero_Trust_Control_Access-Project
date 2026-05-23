🚀 AI-Powered Zero Trust Access Control System
📌 Overview

An intelligent cybersecurity system that implements the Zero Trust Security Model using Machine Learning to continuously verify users instead of trusting them by default.

The system performs:

🔐 Login Risk Assessment
👁️ Continuous Session Monitoring
🤖 AI-Based Threat Detection
⚡ Automatic Access Decisions
🛡️ Features
Feature	Description
Risk-Based Authentication	Calculates login risk score using ML
Session Monitoring	Detects suspicious behavior in real time
JWT Authentication	Secure token-based authentication
Admin Dashboard	Monitor users, risks, and anomalies
Audit Logging	Tracks all activities for security review
Redis Session Store	Fast and scalable session management
PostgreSQL Database	Stores users and security logs
🧠 Machine Learning Models
1️⃣ Login Risk Assessment
Model Used:
Calibrated Random Forest
Features:
IP Address
Device Information
Browser
Login Time
Geolocation
Login History
Risk Levels
Score	Risk
0.0 - 0.3	🟢 Low
0.3 - 0.7	🟡 Medium
0.7 - 1.0	🔴 High
Performance
Metric	Value
Accuracy	91.5%
Precision	89.2%
Recall	93.8%
2️⃣ Session Anomaly Detection
Model Used:
Isolation Forest
Monitored Activities:
Request Frequency
Endpoint Access Patterns
Data Downloads
User Navigation Behavior
Performance
Metric	Value
Detection Rate	87.3%
False Positive Rate	4.2%
⚙️ Tech Stack
Frontend
React.js
JavaScript
HTML/CSS
Backend
Python Flask
PostgreSQL
Redis
Machine Learning
scikit-learn
pandas
numpy
DevOps
Docker
🏗️ Project Architecture
User Login
    ↓
Frontend (React)
    ↓
Flask REST API
    ↓
Risk Assessment ML Model
    ↓
Decision Engine
 ┌───────────────┐
 │ Allow Access  │
 │ Challenge MFA │
 │ Deny Access   │
 └───────────────┘
    ↓
Session Monitoring
    ↓
Isolation Forest
    ↓
Threat Detection & Alerts
📂 Project Structure
AI-Zero-Trust-System/
│
├── notebooks/               # ML model training notebooks
├── zero-trust-frontend/     # React frontend
├── zta-backend/             # Flask backend
├── docker-compose.yml
├── README.md
└── requirements.txt
🔄 Workflow
Step 1: User Login

The user attempts to login using credentials.

Step 2: Feature Extraction

The system extracts:

IP address
Device info
Browser details
Login time
Geolocation
Step 3: Risk Prediction

The ML model predicts a risk score.

Step 4: Decision Engine

Based on the score:

✅ Allow Access
⚠️ Ask for Verification
❌ Deny Access
Step 5: Session Monitoring

The system continuously tracks user behavior.

Step 6: Anomaly Detection

Isolation Forest identifies suspicious activity.



📊 Future Improvements
✅ Biometric Verification
✅ Real-Time Email/SMS Alerts
✅ Threat Intelligence Integration
✅ Mobile Application
✅ SIEM Integration
