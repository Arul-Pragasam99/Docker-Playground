"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import Terminal from "@/components/Terminal";
import ResultCard from "@/components/ResultCard";
import HistoryPanel from "@/components/HistoryPanel";
import { useDockerPlayground } from "@/hooks/useDockerPlayground";

export default function Home() {
  const headerRef = useRef<HTMLDivElement>(null);
  const mainRef = useRef<HTMLDivElement>(null);

  const {
    command,
    setCommand,
    result,
    loading,
    history,
    sessionId,
    historyIndex,
    validate,
    clearHistory,
    navigateHistory,
  } = useDockerPlayground();

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".header-badge",
        { opacity: 0, y: -20 },
        { opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }
      );
      gsap.fromTo(
        ".header-title",
        { opacity: 0, y: 30, skewX: -3 },
        { opacity: 1, y: 0, skewX: 0, duration: 0.8, delay: 0.15, ease: "power3.out" }
      );
      gsap.fromTo(
        ".header-sub",
        { opacity: 0, y: 15 },
        { opacity: 1, y: 0, duration: 0.6, delay: 0.35, ease: "power3.out" }
      );
      gsap.fromTo(
        ".stat-pill",
        { opacity: 0, scale: 0.85 },
        {
          opacity: 1,
          scale: 1,
          duration: 0.45,
          stagger: 0.1,
          delay: 0.5,
          ease: "back.out(1.7)",
        }
      );
      gsap.fromTo(
        mainRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.7, delay: 0.6, ease: "power3.out" }
      );
    });
    return () => ctx.revert();
  }, []);

  return (
    <div className="app-shell">
      {/* Ambient background */}
      <div className="bg-grid" />
      <div className="bg-glow" />

      {/* Header */}
      <header className="app-header" ref={headerRef}>
        <div className="header-inner">
          <span className="header-badge">
            <span className="badge-dot" />
            AI Powered
          </span>
          <h1 className="header-title">Docker Playground</h1>
          <p className="header-sub">
            Paste any Docker command — get a full breakdown of every flag, typo checks, and pro tips.
          </p>
          <div className="stat-row">
            {["Flag Breakdown", "Typo Detection", "Pro Tips", "Session History"].map((s) => (
              <span key={s} className="stat-pill">
                {s}
              </span>
            ))}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="app-main" ref={mainRef}>
        <div className="layout-grid">
          {/* Left: Terminal + Result */}
          <div className="center-col">
            <Terminal
              command={command}
              setCommand={setCommand}
              onSubmit={validate}
              loading={loading}
              onNavigateHistory={navigateHistory}
            />
            {(result || loading) && (
              <ResultCard result={result} loading={loading} />
            )}
          </div>

          {/* Right: History */}
          <HistoryPanel
            history={history}
            onSelect={setCommand}
            onClear={clearHistory}
            sessionId={sessionId}
          />
        </div>
      </main>

      <footer className="app-footer">
        <span>Docker Playground · Command Validator</span>
      </footer>
    </div>
  );
}