"""
Docker Command Validator — Local AI Engine
Uses: scikit-learn, nltk, numpy (no external APIs)
"""

import re
import json
import difflib
from typing import Dict, List, Optional, Tuple

import numpy as np

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
    "buildx", "sbom", "scout", "attach", "history", "create", "version",
    "prune", "help",
}

FLAG_DB: Dict[str, Dict] = {
    # ── run ──────────────────────────────────────────────────────────────────
    "-d":               {"desc": "Run container in detached (background) mode.", "cat": "execution"},
    "--detach":         {"desc": "Long form of -d. Runs the container in the background.", "cat": "execution"},
    "-it":              {"desc": "Interactive + TTY. Use for shell sessions inside containers.", "cat": "execution"},
    "-i":               {"desc": "Keep STDIN open even if not attached.", "cat": "execution"},
    "--interactive":    {"desc": "Long form of -i.", "cat": "execution"},
    "-t":               {"desc": "Allocate a pseudo-TTY.", "cat": "execution"},
    "--tty":            {"desc": "Long form of -t.", "cat": "execution"},
    "--rm":             {"desc": "Auto-remove container when it exits.", "cat": "execution"},
    "-p":               {"desc": "Publish port(s): HOST_PORT:CONTAINER_PORT.", "cat": "network"},
    "--publish":        {"desc": "Long form of -p.", "cat": "network"},
    "-P":               {"desc": "Publish ALL exposed ports to random host ports.", "cat": "network"},
    "--publish-all":    {"desc": "Long form of -P.", "cat": "network"},
    "-v":               {"desc": "Bind mount: HOST_PATH:CONTAINER_PATH[:ro].", "cat": "volume"},
    "--volume":         {"desc": "Long form of -v.", "cat": "volume"},
    "--mount":          {"desc": "Explicit mount: type=bind|volume|tmpfs.", "cat": "volume"},
    "-e":               {"desc": "Set environment variable: KEY=VALUE.", "cat": "execution"},
    "--env":            {"desc": "Long form of -e.", "cat": "execution"},
    "--env-file":       {"desc": "Load env vars from a file.", "cat": "execution"},
    "--name":           {"desc": "Assign a custom name to the container.", "cat": "container"},
    "--network":        {"desc": "Connect to a Docker network.", "cat": "network"},
    "--net":            {"desc": "Alias for --network.", "cat": "network"},
    "--hostname":       {"desc": "Set the container hostname.", "cat": "network"},
    "--link":           {"desc": "Link to another container (legacy). Use --network instead.", "cat": "network"},
    "--restart":        {"desc": "Restart policy: no|always|on-failure|unless-stopped.", "cat": "execution"},
    "--memory":         {"desc": "Memory limit (e.g. 512m, 1g).", "cat": "resource"},
    "-m":               {"desc": "Short form of --memory.", "cat": "resource"},
    "--cpus":           {"desc": "Number of CPUs allowed (e.g. 1.5).", "cat": "resource"},
    "--cpu-shares":     {"desc": "Relative CPU weight (default 1024).", "cat": "resource"},
    "--cpu-period":     {"desc": "CPU CFS period in microseconds.", "cat": "resource"},
    "--cpu-quota":      {"desc": "CPU CFS quota in microseconds.", "cat": "resource"},
    "--cpuset-cpus":    {"desc": "CPUs to use (e.g. 0-3 or 0,1).", "cat": "resource"},
    "--memory-swap":    {"desc": "Swap limit (memory + swap). -1 = unlimited.", "cat": "resource"},
    "--memory-reservation": {"desc": "Soft memory limit.", "cat": "resource"},
    "--oom-kill-disable":   {"desc": "Disable OOM killer for this container.", "cat": "resource"},
    "--pids-limit":     {"desc": "Tune container PID limit (-1 = unlimited).", "cat": "resource"},
    "--blkio-weight":   {"desc": "Block IO weight (10–1000).", "cat": "resource"},
    "--user":           {"desc": "Username or UID to run as.", "cat": "execution"},
    "-u":               {"desc": "Short form of --user.", "cat": "execution"},
    "--workdir":        {"desc": "Working directory inside the container.", "cat": "execution"},
    "-w":               {"desc": "Short form of --workdir.", "cat": "execution"},
    "--entrypoint":     {"desc": "Override the image ENTRYPOINT.", "cat": "execution"},
    "--privileged":     {"desc": "Give extended privileges (all host devices). Use with caution.", "cat": "execution"},
    "--read-only":      {"desc": "Mount root filesystem as read-only.", "cat": "execution"},
    "--cap-add":        {"desc": "Add Linux capabilities (e.g. NET_ADMIN).", "cat": "execution"},
    "--cap-drop":       {"desc": "Drop Linux capabilities.", "cat": "execution"},
    "--device":         {"desc": "Add host device (e.g. /dev/snd).", "cat": "execution"},
    "--device-read-bps":  {"desc": "Limit read rate from a device (bytes/sec).", "cat": "resource"},
    "--device-write-bps": {"desc": "Limit write rate to a device (bytes/sec).", "cat": "resource"},
    "--tmpfs":          {"desc": "Mount a RAM-based tmpfs filesystem.", "cat": "volume"},
    "--label":          {"desc": "Add metadata label (key=value).", "cat": "other"},
    "-l":               {"desc": "Short form of --label.", "cat": "other"},
    "--label-file":     {"desc": "Read labels from a file.", "cat": "other"},
    "--log-driver":     {"desc": "Logging driver: json-file|syslog|journald|none etc.", "cat": "output"},
    "--log-opt":        {"desc": "Log driver options (e.g. max-size, max-file).", "cat": "output"},
    "--health-cmd":     {"desc": "Command to use as health check.", "cat": "execution"},
    "--health-interval":{"desc": "Time between health checks (default 30s).", "cat": "execution"},
    "--health-retries": {"desc": "Consecutive failures needed to report unhealthy.", "cat": "execution"},
    "--health-timeout": {"desc": "Max time for a health check to run.", "cat": "execution"},
    "--health-start-period": {"desc": "Grace period before health checks start.", "cat": "execution"},
    "--no-healthcheck": {"desc": "Disable any HEALTHCHECK from the image.", "cat": "execution"},
    "--init":           {"desc": "Run tini as PID 1 to reap zombie processes.", "cat": "execution"},
    "--shm-size":       {"desc": "Size of /dev/shm (e.g. 256m).", "cat": "resource"},
    "--pid":            {"desc": "PID namespace (e.g. --pid=host).", "cat": "execution"},
    "--ipc":            {"desc": "IPC namespace (e.g. --ipc=host).", "cat": "execution"},
    "--ulimit":         {"desc": "Set ulimits (e.g. nofile=1024:1024).", "cat": "resource"},
    "--add-host":       {"desc": "Add entry to /etc/hosts (host:ip).", "cat": "network"},
    "--dns":            {"desc": "Set custom DNS servers.", "cat": "network"},
    "--dns-search":     {"desc": "Set DNS search domains.", "cat": "network"},
    "--dns-opt":        {"desc": "Set DNS options.", "cat": "network"},
    "--expose":         {"desc": "Expose a port without publishing to host.", "cat": "network"},
    "--mac-address":    {"desc": "Set container MAC address.", "cat": "network"},
    "--ip":             {"desc": "Set container IPv4 address.", "cat": "network"},
    "--ip6":            {"desc": "Set container IPv6 address.", "cat": "network"},
    "--network-alias":  {"desc": "Add network-scoped alias for the container.", "cat": "network"},
    "--volumes-from":   {"desc": "Mount volumes from another container.", "cat": "volume"},
    "--stop-signal":    {"desc": "Signal to stop container (default SIGTERM).", "cat": "execution"},
    "--stop-timeout":   {"desc": "Timeout (seconds) to stop a container.", "cat": "execution"},
    "--runtime":        {"desc": "Runtime to use (e.g. nvidia, runc).", "cat": "execution"},
    "--security-opt":   {"desc": "Security options (e.g. no-new-privileges).", "cat": "execution"},
    "--userns":         {"desc": "User namespace (e.g. --userns=host).", "cat": "execution"},
    "--isolation":      {"desc": "Container isolation technology (Windows).", "cat": "execution"},
    "--platform":       {"desc": "Set target platform (e.g. linux/amd64).", "cat": "build"},
    "--pull":           {"desc": "Pull image before running: always|missing|never.", "cat": "image"},
    "--sig-proxy":      {"desc": "Proxy signals to the process (default true).", "cat": "execution"},
    "--attach":         {"desc": "Attach to STDIN, STDOUT or STDERR.", "cat": "execution"},
    "-a":               {"desc": "Short form of --attach / --all.", "cat": "output"},
    "--detach-keys":    {"desc": "Override key sequence for detaching.", "cat": "execution"},
    "--cidfile":        {"desc": "Write container ID to a file.", "cat": "other"},
    "--group-add":      {"desc": "Add additional groups to run as.", "cat": "execution"},
    "--kernel-memory":  {"desc": "Kernel memory limit.", "cat": "resource"},

    # ── build ─────────────────────────────────────────────────────────────────
    "-f":               {"desc": "Dockerfile path (default: ./Dockerfile).", "cat": "build"},
    "--file":           {"desc": "Long form of -f.", "cat": "build"},
    "--tag":            {"desc": "Image name and tag: name:tag.", "cat": "image"},
    "--build-arg":      {"desc": "Set ARG variables defined in Dockerfile.", "cat": "build"},
    "--no-cache":       {"desc": "Build without using cache.", "cat": "build"},
    "--target":         {"desc": "Build a specific multi-stage target.", "cat": "build"},
    "--progress":       {"desc": "Build progress output: auto|plain|tty.", "cat": "output"},
    "--squash":         {"desc": "Squash layers into one (experimental).", "cat": "build"},
    "--compress":       {"desc": "Compress build context with gzip.", "cat": "build"},
    "--quiet":          {"desc": "Suppress output, print image ID only.", "cat": "output"},
    "-q":               {"desc": "Short form of --quiet.", "cat": "output"},
    "--secret":         {"desc": "Pass a secret to the build.", "cat": "build"},
    "--ssh":            {"desc": "Expose SSH agent for private repo access.", "cat": "build"},
    "--cache-from":     {"desc": "Images to use as cache sources.", "cat": "build"},
    "--cache-to":       {"desc": "Export build cache to a destination.", "cat": "build"},
    "--output":         {"desc": "Output destination: type=docker|local|tar.", "cat": "build"},
    "--iidfile":        {"desc": "Write image ID to a file.", "cat": "build"},
    "--network":        {"desc": "Set network mode during build.", "cat": "network"},
    "--add-host":       {"desc": "Add /etc/hosts entry during build.", "cat": "network"},
    "--shm-size":       {"desc": "Size of /dev/shm during build.", "cat": "resource"},
    "--ulimit":         {"desc": "Set ulimits during build.", "cat": "resource"},
    "--rm":             {"desc": "Remove intermediate containers after build (default true).", "cat": "build"},
    "--force-rm":       {"desc": "Always remove intermediate containers.", "cat": "build"},
    "--memory":         {"desc": "Memory limit during build.", "cat": "resource"},
    "--memory-swap":    {"desc": "Swap limit during build.", "cat": "resource"},
    "--cpus":           {"desc": "CPUs allowed during build.", "cat": "resource"},
    "--cpu-shares":     {"desc": "CPU shares during build.", "cat": "resource"},
    "--cpu-period":     {"desc": "CPU period during build.", "cat": "resource"},
    "--cpu-quota":      {"desc": "CPU quota during build.", "cat": "resource"},
    "--cpuset-cpus":    {"desc": "CPUs to use during build.", "cat": "resource"},
    "--cpuset-mems":    {"desc": "Memory nodes to use during build.", "cat": "resource"},

    # ── ps / images ───────────────────────────────────────────────────────────
    "--all":            {"desc": "Show all containers or images.", "cat": "output"},
    "--filter":         {"desc": "Filter output (e.g. status=exited, label=app).", "cat": "output"},
    "--format":         {"desc": "Pretty-print using Go template.", "cat": "output"},
    "--no-trunc":       {"desc": "Don't truncate output.", "cat": "output"},
    "--size":           {"desc": "Display total file sizes.", "cat": "output"},
    "-s":               {"desc": "Short form of --size.", "cat": "output"},
    "--last":           {"desc": "Show last N created containers.", "cat": "output"},
    "-n":               {"desc": "Short form of --last.", "cat": "output"},
    "--latest":         {"desc": "Show the latest created container.", "cat": "output"},
    "--digests":        {"desc": "Show image digests.", "cat": "output"},

    # ── logs ──────────────────────────────────────────────────────────────────
    "--follow":         {"desc": "Follow log output in real time.", "cat": "output"},
    "-f":               {"desc": "Short form of --follow.", "cat": "output"},
    "--since":          {"desc": "Show logs since timestamp or duration (e.g. 1h).", "cat": "output"},
    "--until":          {"desc": "Show logs before timestamp.", "cat": "output"},
    "--tail":           {"desc": "Number of lines from end of logs.", "cat": "output"},
    "--timestamps":     {"desc": "Show timestamps for each log line.", "cat": "output"},
    "-t":               {"desc": "Short form of --timestamps.", "cat": "output"},

    # ── exec ──────────────────────────────────────────────────────────────────
    "--privileged":     {"desc": "Give extended privileges to the command.", "cat": "execution"},
    "--user":           {"desc": "Run as this user.", "cat": "execution"},
    "--workdir":        {"desc": "Working directory inside the container.", "cat": "execution"},
    "--env":            {"desc": "Set environment variables.", "cat": "execution"},
    "--env-file":       {"desc": "Read environment variables from a file.", "cat": "execution"},

    # ── network ───────────────────────────────────────────────────────────────
    "--driver":         {"desc": "Network driver: bridge|overlay|host|macvlan|none.", "cat": "network"},
    "--subnet":         {"desc": "Subnet in CIDR format (e.g. 172.18.0.0/16).", "cat": "network"},
    "--gateway":        {"desc": "IPv4 or IPv6 gateway for the subnet.", "cat": "network"},
    "--ip-range":       {"desc": "Allocate IPs from a sub-range.", "cat": "network"},
    "--internal":       {"desc": "Restrict external access to the network.", "cat": "network"},
    "--attachable":     {"desc": "Allow standalone containers to attach.", "cat": "network"},
    "--ingress":        {"desc": "Create swarm routing-mesh network.", "cat": "network"},
    "--ipv6":           {"desc": "Enable IPv6 networking.", "cat": "network"},
    "--aux-address":    {"desc": "Auxiliary IPv4 or IPv6 addresses.", "cat": "network"},
    "--config-from":    {"desc": "Source network for configuration.", "cat": "network"},
    "--config-only":    {"desc": "Create a configuration only network.", "cat": "network"},
    "--scope":          {"desc": "Network scope: local|swarm.", "cat": "network"},

    # ── volume ────────────────────────────────────────────────────────────────
    "--opt":            {"desc": "Driver-specific options.", "cat": "other"},
    "-o":               {"desc": "Short form of --opt.", "cat": "other"},

    # ── system / general ──────────────────────────────────────────────────────
    "--force":          {"desc": "Force the operation without confirmation.", "cat": "other"},
    "--volumes":        {"desc": "Include volumes when pruning.", "cat": "volume"},
    "--prune":          {"desc": "Prune unused data.", "cat": "other"},

    # ── stop / kill ───────────────────────────────────────────────────────────
    "--signal":         {"desc": "Signal to send (default SIGKILL for kill, SIGTERM for stop).", "cat": "execution"},
    "-s":               {"desc": "Short form of --signal.", "cat": "execution"},
    "--time":           {"desc": "Seconds to wait before force killing.", "cat": "execution"},

    # ── cp ────────────────────────────────────────────────────────────────────
    "--archive":        {"desc": "Archive mode: preserve uid/gid/timestamps.", "cat": "other"},
    "--follow-link":    {"desc": "Follow symbolic links in the source path.", "cat": "other"},

    # ── commit ────────────────────────────────────────────────────────────────
    "--author":         {"desc": "Author of the committed image.", "cat": "other"},
    "--change":         {"desc": "Apply Dockerfile instruction to image.", "cat": "build"},
    "--message":        {"desc": "Commit message.", "cat": "other"},
    "--pause":          {"desc": "Pause container during commit (default true).", "cat": "execution"},

    # ── save / load / export / import ─────────────────────────────────────────
    "--output":         {"desc": "Write to a file instead of STDOUT.", "cat": "other"},
    "--input":          {"desc": "Read from a tar archive file.", "cat": "other"},

    # ── search ────────────────────────────────────────────────────────────────
    "--limit":          {"desc": "Max number of search results (default 25).", "cat": "output"},
    "--no-trunc":       {"desc": "Don't truncate output.", "cat": "output"},
    "--stars":          {"desc": "Filter to images with at least N stars.", "cat": "output"},

    # ── stats ─────────────────────────────────────────────────────────────────
    "--no-stream":      {"desc": "Disable streaming, print current stats once.", "cat": "output"},
    "--no-trunc":       {"desc": "Don't truncate output.", "cat": "output"},

    # ── update ────────────────────────────────────────────────────────────────
    "--restart":        {"desc": "Restart policy: no|always|on-failure|unless-stopped.", "cat": "execution"},
    "--memory":         {"desc": "Update memory limit.", "cat": "resource"},
    "--cpus":           {"desc": "Update CPU limit.", "cat": "resource"},

    # ── image subcommands ──────────────────────────────────────────────────────
    "--tree":           {"desc": "Show image layer tree.", "cat": "output"},

    # ── context ────────────────────────────────────────────────────────────────
    "--description":    {"desc": "Description of the context.", "cat": "other"},
    "--docker":         {"desc": "Set the docker endpoint.", "cat": "other"},
    "--from":           {"desc": "Create context from named context.", "cat": "other"},

    # ── buildx ─────────────────────────────────────────────────────────────────
    "--builder":        {"desc": "Override the configured builder instance.", "cat": "build"},
    "--load":           {"desc": "Shorthand for --output=type=docker.", "cat": "build"},
    "--push":           {"desc": "Shorthand for --output=type=registry.", "cat": "build"},
    "--sbom":           {"desc": "Attach SBOM attestation to image.", "cat": "build"},
    "--provenance":     {"desc": "Attach provenance attestation to image.", "cat": "build"},
}

