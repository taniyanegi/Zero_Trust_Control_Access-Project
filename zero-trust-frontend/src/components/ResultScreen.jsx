import React from "react";
import safeBg from "../assets/safe.jpeg";
import dangerBg from "../assets/danger.jpeg";
import afterLoginBG from "../assets/afterLoginBG.png";

function ResultScreen({
  decision,
  riskScore,
  trustScore,
  onLogout,
  onProceed
}) {
  const backgroundImage =
    decision === "ALLOW"
      ? safeBg
      : decision === "BLOCK"
      ? dangerBg
      : afterLoginBG;

  const getStyle = () => {
    if (decision === "ALLOW") return { color: "#4ade80" };
    if (decision === "BLOCK") return { color: "#ef4444" };
    return { color: "#facc15" };
  };

  const trustPercent = Math.round((trustScore || 1) * 100);

  const getTrustColor = () => {
    if (trustPercent >= 70) return "#4ade80";
    if (trustPercent >= 30) return "#facc15";
    return "#ef4444";
  };

  return (
    <div
      style={{
        height: "100vh",
        width: "100vw",
        backgroundImage: `url(${backgroundImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundAttachment: "fixed",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={styles.container}>
        <h1 style={{ ...styles.decisionText, ...getStyle() }}>
          {decision}
        </h1>

        <p style={styles.riskText}>
          Risk Score: <strong>{(riskScore * 100).toFixed(2)}%</strong>
        </p>

        <p
          style={{
            ...styles.trustText,
            color: getTrustColor()
          }}
        >
          Trust Score: <strong>{trustPercent}%</strong>
        </p>

        {decision === "ALLOW" && (
          <>
            <p style={styles.statusText}>✅ Access Granted</p>

            <button
              style={{
                ...styles.actionButton,
                background: "rgba(74, 222, 128, 0.2)",
                color: "#4ade80",
                border: "1px solid #4ade80"
              }}
              onClick={onProceed}
            >
              Proceed to Dashboard
            </button>
          </>
        )}

        {decision === "BLOCK" && (
          <>
            <p style={styles.statusText}>⛔ Access Denied</p>
          </>
        )}

        {decision === "MFA" && (
          <>
            <p style={styles.statusText}>
              🔐 Additional Verification Required.
            </p>

            <button
              style={{
                ...styles.actionButton,
                background: "rgba(250, 204, 21, 0.2)",
                color: "#facc15",
                border: "1px solid #facc15"
              }}
              onClick={onProceed}
            >
              Enter OTP
            </button>
          </>
        )}

        {onLogout && (
          <button
            style={styles.logoutButton}
            onClick={onLogout}
          >
            Logout
          </button>
        )}
      </div>
    </div>
  );
}

export default ResultScreen;

const styles = {
  container: {
    width: "430px",
    padding: "40px",
    borderRadius: "18px",
    background: "rgba(0, 0, 0, 0.72)",
    backdropFilter: "blur(14px)",
    boxShadow: "0 0 50px rgba(0, 150, 255, 0.45)",
    textAlign: "center",
    color: "#ffffff",
  },

  decisionText: {
    fontSize: "46px",
    fontWeight: "800",
    marginBottom: "14px",
    letterSpacing: "2px",
  },

  riskText: {
    fontSize: "22px",
    marginBottom: "10px",
    color: "#e5e7eb",
  },

  trustText: {
    fontSize: "22px",
    marginBottom: "22px",
    fontWeight: "700",
  },

  statusText: {
    fontSize: "26px",
    fontWeight: "700",
    marginBottom: "24px",
  },

  actionButton: {
    padding: "12px 24px",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "18px",
    fontWeight: "700",
    transition: "0.3s",
    marginRight: "10px",
  },

  logoutButton: {
    marginTop: "18px",
    padding: "12px 24px",
    backgroundColor: "transparent",
    color: "#ef4444",
    border: "1px solid #ef4444",
    borderRadius: "10px",
    cursor: "pointer",
    fontSize: "17px",
    fontWeight: "700",
    transition: "0.3s",
  },
};