import React from "react";
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import "./App.css";
import ChatPage from "./ChatPage";
import SubscribePage from "./SubscribePage";
import SummarizePage from "./SummarizePage";

const API_BASE = "http://localhost:8000";

function Landing() {
  const navigate = useNavigate();
  return (
    <div>
      <header className="hero">
        <h1>Stay Ahead with the Latest AI News</h1>
        <p>Curated weekly digests, smart summaries, and interactive AI chat—all in one place.</p>
      </header>
      <main className="features">
        <section className="feature-card" id="subscribe">
          <h2>📬 Subscribe</h2>
          <p>Get weekly AI news digests delivered to your inbox. Never miss an update!</p>
          <button className="primary-btn" onClick={() => navigate("/subscribe")}>Subscribe Now</button>
        </section>
        <section className="feature-card" id="chat">
          <h2>💬 Chat</h2>
          <p>Ask our AI chatbot about the latest trends, tools, and breakthroughs in AI.</p>
          <button className="primary-btn" onClick={() => navigate("/chat")}>Start Chatting</button>
        </section>
        <section className="feature-card" id="summarize">
          <h2>📝 Summarize</h2>
          <p>Read concise, expert summaries of the most important AI news stories.</p>
          <button className="primary-btn" onClick={() => navigate("/summarize")}>View Summary</button>
        </section>
      </main>
    </div>
  );
}

function isArabic(text) {
  // Check if text contains Arabic characters
  return /[\u0600-\u06FF]/.test(text);
}

function parseEmojis(text) {
  // Replace :emoji: with actual emoji (simple demo)
  return text
    .replace(/:smile:/g, "😊")
    .replace(/:rocket:/g, "🚀")
    .replace(/:robot:/g, "🤖")
    .replace(/:star:/g, "⭐")
    .replace(/:fire:/g, "🔥");
}

function formatAiResponse(text) {
  // Split by lines, look for lines starting with - or * or numbered lists
  const lines = text.split(/\r?\n/).filter(line => line.trim() !== "");
  // If most lines look like bullets or numbered, render as a list
  const bulletLines = lines.filter(line => /^[-*•\d+\.]/.test(line.trim()));
  if (bulletLines.length > 2) {
    return (
      <ul className="ai-bullet-list">
        {lines.map((line, idx) => (
          /^[-*•\d+\.]/.test(line.trim()) ? (
            <li key={idx}><span role="img" aria-label="bullet">•</span> {parseEmojis(line.replace(/^[-*•\d+\.]+/, "").trim())}</li>
          ) : null
        ))}
      </ul>
    );
  }
  // Otherwise, render as paragraphs, but highlight bullets if present
  return lines.map((line, idx) => {
    if (/^[-*•\d+\.]/.test(line.trim())) {
      return <div key={idx} className="ai-bullet-line"><span role="img" aria-label="bullet">•</span> {parseEmojis(line.replace(/^[-*•\d+\.]+/, "").trim())}</div>;
    }
    return <div key={idx}>{parseEmojis(line)}</div>;
  });
}

function App() {
  const location = useLocation();
  return (
    <div className="App">
      <nav className="navbar">
        <div className="navbar-logo">📰 AI News Aggregator</div>
        <div className="navbar-links">
          <NavLinkBtn to="/subscribe">Subscribe</NavLinkBtn>
          <NavLinkBtn to="/chat">Chat</NavLinkBtn>
          <NavLinkBtn to="/summarize">Summarize</NavLinkBtn>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/subscribe" element={<SubscribePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/summarize" element={<SummarizePage />} />
      </Routes>
      {location.pathname !== "/summarize" && (
        <footer className="footer">
          <p>© {new Date().getFullYear()} AI News Aggregator. All rights reserved.</p>
        </footer>
      )}
    </div>
  );
}

function NavLinkBtn({ to, children }) {
  const navigate = useNavigate();
  return (
    <a href={to} onClick={e => { e.preventDefault(); navigate(to); }}>
      {children}
    </a>
  );
}

export default function AppWithRouter() {
  return (
    <Router>
      <App />
    </Router>
  );
}