# ─── Common typos → correct flag ─────────────────────────────────────────────
TYPO_MAP = {
    "--detch":           "--detach",
    "--deatch":          "--detach",
    "-detatched":        "-d",
    "--porto":           "--port",
    "--ports":           "-p",
    "--volum":           "--volume",
    "--volumne":         "--volume",
    "--enviroment":      "--env",
    "--environmet":      "--env",
    "--environmnet":     "--env",
    "--memorty":         "--memory",
    "--memeory":         "--memory",
    "--netwrok":         "--network",
    "--netowrk":         "--network",
    "--priviledged":     "--privileged",
    "--privilaged":      "--privileged",
    "--entrypoin":       "--entrypoint",
    "--entrypoitn":      "--entrypoint",
    "--workdirr":        "--workdir",
    "--restar":          "--restart",
    "--restert":         "--restart",
    "--no-cach":         "--no-cache",
    "--no-cashe":        "--no-cache",
    "--buid-arg":        "--build-arg",
    "--buiild-arg":      "--build-arg",
    "--taget":           "--target",
    "--platfrom":        "--platform",
    "--platorm":         "--platform",
    "--squassh":         "--squash",
    "--flter":           "--filter",
    "--formatt":         "--format",
    "--follw":           "--follow",
    "--fllow":           "--follow",
    "--timetamp":        "--timestamps",
    "--timstamp":        "--timestamps",
    "--sine":            "--since",
    "--untill":          "--until",
    "--taill":           "--tail",
    "--signall":         "--signal",
    "--forze":           "--force",
    "--forced":          "--force",
    "--autor":           "--author",
    "--mesage":          "--message",
    "--messge":          "--message",
    "--cahnge":          "--change",
    "--chnage":          "--change",
    "--drver":           "--driver",
    "--diver":           "--driver",
    "--subnt":           "--subnet",
    "--gatway":          "--gateway",
    "--gataway":         "--gateway",
    "--iner":            "--internal",
    "--internall":       "--internal",
    "--lmit":            "--limit",
    "--limt":            "--limit",
    "--no-strm":         "--no-stream",
    "--no-strem":        "--no-stream",
    "--hlth-cmd":        "--health-cmd",
    "--healt-cmd":       "--health-cmd",
    "--initt":           "--init",
    "--shm-sze":         "--shm-size",
    "--shmsize":         "--shm-size",
    "--ulimits":         "--ulimit",
    "--dns-serch":       "--dns-search",
    "--dns-srch":        "--dns-search",
    "--add-hst":         "--add-host",
    "--addhost":         "--add-host",
    "--cpu":             "--cpus",
    "--cpus-set":        "--cpuset-cpus",
    "--mem":             "--memory",
    "--memory-lmt":      "--memory-swap",
    "--bldr":            "--builder",
    "--blder":           "--builder",
}

