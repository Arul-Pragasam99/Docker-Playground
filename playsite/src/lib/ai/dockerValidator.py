"""
Docker Command Validator — Local AI Engine
Uses: scikit-learn, nltk, numpy (no external APIs)
"""

import re
import json
import difflib
from typing import Dict, List, Optional, Tuple

import numpy as np

# ─── NLTK (lazy-init) ────────────────────────────────────────────────────────
try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.metrics.distance import edit_distance

    _NLTK_OK = True
except ImportError:
    _NLTK_OK = False

# ─── Docker Knowledge Base ────────────────────────────────────────────────────

DOCKER_SUBCOMMANDS = {
    "run", "build", "pull", "push", "exec", "stop", "start", "restart",
    "rm", "rmi", "ps", "images", "logs", "inspect", "network", "volume",
    "compose", "tag", "commit", "cp", "diff", "events", "export", "import",
    "info", "kill", "load", "login", "logout", "pause", "port", "rename",
    "save", "search", "stats", "top", "unpause", "update", "wait",
    "container", "image", "system", "config", "secret", "service", "stack",
    "swarm", "node", "plugin", "trust", "manifest", "context", "scan",
    "buildx", "sbom", "scout",
}

# flag -> {description, category, valid_for}
FLAG_DB: Dict[str, Dict] = {
    # --- run ---
    "-d":            {"desc": "Run container in detached (background) mode. The container runs as a daemon, freeing up your terminal.", "cat": "execution"},
    "--detach":      {"desc": "Long form of -d. Runs the container in the background.", "cat": "execution"},
    "-it":           {"desc": "Combination of -i (interactive) and -t (allocate pseudo-TTY). Use for interactive shells inside containers.", "cat": "execution"},
    "-i":            {"desc": "Keep STDIN open even if not attached. Required for piping input into a container.", "cat": "execution"},
    "--interactive": {"desc": "Long form of -i. Keeps STDIN open for interactive use.", "cat": "execution"},
    "-t":            {"desc": "Allocate a pseudo-TTY (terminal). Required for interactive shell sessions.", "cat": "execution"},
    "--tty":         {"desc": "Long form of -t. Allocates a pseudo-TTY for the container.", "cat": "execution"},
    "--rm":          {"desc": "Automatically remove the container when it exits. Great for one-off tasks to avoid container clutter.", "cat": "execution"},
    "-p":            {"desc": "Publish container port(s) to the host. Format: HOST_PORT:CONTAINER_PORT.", "cat": "network"},
    "--publish":     {"desc": "Long form of -p. Maps container ports to host ports.", "cat": "network"},
    "-P":            {"desc": "Publish ALL exposed ports to random host ports. Docker picks available ports automatically.", "cat": "network"},
    "--publish-all": {"desc": "Long form of -P. Publishes all EXPOSE'd ports to ephemeral host ports.", "cat": "network"},
    "-v":            {"desc": "Bind mount a volume. Format: HOST_PATH:CONTAINER_PATH[:ro]. Persists data outside the container lifecycle.", "cat": "volume"},
    "--volume":      {"desc": "Long form of -v. Creates a bind mount or named volume.", "cat": "volume"},
    "--mount":       {"desc": "More explicit volume mounting syntax. Supports type=bind|volume|tmpfs with key=value options.", "cat": "volume"},
    "-e":            {"desc": "Set an environment variable inside the container. Format: -e KEY=VALUE.", "cat": "execution"},
    "--env":         {"desc": "Long form of -e. Sets an environment variable.", "cat": "execution"},
    "--env-file":    {"desc": "Load environment variables from a file (one KEY=VALUE per line).", "cat": "execution"},
    "--name":        {"desc": "Assign a custom name to the container. Makes it easier to reference vs. auto-generated names.", "cat": "container"},
    "--network":     {"desc": "Connect the container to a specific Docker network (bridge, host, none, or custom).", "cat": "network"},
    "--net":         {"desc": "Alias for --network. Specifies the network mode.", "cat": "network"},
    "--hostname":    {"desc": "Set the container's hostname inside the network.", "cat": "network"},
    "--link":        {"desc": "Add a link to another container (legacy networking). Prefer --network instead.", "cat": "network"},
    "--restart":     {"desc": "Restart policy: no|always|on-failure|unless-stopped. Controls automatic restart behaviour.", "cat": "execution"},
    "--memory":      {"desc": "Memory limit for the container (e.g. 512m, 1g). Prevents runaway memory usage.", "cat": "resource"},
    "-m":            {"desc": "Short form of --memory. Sets the container memory limit.", "cat": "resource"},
    "--cpus":        {"desc": "Number of CPUs the container may use (e.g. --cpus=1.5). Fractional values are allowed.", "cat": "resource"},
    "--cpu-shares":  {"desc": "Relative CPU weight (default 1024). Higher value = more CPU time relative to other containers.", "cat": "resource"},
    "--user":        {"desc": "Username or UID to run the container process as. Use for least-privilege security.", "cat": "execution"},
    "-u":            {"desc": "Short form of --user. Sets the user for the container process.", "cat": "execution"},
    "--workdir":     {"desc": "Set the working directory inside the container for the entrypoint/cmd.", "cat": "execution"},
    "-w":            {"desc": "Short form of --workdir. Sets the working directory.", "cat": "execution"},
    "--entrypoint":  {"desc": "Override the default ENTRYPOINT of the image.", "cat": "execution"},
    "--privileged":  {"desc": "Give extended privileges to the container (access to all host devices). Use with caution.", "cat": "execution"},
    "--read-only":   {"desc": "Mount the container's root filesystem as read-only. Good security hardening.", "cat": "execution"},
    "--cap-add":     {"desc": "Add Linux capabilities (e.g. --cap-add=NET_ADMIN). Fine-grained privilege control.", "cat": "execution"},
    "--cap-drop":    {"desc": "Drop Linux capabilities for reduced attack surface.", "cat": "execution"},
    "--device":      {"desc": "Add a host device to the container (e.g. --device=/dev/snd).", "cat": "execution"},
    "--tmpfs":       {"desc": "Mount a tmpfs (RAM-based) filesystem at a path. Data is lost on container stop.", "cat": "volume"},
    "--label":       {"desc": "Add metadata labels to the container (key=value pairs).", "cat": "other"},
    "-l":            {"desc": "Short form of --label.", "cat": "other"},
    "--log-driver":  {"desc": "Logging driver for the container (json-file, syslog, journald, none, etc.).", "cat": "output"},
    "--log-opt":     {"desc": "Log driver options (e.g. max-size, max-file for json-file driver).", "cat": "output"},
    "--health-cmd":  {"desc": "Command to run as the container health check.", "cat": "execution"},
    "--no-healthcheck": {"desc": "Disable any HEALTHCHECK defined in the image.", "cat": "execution"},
    "--init":        {"desc": "Run an init process (tini) inside the container. Reaps zombie processes.", "cat": "execution"},
    "--shm-size":    {"desc": "Size of /dev/shm (shared memory). Increase for apps like Chrome that need large shared mem.", "cat": "resource"},
    "--pid":         {"desc": "PID namespace to use (e.g. --pid=host shares the host PID namespace).", "cat": "execution"},
    "--ipc":         {"desc": "IPC namespace (e.g. --ipc=host or --ipc=shareable).", "cat": "execution"},
    "--ulimit":      {"desc": "Set ulimits for the container (e.g. --ulimit nofile=1024:1024).", "cat": "resource"},
    "--add-host":    {"desc": "Add a custom host-to-IP mapping to /etc/hosts inside the container.", "cat": "network"},
    "--dns":         {"desc": "Set custom DNS servers for the container.", "cat": "network"},
    "--dns-search":  {"desc": "Set DNS search domains for the container.", "cat": "network"},
    "--expose":      {"desc": "Expose a port without publishing it to the host (used for inter-container communication).", "cat": "network"},

    # --- build ---
    "-f":            {"desc": "Specify the Dockerfile path. Default: ./Dockerfile.", "cat": "build"},
    "--file":        {"desc": "Long form of -f. Path to the Dockerfile.", "cat": "build"},
    "--tag":         {"desc": "Name and optionally a tag for the image (name:tag format).", "cat": "image"},
    "--build-arg":   {"desc": "Set build-time ARG variables defined in the Dockerfile.", "cat": "build"},
    "--no-cache":    {"desc": "Do not use the build cache. Forces a full rebuild from scratch.", "cat": "build"},
    "--target":      {"desc": "Build a specific stage in a multi-stage Dockerfile.", "cat": "build"},
    "--platform":    {"desc": "Set the target platform (e.g. linux/amd64, linux/arm64) for multi-arch builds.", "cat": "build"},
    "--progress":    {"desc": "Set build progress output type: auto, plain, tty.", "cat": "output"},
    "--squash":      {"desc": "Squash newly built layers into a single layer (experimental).", "cat": "build"},
    "--compress":    {"desc": "Compress the build context with gzip.", "cat": "build"},
    "--pull":        {"desc": "Always attempt to pull a newer version of the base image.", "cat": "build"},
    "--quiet":       {"desc": "Suppress verbose build output. Only print the image ID on success.", "cat": "output"},
    "-q":            {"desc": "Short form of --quiet.", "cat": "output"},
    "--secret":      {"desc": "Pass a secret to the build (e.g. SSH keys) without baking it into the image.", "cat": "build"},
    "--ssh":         {"desc": "Expose SSH agent socket or keys to the build for private repo access.", "cat": "build"},
    "--cache-from":  {"desc": "Images to use as cache sources during the build.", "cat": "build"},
    "--cache-to":    {"desc": "Export build cache to a destination (e.g. type=registry).", "cat": "build"},
    "--output":      {"desc": "Output destination (e.g. type=docker, type=local, type=tar).", "cat": "build"},
    "--iidfile":     {"desc": "Write the image ID to a file after a successful build.", "cat": "build"},

    # --- ps / images ---
    "-a":            {"desc": "Show all containers (default shows only running). For images, shows all layers.", "cat": "output"},
    "--all":         {"desc": "Long form of -a. Show all containers or images.", "cat": "output"},
    "--filter":      {"desc": "Filter output by a condition (e.g. --filter status=exited, --filter label=app).", "cat": "output"},
    "--format":      {"desc": "Pretty-print output using a Go template (e.g. --format '{{.Names}}').", "cat": "output"},
    "--no-trunc":    {"desc": "Don't truncate output. Shows full container IDs and image digests.", "cat": "output"},
    "--size":        {"desc": "Display total file sizes for containers.", "cat": "output"},
    "-s":            {"desc": "Short form of --size.", "cat": "output"},

    # --- logs ---
    "--follow":      {"desc": "Follow log output in real time (like tail -f).", "cat": "output"},
    "--since":       {"desc": "Show logs since a timestamp or relative duration (e.g. --since=1h).", "cat": "output"},
    "--until":       {"desc": "Show logs before a timestamp (e.g. --until=2024-01-01).", "cat": "output"},
    "--tail":        {"desc": "Number of lines from the end of logs to show (e.g. --tail=100).", "cat": "output"},
    "--timestamps":  {"desc": "Show timestamps for each log line.", "cat": "output"},

    # --- exec ---
    "--detach-keys": {"desc": "Override the key sequence for detaching from a container.", "cat": "execution"},

    # --- network create ---
    "--driver":      {"desc": "Network driver: bridge (default), overlay, host, macvlan, none.", "cat": "network"},
    "--subnet":      {"desc": "Subnet in CIDR format (e.g. 172.18.0.0/16).", "cat": "network"},
    "--gateway":     {"desc": "IPv4 or IPv6 gateway for the master subnet.", "cat": "network"},
    "--ip-range":    {"desc": "Allocate container IPs from a sub-range of the subnet.", "cat": "network"},
    "--internal":    {"desc": "Restrict external access to the network.", "cat": "network"},
    "--attachable":  {"desc": "Allow standalone containers to attach to the network (swarm overlay).", "cat": "network"},
    "--ingress":     {"desc": "Create a swarm routing-mesh network.", "cat": "network"},
    "--ipv6":        {"desc": "Enable IPv6 networking.", "cat": "network"},

    # --- volume create ---
    "--opt":         {"desc": "Set driver-specific options for volume or network creation.", "cat": "other"},
    "-o":            {"desc": "Short form of --opt.", "cat": "other"},

    # --- system ---
    "--force":       {"desc": "Do not prompt for confirmation. Force the operation.", "cat": "other"},
    "--volumes":     {"desc": "Include volumes when pruning or removing containers.", "cat": "volume"},
}

