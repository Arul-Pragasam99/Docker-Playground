"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";

interface HistoryItem {
  id: string;
  command: string;
  valid: boolean;
  timestamp: string;
}

interface HistoryPanelProps {
  history: HistoryItem[];
  onSelect: (cmd: string) => void;
  onClear: () => void;
  sessionId: string;
}

export default function HistoryPanel({
  history,
  onSelect,
  onClear,
  sessionId,
}: HistoryPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    gsap.fromTo(
      panelRef.current,
      { opacity: 0, x: 24 },
      { opacity: 1, x: 0, duration: 0.7, delay: 0.5, ease: "power3.out" }
    );
  }, []);

  useEffect(() => {
    if (history.length === 0) return;
    gsap.fromTo(
      ".history-item:first-child",
      { opacity: 0, x: 12 },
      { opacity: 1, x: 0, duration: 0.35, ease: "power2.out" }
    );
  }, [history.length]);

  return (
    <aside className="history-panel" ref={panelRef}>
      <div className="history-header">
        <span className="history-title">Session History</span>
        {history.length > 0 && (
          <button className="btn-clear" onClick={onClear} title="Clear history">
            Clear
          </button>
        )}
      </div>

      <div className="session-id">
        <span className="sid-label">Session</span>
        <code className="sid-value">
          {sessionId ? sessionId.slice(0, 8) + "…" : "———"}
        </code>
      </div>

      {history.length === 0 ? (
        <div className="history-empty">
          <span className="empty-icon">🐳</span>
          <p>No commands yet.</p>
          <p className="empty-sub">Validated commands will appear here.</p>
        </div>
      ) : (
        <ul className="history-list">
          {history.map((item) => (
            <li
              key={item.id}
              className="history-item"
              onClick={() => onSelect(item.command)}
              title={item.command}
            >
              <div className="hi-top">
                <span className={`hi-dot ${item.valid ? "dot-ok" : "dot-err"}`} />
                <code className="hi-cmd">
                  docker {item.command.length > 36 ? item.command.slice(0, 36) + "…" : item.command}
                </code>
              </div>
              <span className="hi-time">{new Date(item.timestamp).toLocaleTimeString()}</span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}