# ─── Pro tips per subcommand ──────────────────────────────────────────────────
PRO_TIPS: Dict[str, List[str]] = {
    "run": [
        "Use '--rm' with one-off tasks to auto-clean containers.",
        "Prefer '--network' over legacy '--link' for container communication.",
        "Set '--restart=unless-stopped' for long-running services.",
        "Use '--memory' and '--cpus' to prevent resource starvation.",
        "Combine '-e' with '--env-file' to keep secrets out of shell history.",
        "Use '--read-only' + '--tmpfs /tmp' for a hardened container.",
        "Use '--init' to properly handle zombie processes.",
        "Pin image versions (myimage:1.2.3), never use ':latest' in production.",
    ],
    "build": [
        "Add a .dockerignore to exclude node_modules, .git from build context.",
        "Use multi-stage builds (--target) to keep final images small.",
        "Place rarely-changing layers (apt-get, pip install) early in Dockerfile.",
        "--no-cache is essential in CI for reproducible builds.",
        "Use --build-arg for env-specific values, not secrets.",
        "Enable BuildKit: set DOCKER_BUILDKIT=1 for parallel builds.",
        "Use --secret for sensitive build-time values like SSH keys.",
        "Use --platform for cross-architecture builds (e.g. linux/arm64).",
    ],
    "exec": [
        "Use 'docker exec -it <name> sh' for containers without bash.",
        "exec only works on running containers — start it first if stopped.",
        "Use '-u root' to exec as root for debugging.",
        "'-d' runs the command detached inside the container.",
    ],
    "ps": [
        "Use '--filter status=exited' to find stopped containers.",
        "'docker ps -q' returns only IDs — pipe to 'docker rm' for bulk cleanup.",
        "--format '{{.Names}}\\t{{.Status}}' gives a custom view.",
        "Use '--no-trunc' to see full container IDs.",
    ],
    "logs": [
        "'docker logs -f --tail=100' is fastest for tailing recent output.",
        "Use --timestamps to correlate logs across services.",
        "Consider --log-driver=journald for production workloads.",
        "Use --since=1h to see only recent logs.",
    ],
    "network": [
        "Custom bridge networks provide automatic DNS between containers.",
        "Use --internal to isolate a network from outside.",
        "Overlay networks are required for multi-host Swarm communication.",
        "Use 'docker network inspect' to debug connectivity issues.",
    ],
    "volume": [
        "Named volumes survive 'docker rm'; bind mounts depend on host path.",
        "Use 'docker volume prune' to clean up unused volumes.",
        "--mount is more explicit and readable than -v for complex cases.",
        "Use 'docker volume inspect' to find where data is stored on the host.",
    ],
    "pull": [
        "Always specify a tag — ':latest' may not be what you expect.",
        "Use '--platform' to pull images for a specific architecture.",
        "Use 'docker pull' before 'docker run' to pre-cache images.",
    ],
    "push": [
        "Login first with 'docker login' before pushing.",
        "Tag your image properly: registry/username/image:tag.",
        "Use multi-arch manifests (buildx --push) for cross-platform images.",
    ],
    "stop": [
        "Use '--time' to give the container more time to gracefully shut down.",
        "Containers receive SIGTERM first, then SIGKILL after the timeout.",
        "Use 'docker stop $(docker ps -q)' to stop all running containers.",
    ],
    "rm": [
        "Use '-f' to force-remove a running container.",
        "Use 'docker rm $(docker ps -aq)' to remove all stopped containers.",
        "Use '--volumes' to also remove associated anonymous volumes.",
        "'docker container prune' removes all stopped containers at once.",
    ],
    "rmi": [
        "Use '-f' to force-remove an image used by stopped containers.",
        "Use 'docker image prune -a' to remove all unused images.",
        "Remove dangling images with 'docker rmi $(docker images -f dangling=true -q)'.",
    ],
    "images": [
        "Use '--filter dangling=true' to find untagged intermediate images.",
        "'docker images -q' returns only image IDs for scripting.",
        "Use '--digests' to see the image content hash.",
        "Use 'docker image inspect' for full image metadata.",
    ],
    "inspect": [
        "Use '-f' with Go templates to extract specific fields.",
        "Works on containers, images, networks, and volumes.",
        "Use 'docker inspect --format={{.NetworkSettings.IPAddress}}' to get IP.",
    ],
    "commit": [
        "Prefer Dockerfiles over commit for reproducibility.",
        "Use '--change' to add Dockerfile instructions to the committed image.",
        "Always tag committed images: docker commit <container> name:tag.",
    ],
    "tag": [
        "Tagging doesn't copy the image — it just creates a new reference.",
        "Use this before 'docker push' to set the registry/repo/tag.",
    ],
    "cp": [
        "Syntax: docker cp <container>:<path> <local_path> (or reverse).",
        "Works on both running and stopped containers.",
        "Use '--archive' to preserve file ownership.",
    ],
    "stats": [
        "Use '--no-stream' for a one-shot snapshot.",
        "Use '--format' to customise the output columns.",
        "Pipe to a file for basic monitoring over time.",
    ],
    "system": [
        "Use 'docker system prune -a' to reclaim all unused disk space.",
        "Use 'docker system df' to see disk usage breakdown.",
        "Add '--volumes' to also prune unused volumes.",
    ],
    "buildx": [
        "Use 'docker buildx create --use' to set a new builder instance.",
        "Build multi-arch images with --platform=linux/amd64,linux/arm64.",
        "Use --push to build and push directly to the registry.",
        "BuildKit is required and enabled automatically with buildx.",
    ],
    "compose": [
        "Use '-f' to specify a custom compose file.",
        "Use 'docker compose up -d' to start services in the background.",
        "Use 'docker compose logs -f' to tail all service logs.",
        "Use 'docker compose down -v' to also remove volumes.",
    ],
    "swarm": [
        "Run 'docker swarm init' on the manager node to start a swarm.",
        "Use 'docker swarm join-token worker' to get the join command.",
        "Drain a node before maintenance: 'docker node update --availability drain'.",
    ],
    "service": [
        "Use 'docker service scale <name>=N' to scale replicas.",
        "Use 'docker service update' to roll out new image versions.",
        "Use 'docker service logs' to tail distributed service logs.",
    ],
    "secret": [
        "Secrets are only available to services, not standalone containers.",
        "Use 'docker secret create' to store secrets securely.",
        "Secrets are mounted at /run/secrets/<name> inside the container.",
    ],
    "stack": [
        "Deploy with 'docker stack deploy -c docker-compose.yml <name>'.",
        "Use 'docker stack ps' to see task status across the swarm.",
        "Use 'docker stack rm' to remove all services in a stack.",
    ],
    "context": [
        "Use 'docker context use <name>' to switch between Docker endpoints.",
        "Contexts let you manage remote Docker hosts without SSH manually.",
        "List contexts with 'docker context ls'.",
    ],
    "scout": [
        "Use 'docker scout cves <image>' to see CVEs in an image.",
        "Use 'docker scout recommendations' for upgrade suggestions.",
        "Integrate with CI for automatic vulnerability scanning.",
    ],
    "attach": [
        "Use Ctrl+P then Ctrl+Q to detach without stopping the container.",
        "attach connects to the main process — use exec for a new shell.",
        "Only works on running containers with an open TTY.",
    ],
    "history": [
        "Shows all layers of an image and their sizes.",
        "Use '--no-trunc' to see full commands used to build each layer.",
        "Useful for debugging large or unexpected image sizes.",
    ],
    "create": [
        "Creates a container without starting it.",
        "Use 'docker start <name>' to start it later.",
        "Accepts all the same flags as 'docker run'.",
    ],
    "pause": [
        "Pauses all processes using cgroups freezer.",
        "Use 'docker unpause' to resume.",
        "Useful for taking consistent snapshots.",
    ],
    "unpause": [
        "Resumes all paused processes in a container.",
        "Use after 'docker pause' to continue execution.",
    ],
    "port": [
        "Shows which host ports are mapped to the container.",
        "Use 'docker port <container> <port>' to check a specific port.",
    ],
    "rename": [
        "Renaming doesn't affect the container ID.",
        "Other containers using '--link' by old name will break.",
    ],
    "wait": [
        "Blocks until the container stops and prints its exit code.",
        "Useful in scripts to wait for a container to finish.",
    ],
    "diff": [
        "Shows A (added), C (changed), D (deleted) files.",
        "Useful for understanding what a container has modified.",
    ],
    "events": [
        "Use '--filter type=container' to filter event types.",
        "Use '--since' and '--until' to scope the event window.",
        "Useful for monitoring and debugging Docker daemon activity.",
    ],
    "export": [
        "Exports the container filesystem — not the image layers.",
        "Use 'docker import' to create an image from the export.",
        "Note: export flattens all layers into one.",
    ],
    "import": [
        "Creates a flat single-layer image from a tarball.",
        "Use '--change' to apply Dockerfile instructions during import.",
    ],
    "save": [
        "Saves the full image with all layers and tags.",
        "Use 'docker load' to restore the image on another host.",
        "Useful for air-gapped environments without a registry.",
    ],
    "load": [
        "Loads an image from a tar archive created by 'docker save'.",
        "Use '-i' to specify the input file instead of STDIN.",
    ],
    "search": [
        "Only searches Docker Hub — not other registries.",
        "Use '--filter stars=100' to find popular images.",
        "Always review the Dockerfile of unknown images before use.",
    ],
    "login": [
        "Credentials are stored in ~/.docker/config.json.",
        "Use a credential helper for better security.",
        "Use '--password-stdin' to avoid password in shell history.",
    ],
    "logout": [
        "Removes stored credentials for the registry.",
        "Default registry is Docker Hub if none specified.",
    ],
    "update": [
        "Use to change resource limits on running containers.",
        "Changes take effect immediately without restarting.",
        "Use 'docker inspect' to verify the updated values.",
    ],
    "kill": [
        "Sends SIGKILL by default — immediate termination.",
        "Use '--signal' to send a custom signal (e.g. SIGHUP).",
        "Use 'docker stop' for graceful shutdown instead.",
    ],
    "version": [
        "Shows both client and server (daemon) versions.",
        "Useful for debugging version mismatch issues.",
    ],
    "info": [
        "Shows system-wide Docker configuration and resource usage.",
        "Check 'Storage Driver' and 'Cgroup Driver' for compatibility.",
    ],
    "top": [
        "Shows processes running inside the container.",
        "Accepts ps options (e.g. docker top <container> aux).",
    ],
    "default": [
        "Use 'docker system prune -a' to reclaim disk space.",
        "Always pin image versions in production — never ':latest'.",
        "Use 'docker inspect' to get full metadata on any object.",
        "Docker Compose is recommended for multi-container apps.",
        "Use 'docker stats' to monitor resource usage in real time.",
    ],
}