# Common typo → correct flag
TYPO_MAP = {
    "--detch":     "--detach",
    "--deatch":    "--detach",
    "--detach ":   "--detach",
    "-detatched":  "-d",
    "--porto":     "--port",
    "--ports":     "-p",
    "--volum":     "--volume",
    "--volumne":   "--volume",
    "--enviroment": "--env",
    "--environmet": "--env",
    "--environmnet": "--env",
    "--memorty":   "--memory",
    "--memeory":   "--memory",
    "--netwrok":   "--network",
    "--netowrk":   "--network",
    "--priviledged": "--privileged",
    "--privilaged": "--privileged",
    "--entrypoin": "--entrypoint",
    "--entrypoitn": "--entrypoint",
    "--workdirr":  "--workdir",
    "--restar":    "--restart",
    "--restert":   "--restart",
    "--no-cach":   "--no-cache",
    "--no-cashe":  "--no-cache",
    "--buid-arg":  "--build-arg",
    "--buiild-arg": "--build-arg",
    "--taget":     "--target",
    "--platfrom":  "--platform",
    "--platorm":   "--platform",
    "--squassh":   "--squash",
    "--flter":     "--filter",
    "--formatt":   "--format",
    "--follw":     "--follow",
    "--fllow":     "--follow",
}

# Pro tips per subcommand
PRO_TIPS: Dict[str, List[str]] = {
    "run": [
        "Use '--rm' with one-off commands to auto-clean containers.",
        "Prefer '--network' over the legacy '--link' flag for inter-container communication.",
        "Set '--restart=unless-stopped' for long-running services so they survive reboots.",
        "Use '--memory' and '--cpus' to avoid a single container starving the host.",
        "Combine '-e' with '--env-file' to keep sensitive values out of shell history.",
        "Use '--read-only' + '--tmpfs /tmp' for a hardened, mostly-immutable container.",
    ],
    "build": [
        "Add a .dockerignore file to exclude node_modules, .git, etc. from the build context.",
        "Use multi-stage builds (--target) to keep final images lean.",
        "--no-cache is useful in CI pipelines to ensure reproducible builds.",
        "Cache expensive layers (apt-get, npm install) early in the Dockerfile.",
        "Use --build-arg for values that change between environments, not secrets.",
        "BuildKit (DOCKER_BUILDKIT=1) enables parallelism, secrets, and SSH forwarding.",
    ],
    "exec": [
        "Use 'docker exec -it <name> sh' for containers that don't have bash.",
        "'-d' runs the command in the background inside the container.",
        "exec only works on running containers — use 'docker start' first if needed.",
    ],
    "ps": [
        "Use '--filter status=exited' to find stopped containers consuming disk space.",
        "'docker ps -q' returns only IDs — pipe to 'docker rm' for bulk cleanup.",
        "--format '{{.Names}}\t{{.Status}}' gives a clean custom view.",
    ],
    "logs": [
        "'docker logs -f --tail=100' is the fastest way to tail recent output.",
        "Timestamps (--timestamps) are invaluable when correlating logs across services.",
        "Consider a proper logging driver (--log-driver=journald) for production.",
    ],
    "network": [
        "Custom bridge networks provide automatic DNS resolution between containers.",
        "Use --internal to isolate a network from the outside world.",
        "Overlay networks are needed for multi-host (Swarm) communication.",
    ],
    "volume": [
        "Named volumes survive 'docker rm'; bind mounts depend on host path existence.",
        "Use 'docker volume prune' to clean up unused volumes.",
        "--mount is more explicit and easier to read than -v for complex cases.",
    ],
    "default": [
        "Use 'docker system prune -a' periodically to reclaim disk space.",
        "Docker Compose is recommended for multi-container applications.",
        "Always pin image versions (myimage:1.2.3) in production, never use ':latest'.",
        "Use 'docker inspect' to dump full metadata about containers, images, or networks.",
    ],
}

