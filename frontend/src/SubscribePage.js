import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

function SubscribePage() {
  const [email, setEmail] = useState("");
  const [msg, setMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubscribe = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMsg("");
    try {
      const res = await fetch(`${API_BASE}/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      setMsg(data.message || "Subscription request sent.");
    } catch (err) {
      setMsg("Error subscribing. Please try again.");
    }
    setSubmitting(false);
  };

  return (
    <div className="feature-page">
      <h2>Subscribe to Weekly Digest</h2>
      <form className="modal-content" onSubmit={handleSubscribe} style={{maxWidth: 400, margin: "2rem auto"}}>
        <input
          type="email"
          placeholder="Your email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          disabled={submitting}
        />
        <button className="primary-btn" type="submit" disabled={submitting}>
          {submitting ? "Subscribing..." : "Subscribe"}
        </button>
        {msg && <div className="status-msg">{msg}</div>}
      </form>
    </div>
  );
}

export default SubscribePage; 