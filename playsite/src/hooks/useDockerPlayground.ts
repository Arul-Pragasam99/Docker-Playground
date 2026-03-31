"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { v4 as uuidv4 } from "uuid";

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

interface HistoryItem {
  id: string;
  command: string;
  valid: boolean;
  timestamp: string;
}

export function useDockerPlayground() {
  const [command, setCommand] = useState("");
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [sessionId] = useState<string>(() => {
    if (typeof window === "undefined") return uuidv4();
    const stored = sessionStorage.getItem("docker_session_id");
    if (stored) return stored;
    const id = uuidv4();
    sessionStorage.setItem("docker_session_id", id);
    return id;
  });

  const commandBeforeNav = useRef("");

  // Load history on mount
  useEffect(() => {
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`/api/history?sessionId=${sessionId}`);
      if (!res.ok) return;
      const data = await res.json();
      setHistory(data.history || []);
    } catch {
      // silently fail
    }
  }, [sessionId]);

  const validate = useCallback(async () => {
    if (!command.trim() || loading) return;
    setLoading(true);
    setResult(null);
    setHistoryIndex(-1);

    try {
      const res = await fetch("/api/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: command.trim(), sessionId }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Validation failed");
      setResult(data);
      await fetchHistory();
    } catch (err: any) {
      setResult({
        valid: false,
        command: command.trim(),
        subcommand: "",
        confidence: 0,
        flags: [],
        typos: [],
        pro_tips: [],
        summary: "",
        error: err.message,
      });
    } finally {
      setLoading(false);
    }
  }, [command, loading, sessionId, fetchHistory]);

  const clearHistory = useCallback(async () => {
    try {
      await fetch(`/api/history?sessionId=${sessionId}`, { method: "DELETE" });
      setHistory([]);
    } catch {
      // silently fail
    }
  }, [sessionId]);

  const navigateHistory = useCallback(
    (dir: "up" | "down") => {
      if (history.length === 0) return;
      if (historyIndex === -1) commandBeforeNav.current = command;

      let newIndex = historyIndex;
      if (dir === "up") {
        newIndex = Math.min(historyIndex + 1, history.length - 1);
      } else {
        newIndex = Math.max(historyIndex - 1, -1);
      }

      setHistoryIndex(newIndex);
      if (newIndex === -1) {
        setCommand(commandBeforeNav.current);
      } else {
        setCommand(history[newIndex].command);
      }
    },
    [history, historyIndex, command]
  );

  return {
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
  };
}