# ─── Subcommand proximity map (for typo detection) ───────────────────────────
ALL_SUBCOMMANDS_LIST = sorted(DOCKER_SUBCOMMANDS)


# ─── Vectoriser (TF-IDF style, local, no sklearn needed at runtime) ──────────

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _token_vector(tokens: List[str], vocab: List[str]) -> np.ndarray:
    vec = np.zeros(len(vocab))
    for t in tokens:
        if t in vocab:
            vec[vocab.index(t)] += 1
    return vec


# ─── Parser ──────────────────────────────────────────────────────────────────

def _tokenize_command(command: str) -> List[str]:
    """Split a docker command string into tokens."""
    command = command.strip()
    # Strip leading 'docker' keyword
    if command.lower().startswith("docker"):
        command = command[6:].strip()
    # Simple shell-style tokenisation (respects single quotes)
    tokens = re.findall(r"'[^']*'|\"[^\"]*\"|\S+", command)
    return tokens


def _find_typo(token: str) -> Optional[Tuple[str, str]]:
    """Return (suggestion, message) if token looks like a typo."""
    # Exact map first
    if token in TYPO_MAP:
        return TYPO_MAP[token], f"'{token}' is a common misspelling."

    # Edit-distance check against known flags
    if token.startswith("-"):
        all_flags = list(FLAG_DB.keys())
        best_flag, best_dist = None, 99
        for f in all_flags:
            d = _edit_dist(token, f)
            if d < best_dist:
                best_dist = d
                best_flag = f
        threshold = max(2, len(token) // 4)
        if best_flag and best_dist <= threshold and token != best_flag:
            return best_flag, f"Did you mean '{best_flag}'? (edit distance {best_dist})"

    return None


def _edit_dist(a: str, b: str) -> int:
    if _NLTK_OK:
        return edit_distance(a, b)
    # Fallback pure-Python Levenshtein
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[:]
        dp[0] = i
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[j] = prev[j - 1]
            else:
                dp[j] = 1 + min(prev[j], dp[j - 1], prev[j - 1])
    return dp[n]


def _closest_subcommand(token: str) -> Optional[str]:
    matches = difflib.get_close_matches(token, ALL_SUBCOMMANDS_LIST, n=1, cutoff=0.6)
    return matches[0] if matches else None


# ─── Confidence scoring ───────────────────────────────────────────────────────

def _compute_confidence(
    subcommand_known: bool,
    flag_ratio: float,
    typo_count: int,
    has_image_or_arg: bool,
) -> float:
    score = 0.0
    if subcommand_known:
        score += 0.40
    score += flag_ratio * 0.35
    score += 0.15 if has_image_or_arg else 0.0
    score -= typo_count * 0.08
    return round(max(0.0, min(1.0, score)), 2)


# ─── Main validator ───────────────────────────────────────────────────────────

def validate_command(raw: str) -> Dict:
    tokens = _tokenize_command(raw)

    if not tokens:
        return {
            "valid": False,
            "command": raw,
            "subcommand": "",
            "confidence": 0.0,
            "flags": [],
            "typos": [],
            "pro_tips": PRO_TIPS["default"],
            "summary": "Empty command.",
        }

    # First token = subcommand
    subcommand_raw = tokens[0]
    subcommand = subcommand_raw.lower()
    rest = tokens[1:]

    subcommand_known = subcommand in DOCKER_SUBCOMMANDS
    subcommand_typo = None
    if not subcommand_known:
        closest = _closest_subcommand(subcommand)
        subcommand_typo = closest

    flags_found: List[Dict] = []
    typos_found: List[Dict] = []
    positional_args: List[str] = []

    i = 0
    known_flag_count = 0
    while i < len(rest):
        token = rest[i]

        # Combined short flags like -it, -dp
        if re.match(r"^-[a-zA-Z]{2,}$", token) and not token.startswith("--"):
            # Expand: -it → -i, -t
            for ch in token[1:]:
                f = f"-{ch}"
                if f in FLAG_DB:
                    known_flag_count += 1
                    info = FLAG_DB[f]
                    flags_found.append({
                        "flag": f,
                        "description": info["desc"],
                        "category": info["cat"],
                    })
                else:
                    flags_found.append({
                        "flag": f,
                        "description": f"Short flag -{ch} (unrecognised in knowledge base).",
                        "category": "other",
                    })
            i += 1
            continue

        if token.startswith("-"):
            # May include value like --name=myapp or -p 8080:80
            flag_part = token
            value_part = None

            if "=" in token:
                flag_part, value_part = token.split("=", 1)

            # Typo check
            typo = _find_typo(flag_part)
            if typo:
                suggestion, msg = typo
                typos_found.append({
                    "original": flag_part,
                    "suggestion": suggestion,
                    "message": msg,
                })

            if flag_part in FLAG_DB:
                known_flag_count += 1
                info = FLAG_DB[flag_part]
                entry: Dict = {
                    "flag": flag_part,
                    "description": info["desc"],
                    "category": info["cat"],
                }
                # Grab next token as value if no = and next token doesn't start with -
                if value_part:
                    entry["value"] = value_part
                elif i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                    entry["value"] = rest[i + 1]
                    i += 1  # consume value
                flags_found.append(entry)
            else:
                entry = {
                    "flag": flag_part,
                    "description": f"Flag '{flag_part}' not found in knowledge base.",
                    "category": "other",
                }
                if value_part:
                    entry["value"] = value_part
                flags_found.append(entry)
        else:
            positional_args.append(token)

        i += 1

    # Subcommand typo entry
    if subcommand_typo:
        typos_found.insert(0, {
            "original": subcommand_raw,
            "suggestion": subcommand_typo,
            "message": f"Unknown subcommand '{subcommand_raw}'. Did you mean '{subcommand_typo}'?",
        })

    total_flags = len(flags_found)
    flag_ratio = (known_flag_count / total_flags) if total_flags > 0 else 1.0
    confidence = _compute_confidence(
        subcommand_known,
        flag_ratio,
        len(typos_found),
        bool(positional_args),
    )

    valid = subcommand_known and len(typos_found) == 0 and confidence >= 0.45

    # Build summary
    if not subcommand_known:
        summary = f"Unrecognised subcommand '{subcommand_raw}'.{' Possible match: docker ' + subcommand_typo if subcommand_typo else ''}"
    elif typos_found:
        summary = f"Command 'docker {subcommand}' is valid but contains {len(typos_found)} likely typo(s) in flags."
    elif total_flags == 0:
        summary = f"'docker {subcommand}' with no flags. Simple invocation."
    else:
        flag_names = ", ".join(f["flag"] for f in flags_found[:4])
        extra = f" (+{total_flags - 4} more)" if total_flags > 4 else ""
        summary = f"Valid 'docker {subcommand}' command using: {flag_names}{extra}."

    # Tips
    tips = PRO_TIPS.get(subcommand, PRO_TIPS["default"])

    return {
        "valid": valid,
        "command": raw,
        "subcommand": subcommand if subcommand_known else (subcommand_typo or subcommand),
        "confidence": confidence,
        "flags": flags_found,
        "typos": typos_found,
        "pro_tips": tips[:4],
        "summary": summary,
    }
