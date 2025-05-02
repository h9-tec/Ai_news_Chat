import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from 'react-markdown';

const API_BASE = "http://localhost:8001";

function parseEmojis(text) {
  return text
    .replace(/:smile:/g, "😊")
    .replace(/:rocket:/g, "🚀")
    .replace(/:robot:/g, "🤖")
    .replace(/:star:/g, "⭐")
    .replace(/:fire:/g, "🔥");
}

function isArabic(text) {
  return /[\u0600-\u06FF]/.test(text);
}

const AVATAR_AI = "https://api.dicebear.com/7.x/bottts/svg?seed=ai";
const AVATAR_USER = "https://api.dicebear.com/7.x/personas/svg?seed=user";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages, loading]);

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus();
  }, [loading]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { role: "user", content: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setLoading(true);
    setInput("");
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: input, backend: "groq" }),
      });
      const data = await res.json();
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: data.response }
      ]);
    } catch {
      setMessages((msgs) => [
        ...msgs,
        { role: "assistant", content: "Error. Please try again." }
      ]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(e);
    }
  };

  return (
    <div className="chat-fancy-bg" style={{minHeight: '100vh', display: 'flex', flexDirection: 'column', position: 'relative'}}>
      {/* Subtle overlay for depth */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        pointerEvents: 'none',
        background: 'radial-gradient(circle at 70% 20%, rgba(255,255,255,0.04) 0%, rgba(79,140,255,0.08) 100%)',
        zIndex: 0
      }} />
      <header className="chat-fancy-header" style={{zIndex: 1}}>
        <img src={AVATAR_AI} alt="AI Avatar" className="chat-fancy-avatar" />
        <span className="chat-fancy-title">AI News Chatbot</span>
      </header>
      <main
        className="chat-fancy-main"
        ref={chatRef}
        style={{
          flex: 1,
          minHeight: 0,
          zIndex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          width: '100%',
          maxWidth: '820px',
          margin: '0 auto',
          padding: '2.5rem 1.5vw 2.5rem 1.5vw',
        }}
      >
        {messages.length === 0 && (
          <div className="chat-fancy-empty">Ask me anything about AI news! 🚀</div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={
              msg.role === "user"
                ? "chat-fancy-msg chat-fancy-msg-user"
                : "chat-fancy-msg chat-fancy-msg-ai"
            }
            dir={msg.role === "assistant" && isArabic(msg.content) ? "rtl" : "ltr"}
            style={{width: '100%'}}
          >
            <img
              src={msg.role === "user" ? AVATAR_USER : AVATAR_AI}
              alt={msg.role}
              className="chat-fancy-msg-avatar"
            />
            <div className="chat-fancy-msg-bubble">
              <ReactMarkdown>{parseEmojis(msg.content)}</ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-fancy-msg chat-fancy-msg-ai">
            <img src={AVATAR_AI} alt="AI Avatar" className="chat-fancy-msg-avatar" />
            <div className="chat-fancy-msg-bubble chat-new-loading">
              <span className="dot-flashing"></span>
            </div>
          </div>
        )}
      </main>
      <form
        className="chat-fancy-inputbar"
        onSubmit={sendMessage}
        style={{marginTop: 'auto', zIndex: 1}}
        aria-label="Send a message to the AI chatbot"
      >
        <input
          type="text"
          placeholder="Type your question..."
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
          ref={inputRef}
          onKeyDown={handleKeyDown}
          autoComplete="off"
          aria-label="Chat input"
          style={{fontSize: '1.15rem'}}
        />
        <button
          type="submit"
          className="primary-btn"
          disabled={loading || !input.trim()}
          aria-label="Send message"
          style={{fontSize: '1.15rem'}}
        >
          Send
        </button>
      </form>
      <div className="footer" style={{zIndex: 1}}>
        © {new Date().getFullYear()} AI News Aggregator. All rights reserved.
      </div>
      {/* Responsive tweaks for mobile */}
      <style>{`
        @media (max-width: 600px) {
          .chat-fancy-main {
            max-width: 99vw !important;
            padding-left: 2vw !important;
            padding-right: 2vw !important;
          }
          .chat-fancy-msg-bubble {
            max-width: 95vw !important;
            font-size: 1rem !important;
            padding: 0.8rem 0.9rem !important;
          }
          .chat-fancy-header {
            padding: 1rem 1vw !important;
          }
          .chat-fancy-inputbar {
            max-width: 99vw !important;
            padding-left: 2vw !important;
            padding-right: 2vw !important;
          }
        }
      `}</style>
    </div>
  );
} 