ALL_SUBCOMMANDS_LIST = sorted(DOCKER_SUBCOMMANDS)


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


def _tokenize_command(command: str) -> List[str]:
    command = command.strip()
    if command.lower().startswith("docker"):
        command = command[6:].strip()
    tokens = re.findall(r"'[^']*'|\"[^\"]*\"|\S+", command)
    return tokens


def _find_typo(token: str) -> Optional[Tuple[str, str]]:
    if token in TYPO_MAP:
        return TYPO_MAP[token], f"'{token}' is a common misspelling."
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

    subcommand_raw = tokens[0]
    subcommand = subcommand_raw.lower()
    rest = tokens[1:]

    subcommand_known = subcommand in DOCKER_SUBCOMMANDS
    subcommand_typo = None
    if not subcommand_known:
        subcommand_typo = _closest_subcommand(subcommand)

    flags_found: List[Dict] = []
    typos_found: List[Dict] = []
    positional_args: List[str] = []

    i = 0
    known_flag_count = 0
    while i < len(rest):
        token = rest[i]

        if re.match(r"^-[a-zA-Z]{2,}$", token) and not token.startswith("--"):
            for ch in token[1:]:
                f = f"-{ch}"
                if f in FLAG_DB:
                    known_flag_count += 1
                    info = FLAG_DB[f]
                    flags_found.append({"flag": f, "description": info["desc"], "category": info["cat"]})
                else:
                    flags_found.append({"flag": f, "description": f"Short flag -{ch} (not in knowledge base).", "category": "other"})
            i += 1
            continue

        if token.startswith("-"):
            flag_part = token
            value_part = None
            if "=" in token:
                flag_part, value_part = token.split("=", 1)

            typo = _find_typo(flag_part)
            if typo:
                suggestion, msg = typo
                typos_found.append({"original": flag_part, "suggestion": suggestion, "message": msg})

            if flag_part in FLAG_DB:
                known_flag_count += 1
                info = FLAG_DB[flag_part]
                entry: Dict = {"flag": flag_part, "description": info["desc"], "category": info["cat"]}
                if value_part:
                    entry["value"] = value_part
                elif i + 1 < len(rest) and not rest[i + 1].startswith("-"):
                    entry["value"] = rest[i + 1]
                    i += 1
                flags_found.append(entry)
            else:
                entry = {"flag": flag_part, "description": f"Flag '{flag_part}' not found in knowledge base.", "category": "other"}
                if value_part:
                    entry["value"] = value_part
                flags_found.append(entry)
        else:
            positional_args.append(token)

        i += 1

    if subcommand_typo:
        typos_found.insert(0, {
            "original": subcommand_raw,
            "suggestion": subcommand_typo,
            "message": f"Unknown subcommand '{subcommand_raw}'. Did you mean '{subcommand_typo}'?",
        })

    total_flags = len(flags_found)
    flag_ratio = (known_flag_count / total_flags) if total_flags > 0 else 1.0
    confidence = _compute_confidence(subcommand_known, flag_ratio, len(typos_found), bool(positional_args))
    valid = subcommand_known and len(typos_found) == 0 and confidence >= 0.45

    if not subcommand_known:
        summary = f"Unrecognised subcommand '{subcommand_raw}'.{' Possible match: docker ' + subcommand_typo if subcommand_typo else ''}"
    elif typos_found:
        summary = f"Command 'docker {subcommand}' is valid but contains {len(typos_found)} likely typo(s) in flags."
    elif total_flags == 0:
        summary = f"'docker {subcommand}' with no flags — simple invocation."
    else:
        flag_names = ", ".join(f["flag"] for f in flags_found[:4])
        extra = f" (+{total_flags - 4} more)" if total_flags > 4 else ""
        summary = f"Valid 'docker {subcommand}' command using: {flag_names}{extra}."

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