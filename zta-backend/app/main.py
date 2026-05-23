from pyexpat import features

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import datetime
import numpy as np
import joblib
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from sklearn.ensemble import IsolationForest

# ==========================
# Local Imports (FIXED ✅)
# ==========================
from .database import SessionLocal, engine
from . import models
from .auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

# ==========================
# App
# ==========================
app = FastAPI(title="Zero Trust Auth + ML Backend")

# ==========================
# CORS
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================
# DB Init
# ==========================
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================
# Password Hashing
# ==========================
# Support both argon2 and bcrypt for backwards compatibility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

# ==========================
# 🧠 AI Phase 1: Load Initial Risk Model (Random Forest)
# ==========================
# This model evaluates the initial login attempt (Context-based access).
# It was trained on historical data to identify risky login patterns.
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "zta_calibrated_rf.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "zta_scaler.pkl")
FEATURES_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "zta_feature_columns.pkl")

rf_model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
feature_columns = joblib.load(FEATURES_PATH)

print("✅ New Calibrated RF Login model loaded")

# ==========================
# 🧠 AI Phase 2: Load Isolation Forest for Continuous Monitoring
# ==========================
# In Zero Trust, we "Never Trust, Always Verify".
SESSION_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "session_model.pkl")
print("⚙️ Loading Isolation Forest for Continuous Monitoring...")
isolation_forest = joblib.load(SESSION_MODEL_PATH)
print("✅ Isolation Forest model loaded")

# ==========================
# Schemas
# ==========================
class SignupRequest(BaseModel):
    username: str
    password: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str
    hour: int | None = None
    day_of_week: int | None = None
    rtt: float | None = None
    asn: int | None = None
    ip_octet1: int | None = None
    country: str | None = None
    browser: str | None = None

class VerifyMFARequest(BaseModel):
    username: str
    otp: str

# ==========================
# Email utility
# ==========================
import threading

