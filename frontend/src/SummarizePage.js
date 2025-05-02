import React, { useState, useEffect } from "react";
import ReactMarkdown from 'react-markdown';

const API_BASE = "http://localhost:8001";

function SummarizePage() {
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState("");

  useEffect(() => {
    const fetchSummary = async () => {
      setSummaryLoading(true);
      setSummaryError("");
      setSummary("");
      try {
        const res = await fetch(`${API_BASE}/summarize`);
        const data = await res.json();
        setSummary(data.summary || "No summary available.");
      } catch (err) {
        setSummaryError("Error fetching summary. Please try again.");
      }
      setSummaryLoading(false);
    };
    fetchSummary();
  }, []);

  return (
    <div className="summarize-root">
      <h2>Latest AI News Summary</h2>
      <div className="summary-content">
        {summaryLoading && <div>Loading summary...</div>}
        {summaryError && <div className="status-msg error">{summaryError}</div>}
        {summary && <ReactMarkdown>{summary}</ReactMarkdown>}
      </div>
      <div className="footer">© {new Date().getFullYear()} AI News Aggregator. All rights reserved.</div>
    </div>
  );
}

export default SummarizePage; 