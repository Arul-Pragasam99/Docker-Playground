"use client";

import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";

interface FlagInfo {
  flag: string;
  value?: string;
  description: string;
  category: string;
}

interface ValidationResult {
  valid: boolean;
  command: string;
  subcommand: string;
  confidence: number;
  flags: FlagInfo[];
  typos: { original: string; suggestion: string; message: string }[];
  pro_tips: string[];
  summary: string;
  error?: string;
}

interface ResultCardProps {
  result: ValidationResult | null;
  loading: boolean;
}

const CATEGORY_COLORS: Record<string, string> = {
  network: "#3b82f6",
  volume: "#8b5cf6",
  execution: "#10b981",
  resource: "#f59e0b",
  output: "#06b6d4",
  build: "#f97316",
  image: "#ec4899",
  container: "#84cc16",
  other: "#6b7280",
};

export default function ResultCard({ result, loading }: ResultCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!cardRef.current) return;
    if (loading) {
      gsap.fromTo(
        cardRef.current,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }
      );
    }
  }, [loading]);

  useEffect(() => {
    if (!result || !cardRef.current) return;
    setCollapsed(false);

    const ctx = gsap.context(() => {
      gsap.fromTo(
        cardRef.current,
        { opacity: 0, y: 20, scale: 0.98 },
        { opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "power3.out" }
      );
      gsap.fromTo(
        ".flag-row",
        { opacity: 0, x: -12 },
        {
          opacity: 1,
          x: 0,
          stagger: 0.06,
          delay: 0.2,
          duration: 0.4,
          ease: "power2.out",
        }
      );
      gsap.fromTo(
        ".tip-item",
        { opacity: 0, y: 8 },
        {
          opacity: 1,
          y: 0,
          stagger: 0.08,
          delay: 0.3,
          duration: 0.35,
          ease: "power2.out",
        }
      );
    });
    return () => ctx.revert();
  }, [result]);

  if (loading) {
    return (
      <div className="result-card skeleton-card" ref={cardRef}>
        <div className="skeleton-line w-40" />
        <div className="skeleton-line w-full" />
        <div className="skeleton-line w-3/4" />
        <div className="skeleton-grid">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="skeleton-flag" />
          ))}
        </div>
      </div>
    );
  }

  if (!result) return null;

  const confidencePct = Math.round(result.confidence * 100);
  const confColor =
    confidencePct >= 80 ? "#10b981" : confidencePct >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div
      className={`result-card ${result.valid ? "card-valid" : "card-invalid"} ${collapsed ? "card-collapsed" : ""}`}
      ref={cardRef}
    >
      {/* Card header */}
      <div className="card-header" onClick={() => setCollapsed((c) => !c)}>
        <div className="card-status">
          <span className={`status-icon ${result.valid ? "icon-ok" : "icon-err"}`}>
            {result.valid ? "✓" : "✗"}
          </span>
          <div className="card-title-group">
            <span className="card-subcommand">docker {result.subcommand}</span>
            <span className="card-validity">{result.valid ? "Valid command" : "Invalid / needs review"}</span>
          </div>
        </div>
        <div className="card-meta">
          <span className="conf-badge" style={{ color: confColor, borderColor: confColor }}>
            {confidencePct}% confidence
          </span>
          <span className="collapse-toggle">{collapsed ? "▼" : "▲"}</span>
        </div>
      </div>

      {!collapsed && (
        <div className="card-body">
          {/* Summary */}
          <p className="card-summary">{result.summary}</p>

          {/* Typos */}
          {result.typos && result.typos.length > 0 && (
            <div className="section typo-section">
              <h3 className="section-title">⚠ Typos / Corrections</h3>
              {result.typos.map((t, i) => (
                <div key={i} className="typo-row">
                  <span className="typo-orig">{t.original}</span>
                  <span className="typo-arrow">→</span>
                  <span className="typo-sug">{t.suggestion}</span>
                  <span className="typo-msg">{t.message}</span>
                </div>
              ))}
            </div>
          )}

          {/* Flags breakdown */}
          {result.flags && result.flags.length > 0 && (
            <div className="section">
              <h3 className="section-title">🚩 Flag Breakdown</h3>
              <div className="flags-grid">
                {result.flags.map((f, i) => {
                  const cat = f.category?.toLowerCase() || "other";
                  const color = CATEGORY_COLORS[cat] || CATEGORY_COLORS.other;
                  return (
                    <div key={i} className="flag-row" style={{ "--flag-color": color } as React.CSSProperties}>
                      <div className="flag-top">
                        <code className="flag-name">{f.flag}</code>
                        {f.value && <span className="flag-value">{f.value}</span>}
                        <span className="flag-category" style={{ color }}>
                          {f.category}
                        </span>
                      </div>
                      <p className="flag-desc">{f.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Pro tips */}
          {result.pro_tips && result.pro_tips.length > 0 && (
            <div className="section">
              <h3 className="section-title">💡 Pro Tips</h3>
              <ul className="tips-list">
                {result.pro_tips.map((tip, i) => (
                  <li key={i} className="tip-item">
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Error */}
          {result.error && (
            <div className="error-block">
              <span className="error-icon">⚠</span> {result.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