def _send_email_background(to_email: str, otp: str):
    """Sends OTP email in a background thread so it doesn't block the API response."""
    sender_email = os.getenv("SMTP_EMAIL")
    sender_password = os.getenv("SMTP_APP_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ ERROR: SMTP_EMAIL or SMTP_APP_PASSWORD missing in .env file!")
        return

    subject = "🔐 Your Zero Trust Login OTP"
    body = f"""
Hello,

Your One-Time Password (OTP) for Zero Trust login is:

    👉  {otp}

This OTP expires in 5 minutes. Do not share it with anyone.

— Zero Trust Security System
"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    # Try port 587 (STARTTLS) first — works on most networks
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
        print(f"✅ OTP email sent successfully to {to_email} (port 587)")
        return
    except Exception as e1:
        print(f"⚠️  Port 587 failed: {e1} — trying port 465...")

    # Fallback: try port 465 (SSL)
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [to_email], msg.as_string())
        print(f"✅ OTP email sent successfully to {to_email} (port 465)")
        return
    except Exception as e2:
        print(f"❌ Port 465 also failed: {e2}")
        print("❌ EMAIL NOT SENT. Check your Gmail App Password at:")
        print("   https://myaccount.google.com/apppasswords")

def send_otp_email(to_email: str, otp: str):
    """Non-blocking email sender — runs in background thread."""
    print(f"\n📧 [EMAIL SYSTEM] Sending OTP {otp} to {to_email}\n")
    thread = threading.Thread(target=_send_email_background, args=(to_email, otp))
    thread.daemon = True
    thread.start()

# ==========================
# Zero Trust Logic
# ==========================
def zero_trust_decision(risk: float) -> str:
    if risk < 0.30:
        return "ALLOW"
    elif risk < 0.70:
        return "MFA"
    return "BLOCK"

# ==========================
# Telemetry Simulation
# ==========================
def simulate_rtt(ip_octet1: int) -> float:
    return round(40 + ip_octet1 % 40 + random.uniform(5, 30), 2)

def simulate_asn(ip_octet1: int) -> int:
    return 20000 + (ip_octet1 * 37) % 4000

def simulate_country(ip_octet1: int) -> str:
    return "IN" if ip_octet1 < 128 else "OTHER"

# ==========================
# Health Check
# ==========================
@app.get("/")
def root():
    return {"message": "Backend running"}

# ==========================
# SIGNUP
# ==========================
@app.post("/signup")
def signup(data: SignupRequest, db: Session = Depends(get_db)):

    import re
    if len(data.password) <= 7 or len(data.password) > 15:
        raise HTTPException(status_code=400, detail="Password must be between 8 and 15 characters")
    if not re.search(r"[A-Z]", data.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
    if not re.search(r"\d", data.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", data.password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")

    existing_user = db.query(models.User).filter(
        models.User.username == data.username
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    existing_email = db.query(models.User).filter(
        models.User.email == data.email
    ).first()

    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = pwd_context.hash(data.password)

    new_user = models.User(
        username=data.username,
        email=data.email,
        password=hashed_password,
        role="user"

    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 🖨️ Print to terminal to show the user what it looks like!
    print(f"\n--- NEW USER CREATED ---")
    print(f"Username: {data.username}")
    print(f"Raw Password: {data.password}")
    print(f"Hashed Password saved to DB: {hashed_password}")
    print(f"------------------------\n")

    return {"message": "Signup successful", "username": data.username}


# ==========================
# DEBUG: list users (temporary)
# ==========================
@app.get("/debug/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.isoformat() if getattr(u, 'created_at', None) else None,
        })
    return result

# ==========================
# LOGIN + ML RISK EVALUATION
# ==========================
@app.post("/login-risk")
def login_risk(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        (models.User.username == data.username) |
        (models.User.email == data.username)
    ).first()

    if not user:
        print("USER NOT FOUND")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Access disabled by administrator"
        )

    print("USER FOUND:", user.username)
    print("TRUST FROM DB:", user.trust_score)
    print("ENTERED PASSWORD:", data.password)
    print("HASH IN DB:", user.password)

    if not verify_password(data.password, user.password):
        print("PASSWORD VERIFY FAILED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Step 2: Contextual Data Gathering
    hour = data.hour
    day_of_week = data.day_of_week

    client_ip = request.client.host
    try:
        if "." in client_ip:
            ip_octet1 = int(client_ip.split(".")[0])
        else:
            ip_octet1 = 127
    except:
        ip_octet1 = 127

    browser = (data.browser or "chrome").lower()
    browser_chrome = 1 if browser == "chrome" else 0
    browser_edge = 1 if browser == "edge" else 0
    browser_other = 1 if browser_chrome == 0 and browser_edge == 0 else 0

    rtt = data.rtt
    asn = data.asn
    ip_octet1 = data.ip_octet1
    country = data.country
    country_in = 1 if country == "IN" else 0

    # Step 3: Run Random Forest AI Prediction
    features = np.array([[
        rtt,
        asn,
        hour,
        day_of_week,
        ip_octet1,
        country_in,
        browser_chrome,
        browser_edge,
        browser_other
    ]])

    print("FEATURES USED:", features)

    risk_score = rf_model.predict_proba(features)[0][1]

    # Admin bypass
    if user.role and user.role.lower() == "admin":
        risk_score = 0.0
        decision = "ALLOW"
    else:
        decision = zero_trust_decision(risk_score)

    # Adaptive trust-based MFA / block
    if user.role.lower() != "admin" and user.trust_score is not None:
        if user.trust_score < 0.3:
            decision = "BLOCK"
        elif user.trust_score < 0.7 and decision == "ALLOW":
            decision = "MFA"

    # Initialize trust only once (do not overwrite session trust)
    if user.username.lower() != "tannu":
        if user.trust_score is None:
             user.trust_score = max(
            0.0,
            min(1.0, 1.0 - float(risk_score))
        )
        db.commit()

# refresh latest DB value
    db.refresh(user)

    print("DECISION:", decision)

    response_data = {
    "username": data.username,
    "role": user.role,
    "risk_score": round(float(risk_score), 4),
    "decision": decision,
    "current_trust": round(float(user.trust_score or 1.0), 2)
}

    # Step 4: Access Handling
    if decision == "ALLOW":
        access_token_expires = timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )

        response_data["access_token"] = access_token
        response_data["token_type"] = "bearer"

    elif decision == "MFA":
        otp_code = ''.join(
            random.choices(string.digits, k=6)
        )

        user.otp_code = otp_code
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=5)
        db.commit()

        send_otp_email(user.email, otp_code)

    elif decision == "BLOCK":
        if user.username.lower() != "tannu":
            user.is_active = False

            log_entry = models.SessionLog(
                user_id=user.id,
                ip_address=request.client.host,
                action="malicious_login_attempt",
                anomaly_score=float(risk_score)
            )

            db.add(log_entry)
            db.commit()
    print("FINAL TRUST SENT:", user.trust_score)
    print("FINAL DECISION:", decision)
    return response_data
# ==========================
# MFA VERIFICATION
# ==========================
@app.post("/verify-mfa")
def verify_mfa(data: VerifyMFARequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        (models.User.username == data.username) | (models.User.email == data.username)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if not user.otp_code or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="No OTP requested")
        
    if datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP expired")
        
    if user.otp_code != data.otp:
        raise HTTPException(status_code=401, detail="Invalid OTP")
        
    # Clear OTP
    user.otp_code = None
    user.otp_expires_at = None
    
    # Issue token since MFA passed
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    if user.trust_score < 1.0:
        user.trust_score = min(1.0, user.trust_score + 0.05)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "decision": "ALLOW"
    }

# ==========================
# CONTINUOUS MONITORING
# ==========================
class ActivityLog(BaseModel):
    action: str
    files_accessed: float
    data_transferred_mb: float

@app.post("/log-activity")
def log_activity(
    activity: ActivityLog,
    request: Request,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("LOG ROUTE HIT")

    # Re-fetch user in SAME db session
    db_user = db.query(models.User).filter(
        models.User.id == current_user.id
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if db_user.trust_score is None:
        db_user.trust_score = 1.0
        db.commit()

    now = datetime.utcnow()
    hour = now.hour
    day_of_week = now.weekday()
    is_weekend = 1 if day_of_week >= 5 else 0

    action = activity.action.lower()
    action_bulk = 1 if action == "bulk_download" else 0
    action_view = 1 if action == "view_file" else 0
    action_other = 1 if (action_bulk == 0 and action_view == 0) else 0

    files = float(activity.files_accessed)
    data_mb = float(activity.data_transferred_mb)
    mb_per_file = data_mb / max(files, 1)

    is_high_transfer = 1 if data_mb > 10 else 0
    is_many_files = 1 if files > 10 else 0

    trust = float(db_user.trust_score or 1.0)

    features = np.array([[
        files,
        data_mb,
        hour,
        day_of_week,
        is_weekend,
        action_bulk,
        action_view,
        action_other,
        mb_per_file,
        is_high_transfer,
        is_many_files,
        trust,
        float(hour) / 24.0,
        float(files) * data_mb
    ]])

    print("FEATURES:", features)

    is_anomaly = isolation_forest.predict(features)[0] == -1
    raw_score = isolation_forest.decision_function(features)[0]

    if is_anomaly:
        anomaly_score = min(1.0, abs(raw_score) * 2 + 0.5)
    else:
        anomaly_score = max(0.0, 0.2 - raw_score)

    if db_user.username.lower() != "tannu":

        recent_logs = db.query(models.SessionLog).filter(
            models.SessionLog.user_id == db_user.id
        ).order_by(
            models.SessionLog.timestamp.desc()
        ).limit(3).all()

        risk_streak = sum(
            1 for log in recent_logs
            if float(log.anomaly_score or 0) > 0.5
        )

        if anomaly_score > 0.5:
            risk_streak += 1

        same_action_streak = 0
        for log in recent_logs:
            if (log.action or "").lower() == action:
                same_action_streak += 1
            else:
                break

        penalty = 0.0

        if anomaly_score > 0.75:
            penalty = 0.25
        elif anomaly_score > 0.50:
            penalty = 0.15
        elif anomaly_score > 0.30:
            penalty = 0.07

        if action == "bulk_download":
            penalty += 0.10

        penalty += risk_streak * 0.06

        if action == "bulk_download":
            penalty += same_action_streak * 0.08

        if penalty > 0:
            db_user.trust_score = max(
                0.0,
                db_user.trust_score - penalty
            )
        else:
            recovery = 0.001
            db_user.trust_score = min(
                1.0,
                db_user.trust_score + recovery
            )

    log_entry = models.SessionLog(
        user_id=db_user.id,
        ip_address=request.client.host,
        action=activity.action,
        anomaly_score=float(anomaly_score)
    )

    db.add(log_entry)
    db.commit()

    print("TRUST:", db_user.trust_score)

    if db_user.trust_score < 0.3:
        db_user.is_active = False
        db.commit()

        return {
            "status": "blocked",
            "message": "Account suspended due to abnormal activity.",
            "current_trust": 0
        }

    return {
        "status": "ok",
        "anomaly_score": round(float(anomaly_score), 4),
        "current_trust": round(float(db_user.trust_score), 2)
    }
# ==========================
# ADMIN DASHBOARD STATS
# ==========================
@app.get("/admin/stats")
def get_admin_stats(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.role or current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = db.query(models.User).all()
    logs = db.query(models.SessionLog).order_by(models.SessionLog.timestamp.desc()).limit(50).all()

    insights = []
    for u in users:
        user_logs = [l for l in logs if l.user_id == u.id]
        user_logs.sort(key=lambda x: x.timestamp or datetime.utcnow(), reverse=True)

        # Login Time Anomaly: any suspicious event during uncommon hours.
        unusual_login = any(
            (l.action == "malicious_login_attempt") and l.timestamp and (l.timestamp.hour < 6 or l.timestamp.hour >= 23)
            for l in user_logs
        )

        # Location Change: check whether multiple source IPs are observed for this user.
        ip_set = {l.ip_address for l in user_logs if l.ip_address}
        location_change = len(ip_set) > 1

        avg_anomaly = (
            sum(float(l.anomaly_score or 0.0) for l in user_logs) / len(user_logs)
            if user_logs else 0.0
        )

        if not u.is_active:
            prediction = "High Risk"
            recommendation = "Keep blocked and investigate account activity."
        elif avg_anomaly >= 0.6 or u.trust_score < 0.4:
            prediction = "Likely Threat"
            recommendation = "Step-up authentication and monitor all actions."
        elif avg_anomaly >= 0.3 or u.trust_score < 0.7:
            prediction = "Elevated Risk"
            recommendation = "Require MFA and watch for location/time drift."
        else:
            prediction = "Normal"
            recommendation = "Allow access with routine monitoring."

        trust_pct = round(float(u.trust_score or 0.0) * 100)
        risk_pct = max(0, min(100, 100 - trust_pct))
        confidence_pct = round(min(100.0, max(40.0, (avg_anomaly * 100) + (risk_pct * 0.5))))

        insights.append({
            "username": u.username,
            "login_time_anomaly": "Yes" if unusual_login else "No",
            "location_change": "Yes" if location_change else "No",
            "prediction": prediction,
            "ai_recommendation": recommendation,
            "trust_breakdown": {
                "trust_percent": trust_pct,
                "risk_percent": risk_pct,
                "model_confidence_percent": confidence_pct
            }
        })
    
    return {
        "users": [{"username": u.username, "role": u.role, "trust_score": u.trust_score, "is_active": u.is_active} for u in users],
        "recent_anomalies": [{"username": l.user.username if l.user else "Unknown", "action": l.action, "anomaly_score": l.anomaly_score, "time": l.timestamp} for l in logs if l.anomaly_score > 0.5],
        "ai_insights": insights
    }

# ==========================
# ADMIN ROLE MANAGEMENT
# ==========================
@app.post("/admin/promote-user/{username}")
def promote_user(username: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.role or current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can grant admin rights")
    
    target_user = db.query(models.User).filter(models.User.username == username).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    target_user.role = "admin"
    db.commit()
    return {"message": f"{username} has been promoted to admin"}

@app.post("/admin/revoke-user/{username}")
def revoke_admin(
    username: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.role or current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can modify admin rights"
        )

    if username.lower() == "tannu":
        raise HTTPException(
            status_code=403,
            detail="Cannot revoke rights of the permanent Super Admin"
        )

    target_user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if current_user.username == target_user.username:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke your own admin rights"
        )

    target_user.role = "user"
    target_user.is_active = False
    target_user.trust_score = 0.0

    db.commit()

    return {
        "message": f"{username} access revoked successfully"
    }

@app.post("/admin/toggle-block/{username}")
def toggle_block(username: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.role or current_user.role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admins can block/unblock users")
    if username.lower() == "tannu":
        raise HTTPException(status_code=403, detail="Cannot block the permanent Super Admin")
        
    target_user = db.query(models.User).filter(models.User.username == username).first()
    if not target_user: raise HTTPException(status_code=404, detail="User not found")
    if current_user.username == target_user.username: raise HTTPException(status_code=400, detail="Cannot block yourself")
    target_user.is_active = not target_user.is_active
    db.commit()
    return {"message": "Success"}