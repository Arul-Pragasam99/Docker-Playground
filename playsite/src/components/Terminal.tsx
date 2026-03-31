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

// Simple descriptions for subcommands
const COMMAND_DESCRIPTIONS: Record<string, { title: string; desc: string; icon: string }> = {
  run:     { icon: "▶", title: "docker run",     desc: "Create and start a new container from an image." },
  build:   { icon: "🔨", title: "docker build",   desc: "Build a Docker image from a Dockerfile." },
  pull:    { icon: "⬇", title: "docker pull",    desc: "Download an image from a registry (e.g. Docker Hub)." },
  push:    { icon: "⬆", title: "docker push",    desc: "Upload a local image to a registry." },
  exec:    { icon: "⚡", title: "docker exec",    desc: "Run a command inside an already running container." },
  stop:    { icon: "⏹", title: "docker stop",    desc: "Gracefully stop a running container (sends SIGTERM)." },
  start:   { icon: "▶", title: "docker start",   desc: "Start one or more stopped containers." },
  restart: { icon: "🔄", title: "docker restart", desc: "Stop and then start a container again." },
  rm:      { icon: "🗑", title: "docker rm",      desc: "Remove one or more stopped containers." },
  rmi:     { icon: "🗑", title: "docker rmi",     desc: "Remove one or more images from local storage." },
  ps:      { icon: "📋", title: "docker ps",      desc: "List containers. By default shows only running ones." },
  images:  { icon: "🖼", title: "docker images",  desc: "List all locally available Docker images." },
  logs:    { icon: "📜", title: "docker logs",    desc: "Fetch and display logs from a container." },
  inspect: { icon: "🔍", title: "docker inspect", desc: "Return detailed low-level info about any Docker object." },
  network: { icon: "🌐", title: "docker network", desc: "Manage Docker networks (create, list, remove, connect)." },
  volume:  { icon: "💾", title: "docker volume",  desc: "Manage Docker volumes for persistent data storage." },
  compose: { icon: "🧩", title: "docker compose", desc: "Define and run multi-container apps with a YAML file." },
  tag:     { icon: "🏷", title: "docker tag",     desc: "Create a new tag pointing to an existing image." },
  commit:  { icon: "💾", title: "docker commit",  desc: "Create a new image from a container's changes." },
  cp:      { icon: "📂", title: "docker cp",      desc: "Copy files between a container and the local filesystem." },
  info:    { icon: "ℹ", title: "docker info",    desc: "Display system-wide Docker information and config." },
  kill:    { icon: "⚡", title: "docker kill",    desc: "Send a signal (default SIGKILL) to a running container." },
  login:   { icon: "🔑", title: "docker login",   desc: "Log in to a Docker registry." },
  logout:  { icon: "🔓", title: "docker logout",  desc: "Log out from a Docker registry." },
  pause:   { icon: "⏸", title: "docker pause",   desc: "Pause all processes within a container." },
  unpause: { icon: "▶", title: "docker unpause", desc: "Resume a paused container." },
  port:    { icon: "🔌", title: "docker port",    desc: "List port mappings for a container." },
  rename:  { icon: "✏", title: "docker rename",  desc: "Rename an existing container." },
  stats:   { icon: "📊", title: "docker stats",   desc: "Show live CPU, memory, and network usage per container." },
  top:     { icon: "📈", title: "docker top",     desc: "Display running processes inside a container." },
  save:    { icon: "💾", title: "docker save",    desc: "Save one or more images to a tar archive." },
  load:    { icon: "📦", title: "docker load",    desc: "Load an image from a tar archive." },
  search:  { icon: "🔍", title: "docker search",  desc: "Search Docker Hub for available images." },
  system:  { icon: "⚙", title: "docker system",  desc: "Manage Docker disk usage, prune unused resources." },
  update:  { icon: "🔧", title: "docker update",  desc: "Update resource limits on a running container." },
  wait:    { icon: "⏳", title: "docker wait",    desc: "Block until a container stops, then print its exit code." },
  diff:    { icon: "📝", title: "docker diff",    desc: "Show filesystem changes made inside a container." },
  events:  { icon: "📡", title: "docker events",  desc: "Stream real-time events from the Docker daemon." },
  export:  { icon: "📤", title: "docker export",  desc: "Export a container's filesystem as a tar archive." },
  import:  { icon: "📥", title: "docker import",  desc: "Import a tarball to create a new filesystem image." },
  buildx:  { icon: "🔨", title: "docker buildx",  desc: "Extended build with BuildKit — multi-arch, cache mounts, secrets." },
  scout:   { icon: "🛡", title: "docker scout",   desc: "Analyse images for vulnerabilities and recommendations." },
  context: { icon: "🔀", title: "docker context", desc: "Switch between different Docker endpoints/environments." },
};

function getCommandInfo(raw: string) {
  const trimmed = raw.trim().toLowerCase();
  if (!trimmed) return null;

  // Strip leading 'docker' keyword
  const stripped = trimmed.startsWith("docker") ? trimmed.slice(6).trim() : trimmed;
  if (!stripped) return null;

  const subcommand = stripped.split(/\s+/)[0];
  return COMMAND_DESCRIPTIONS[subcommand] || {
    icon: "🐳",
    title: `docker ${subcommand}`,
    desc: `'${subcommand}' — type the full command and hit Validate for a detailed breakdown.`,
  };
}

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
  const descRef = useRef<HTMLDivElement>(null);

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
          opacity: 1, y: 0, scale: 1,
          stagger: 0.07, delay: 0.4, duration: 0.4,
          ease: "back.out(1.5)",
        }
      );
    });
    return () => ctx.revert();
  }, []);

  // Blinking cursor
  useEffect(() => {
    if (!cursorRef.current) return;
    const tl = gsap.to(cursorRef.current, {
      opacity: 0, duration: 0.5, repeat: -1, yoyo: true, ease: "steps(1)",
    });
    return () => tl.kill();
  }, []);

  // Animate description box when command changes
  useEffect(() => {
    if (!descRef.current) return;
    const info = getCommandInfo(command);
    if (!info) return;
    gsap.fromTo(
      descRef.current,
      { opacity: 0, y: 6 },
      { opacity: 1, y: 0, duration: 0.3, ease: "power2.out" }
    );
  }, [command.split(/\s+/)[0]]); // only re-animate when subcommand changes

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!loading && command.trim()) onSubmit();
    }
    if (e.key === "ArrowUp") { e.preventDefault(); onNavigateHistory("up"); }
    if (e.key === "ArrowDown") { e.preventDefault(); onNavigateHistory("down"); }
  };

  const handleChip = (chip: string) => {
    setCommand(chip);
    inputRef.current?.focus();
  };

  const cmdInfo = getCommandInfo(command);

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

      {/* Live command description */}
      {cmdInfo && (
        <div className="cmd-desc-bar" ref={descRef}>
          <span className="cmd-desc-icon">{cmdInfo.icon}</span>
          <div className="cmd-desc-text">
            <span className="cmd-desc-title">{cmdInfo.title}</span>
            <span className="cmd-desc-body">{cmdInfo.desc}</span>
          </div>
        </div>
      )}

      {/* Submit */}
      <div className="terminal-footer">
        <button
          className={`btn-validate ${loading ? "btn-loading" : ""}`}
          onClick={onSubmit}
          disabled={loading || !command.trim()}
        >
          {loading ? (
            <><span className="spinner" /> Analysing…</>
          ) : (
            <><span className="btn-icon">⚡</span> Validate Command</>
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