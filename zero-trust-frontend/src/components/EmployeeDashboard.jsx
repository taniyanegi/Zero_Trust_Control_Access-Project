// Replace your current EmployeeDashboard.jsx with this updated version

import React, { useState } from "react";
import axios from "axios";
import "./EmployeeDashboard.css";
function EmployeeDashboard({ token, onLogout, initialTrust }) {
  const [trust, setTrust] = useState(
  Math.round((initialTrust || 1) * 100)
);
  const [logs, setLogs] = useState([]);

  const sendActivity = async (action, files, mb) => {
    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/log-activity",
        {
          action,
          files_accessed: files,
          data_transferred_mb: mb,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const currentTrust = Math.round(
        (res.data.current_trust || 1) * 100
      );

      setTrust(currentTrust);

      setLogs((prev) => [
        {
          time: new Date().toLocaleTimeString(),
          action,
          trust: currentTrust,
          status: res.data.status,
        },
        ...prev,
      ]);

      if (res.data.status === "blocked") {
        alert("🚨 Session terminated due to suspicious behavior.");
        onLogout();
      } else if ((res.data.anomaly_score || 0) > 0.6) {
        alert("⚠ High Risk Activity Detected!");
      }

    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="cyber-page">
      <div className="sidebar">
        <h2>⚡ ZeroTA</h2>

        <button onClick={() => sendActivity("view_file", 1, 0.2)}>
          📁 My Files
        </button>

        <button onClick={() => sendActivity("view_file", 2, 0.5)}>
          👥 HR Folder
        </button>

        <button onClick={() => sendActivity("view_file", 4, 2)}>
          💰 Finance Reports
        </button>

        <button onClick={() => sendActivity("bulk_download", 25, 40)}>
          ⬇️ Download Center
        </button>

        <button onClick={() => sendActivity("upload_data", 3, 8)}>
          ⬆️ Upload Area
        </button>

        <button className="logout-btn" onClick={onLogout}>
          🚪 Logout
        </button>
      </div>

      <div className="main-panel">
        <div className="top-bar">
          <h1>Employee Security Portal</h1>

          <div className="trust-box">
            <span>Trust Score</span>

            <div className="trust-bar">
              <div
                className="trust-fill"
                style={{ width: `${trust}%` }}
              ></div>
            </div>

            <strong>{trust}%</strong>
          </div>
        </div>

        <div className="cards">

          <div
            className="card"
            onClick={() => sendActivity("view_file", 1, 0.2)}
          >
            <h3>📄 Resume.pdf</h3>
            <p>Secure personal file</p>
          </div>

          <div
            className="card"
            onClick={() => sendActivity("view_file", 2, 0.5)}
          >
            <h3>👥 EmployeeRecords.xlsx</h3>
            <p>Restricted HR data</p>
          </div>

          <div
            className="card danger"
            onClick={() => sendActivity("bulk_download", 50, 100)}
          >
            <h3>🚨 Export Payroll.zip</h3>
            <p>High-risk finance action</p>
          </div>

          <div
            className="card"
            onClick={() => sendActivity("upload_data", 3, 8)}
          >
            <h3>☁ Upload Reports</h3>
            <p>Send internal documents</p>
          </div>

        </div>

        <div className="activity-panel">
          <h2>📜 Live Activity Feed</h2>

          {logs.length === 0 ? (
            <p>No activity yet...</p>
          ) : (
            logs.map((log, i) => (
              <div
                className={`log-row ${
                  log.trust < 40
                    ? "danger-log"
                    : log.trust < 70
                    ? "warn-log"
                    : "safe-log"
                }`}
                key={i}
              >
                <span>{log.time} • {log.action}</span>
                <span>{log.status} • {log.trust}%</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default EmployeeDashboard;