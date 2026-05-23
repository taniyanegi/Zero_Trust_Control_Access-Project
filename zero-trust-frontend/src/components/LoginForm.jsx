import React, { useState } from "react";
import "./LoginForm.css";
import bgImage from "../assets/bg.png";

function LoginForm({ onLogin, onSignup, loginType, onBack, error }){
  const [username, setUsername] = useState(localStorage.getItem("rememberUser") || "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    const now = new Date();
    const day = now.getDay();
/*
const zeroTrustPayload = {
  username: username,
  password: password,
  rtt: 50,
  asn: 24560,
  hour: 10,
  day_of_week: 1,
  ip_octet1: 80,
  country: "IN",
  browser: "Chrome",
};
*/
/*
==============================
MFA TEST PAYLOAD
==============================
*/

const zeroTrustPayload = {
  username: username,
  password: password,
  rtt: 180,
  asn: 60000,
  hour: 2,
  day_of_week: 3,
  ip_octet1: 150,
  country: "US",
  browser: "Chrome",
};



/*
==============================
BLOCK TEST PAYLOAD
==============================
*/
/*
const zeroTrustPayload = {
  username: username,
  password: password,
  rtt: 500,
  asn: 390000,
  hour: 3,
  day_of_week: 0,
  ip_octet1: 220,
  country: "US",
  browser: "Other",
};*/
/*
Expected Result: BLOCK
*/
console.log(zeroTrustPayload);
    if (rememberMe) {
      localStorage.setItem("rememberUser", username);
    } else {
      localStorage.removeItem("rememberUser");
    }

    await onLogin(zeroTrustPayload);
    setLoading(false);
  };

  return (
    <div
      className="login-background"
      style={{ backgroundImage: `url(${bgImage})` }}
    >
      <div className="login-card">

        <div className="input-box">
          <span className="icon">👤</span>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </div>

        <div className="input-box">
          <span className="icon">🔒</span>
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <span
            className="icon"
            onClick={() => setShowPassword(!showPassword)}
            style={{ cursor: "pointer" }}
          >
            {showPassword ? "🙈" : "👁️"}
          </span>
        </div>

        <div className="options">
          <label>
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={() => setRememberMe(!rememberMe)}
            />
            Remember Me
          </label>
        </div>
        {error && (
  <p
    style={{
      color: "#ff4d4f",
      textAlign: "center",
      marginTop: "10px",
      fontWeight: "600"
    }}
  >
    {error}
  </p>
)}
        <button 
          className="login-btn" 
          onClick={handleLogin} 
          disabled={loading}
          style={loginType === 'ADMIN' ? { background: 'linear-gradient(to right, #8e2de2, #4a00e0)' } : {}}
        >
          {loading ? "Logging in..." : `LOGIN AS ${loginType}`}
        </button>

        <p className="signup-text">
          Don’t have an account?{" "}
          <span className="signup-link" onClick={onSignup}>
            Create Account
          </span>
        </p>
        
        <p className="signup-text" style={{ marginTop: '10px' }}>
          <span className="signup-link" onClick={onBack}>
            ← Back to Portal Selection
          </span>
        </p>

      </div>
    </div>
  );
}

export default LoginForm;