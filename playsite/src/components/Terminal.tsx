"use client";

import { useEffect, useRef, KeyboardEvent } from "react";
import { gsap } from "gsap";

interface TerminalProps {
  command: string;
  setCommand: (v: string) => void;
  onSubmit: () => void;
  loading: boolean;
  onNavigateHistory: (dir: "up" | "down") => void;
}

const CHIPS = [
  "docker run -d -p 8080:80 --name web nginx",
  "docker build -t myapp:latest -f Dockerfile .",
  "docker run --rm -v $(pwd):/app -w /app node:18 npm install",
  "docker network create --driver bridge mynet",
  "docker run -e NODE_ENV=production --memory 512m myapp",
  "docker ps -a --filter status=exited",
];

export default function Terminal({
  command,
  setCommand,
  onSubmit,
  loading,
  onNavigateHistory,
}: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const cursorRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        containerRef.current,
        { opacity: 0, y: 24 },
        { opacity: 1, y: 0, duration: 0.7, ease: "power3.out" }
      );
      gsap.fromTo(
        ".chip",
        { opacity: 0, y: 10, scale: 0.9 },
        {
          opacity: 1,
          y: 0,
          scale: 1,
          stagger: 0.07,
          delay: 0.4,
          duration: 0.4,
          ease: "back.out(1.5)",
        }
      );
    });
    return () => ctx.revert();
  }, []);

  // Blinking cursor animation
  useEffect(() => {
    if (!cursorRef.current) return;
    const tl = gsap.to(cursorRef.current, {
      opacity: 0,
      duration: 0.5,
      repeat: -1,
      yoyo: true,
      ease: "steps(1)",
    });
    return () => tl.kill();
  }, []);

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading && command.trim()) onSubmit();
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      onNavigateHistory("up");
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      onNavigateHistory("down");
    }
  };

  const handleChip = (chip: string) => {
    setCommand(chip);
    inputRef.current?.focus();
    gsap.fromTo(
      containerRef.current,
      { borderColor: "var(--accent)" },
      { borderColor: "var(--border)", duration: 0.8, ease: "power2.out" }
    );
  };

  return (
    <div className="terminal-wrap" ref={containerRef}>
      {/* Title bar */}
      <div className="terminal-titlebar">
        <span className="tb-dot tb-red" />
        <span className="tb-dot tb-yellow" />
        <span className="tb-dot tb-green" />
        <span className="tb-title">docker-playground — bash</span>
      </div>

      {/* Input area */}
      <div className="terminal-body">
        <div className="prompt-line">
          <span className="prompt-user">user@docker</span>
          <span className="prompt-sep">:</span>
          <span className="prompt-path">~</span>
          <span className="prompt-dollar">$</span>
          <span className="prompt-cmd-prefix">docker</span>
        </div>
        <div className="input-row">
          <textarea
            ref={inputRef}
            className="terminal-input"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            onKeyDown={handleKey}
            placeholder="run -d -p 8080:80 nginx"
            rows={2}
            spellCheck={false}
            autoCapitalize="none"
            autoCorrect="off"
            disabled={loading}
          />
          <span className="terminal-cursor" ref={cursorRef}>▌</span>
        </div>
        <div className="terminal-hint">
          <kbd>Enter</kbd> to validate &nbsp;·&nbsp; <kbd>↑↓</kbd> history
        </div>
      </div>

      {/* Submit */}
      <div className="terminal-footer">
        <button
          className={`btn-validate ${loading ? "btn-loading" : ""}`}
          onClick={onSubmit}
          disabled={loading || !command.trim()}
        >
          {loading ? (
            <>
              <span className="spinner" /> Analysing…
            </>
          ) : (
            <>
              <span className="btn-icon">⚡</span> Validate Command
            </>
          )}
        </button>
      </div>

      {/* Quick-start chips */}
      <div className="chips-section">
        <span className="chips-label">Quick start:</span>
        <div className="chips-row">
          {CHIPS.map((chip) => (
            <button
              key={chip}
              className="chip"
              onClick={() => handleChip(chip)}
              title={chip}
            >
              {chip.length > 42 ? chip.slice(0, 42) + "…" : chip}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
