AI-Powered Zero Trust Access Control System
Overview
This project implements a Zero Trust security system that uses machine learning to assess login risks and monitor user sessions in real-time. Instead of trusting users by default, the system continuously verifies access based on behavioral patterns and contextual information.
What Does It Do?

Login Risk Assessment: When a user logs in, the system analyzes factors like IP address, device type, location, and time to calculate a risk score
Session Monitoring: During an active session, the system watches for unusual behavior that might indicate a security threat
Automatic Decision Making: Based on risk scores, the system can allow access, challenge the user for additional verification, or deny access entirely

Tech Stack
Frontend:

React.js
JavaScript/HTML/CSS

Backend:

Python Flask
PostgreSQL (Database)
Redis (Session management)

Machine Learning:

Calibrated Random Forest - for login risk scoring
Isolation Forest - for detecting anomalous session behavior
scikit-learn, pandas, numpy

DevOps:

Docker

Project Structure
├── notebooks/              # Jupyter notebooks for ML model training
├── zero-trust-frontend/    # React frontend
├── zta-backend/           # Flask backend API
└── README.md
How We Built It
1. Machine Learning Models
Login Risk Model (Calibrated Random Forest):

Trained on login attempt data with features: IP address, device info, location, time, login history
Outputs risk probability (0-1): Low (0-0.3), Medium (0.3-0.7), High (0.7-1.0)
Achieved 91.5% accuracy

Session Anomaly Detection (Isolation Forest):

Monitors user behavior during sessions: request patterns, endpoints accessed, data downloads
Detects unusual activity that deviates from normal behavior
Anomaly detection rate: 87.3%

2. Backend Development

Built REST API with Flask
Integrated ML models for real-time predictions
Implemented JWT authentication
Set up PostgreSQL for user data and Redis for session storage
Created admin endpoints for monitoring and management

3. Frontend Development

Built user interface with React
Created login and registration pages
Developed admin dashboard for monitoring users and risk scores
Implemented session management

4. Integration

Connected frontend to backend via REST APIs
Implemented real-time risk assessment on login
Added continuous session monitoring
Created automated response based on risk levels

Manual Setup
Backend:
bashcd zta-backend
pip install -r requirements.txt
python run.py
Frontend:
bashcd zero-trust-frontend
npm install
npm start
Key Features

Real-time login risk scoring
Continuous session behavior monitoring
Automatic threat detection and response
Admin dashboard for security monitoring
User activity logging and audit trails

ML Model Performance
Calibrated Random Forest (Login Risk):

Accuracy: 91.5%
Precision: 89.2%
Recall: 93.8%

Isolation Forest (Session Anomaly):

Anomaly Detection Rate: 87.3%
False Positive Rate: 4.2%

How It Works

User attempts to login → System extracts features (IP, device, location, time)
ML model predicts risk score → Decision engine allows/challenges/denies access
If allowed, session starts → Continuous monitoring of user behavior
Anomaly detection runs in background → Alerts/terminates session if threat detected
All events logged for audit and model retraining

Future Improvements

Multi-factor authentication
Biometric integration
Mobile application
Advanced threat intelligence integration
Real-time alerting via email/SMS
