#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <nextflow-workdir>" >&2
    exit 1
fi

WORKDIR=$(realpath "$1")
CMD_RUN="$WORKDIR/.command.run"
CMD_SH="$WORKDIR/.command.sh"
CONTAINER_NAME="${NF_DEBUG_NAME:-nf-debug}"
DEBUG_PORT="${NF_DEBUG_PORT:-5678}"
DEBUG_DIR="${NF_DEBUG_DIR:-/nf-debug}"   # path inside the container

[[ -f "$CMD_RUN" ]] || { echo "Error: $CMD_RUN not found" >&2; exit 1; }
[[ -f "$CMD_SH"  ]] || { echo "Error: $CMD_SH not found"  >&2; exit 1; }

# ------------------------------------------------------------
# 1. Generate launch.json to a temp file on the host
# ------------------------------------------------------------
TMP_LAUNCH=$(mktemp)
trap 'rm -f "$TMP_LAUNCH"' EXIT

python3 - "$CMD_SH" "$WORKDIR" > "$TMP_LAUNCH" <<'PYEOF'
import shlex, json, re, sys

cmd_sh, workdir = sys.argv[1], sys.argv[2]
with open(cmd_sh) as f:
    content = f.read()

candidates = []
for line in content.splitlines():
    s = line.strip()
    if not s or s.startswith('#'):
        continue
    try:
        tokens = shlex.split(s)
    except ValueError:
        continue
    i = 0
    while i < len(tokens) and re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', tokens[i]):
        i += 1
    if i < len(tokens) and re.match(r'^python[0-9.]*$', tokens[i]):
        candidates.append((tokens, i))

if not candidates:
    sys.stderr.write("No python invocation found in .command.sh\n")
    sys.exit(1)
if len(candidates) > 1:
    sys.stderr.write(
        f"Note: {len(candidates)} python invocations found, using the last one\n")

tokens, py_idx = candidates[-1]

env = {}
for t in tokens[:py_idx]:
    k, _, v = t.partition('=')
    env[k] = v

i = py_idx + 1
module = program = None
while i < len(tokens):
    t = tokens[i]
    if t == '-m':
        module = tokens[i + 1]; i += 2; break
    elif t.startswith('-'):
        i += 1
    else:
        program = t; i += 1; break

args = tokens[i:]

cfg = {
    "name": "Debug nextflow task",
    "type": "debugpy",
    "request": "launch",
    "console": "integratedTerminal",
    "cwd": workdir,
    "args": args,
    "justMyCode": False,
}
if module:  cfg["module"]  = module
else:       cfg["program"] = program
if env:     cfg["env"]     = env

print(json.dumps({"version": "0.2.0", "configurations": [cfg]}, indent=2))
PYEOF

# ------------------------------------------------------------
# 2. Build & run the docker command
# ------------------------------------------------------------
DOCKER_LINE=$(grep -E '^[[:space:]]*docker run' "$CMD_RUN" | head -1 | sed 's/^[[:space:]]*//')
[[ -n "$DOCKER_LINE" ]] || { echo "Error: no 'docker run' line found in $CMD_RUN" >&2; exit 1; }

export NXF_TASK_WORKDIR="$WORKDIR"
export NXF_BOXID="$CONTAINER_NAME"

SSH_MOUNT_FLAGS=""
if [[ -n "${NF_DEBUG_GIT_KEY:-}" ]]; then
    SSH_DIR="$HOME/.ssh"
    KEY_PATH="$SSH_DIR/$NF_DEBUG_GIT_KEY"
    if [[ ! -f "$KEY_PATH" ]]; then
        echo "==> WARNING: SSH key '$KEY_PATH' does not exist on host" >&2
        echo "    The mount and GIT_SSH_COMMAND will still be set, but git operations will fail." >&2
    fi
    echo "==> SSH: mounting $SSH_DIR (read-only) and setting GIT_SSH_COMMAND"
    echo "    key in container: $KEY_PATH"
    SSH_MOUNT_FLAGS=" -v $SSH_DIR:$SSH_DIR:ro -e GIT_SSH_COMMAND=\"ssh -i $KEY_PATH -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null\""
else
    echo "==> SSH: NF_DEBUG_GIT_KEY not set — skipping .ssh mount and GIT_SSH_COMMAND export"
    echo "    (set NF_DEBUG_GIT_KEY=<keyname> to enable git/SSH inside the container)"
fi
echo

MODIFIED=$(echo "$DOCKER_LINE" \
    | sed 's|^docker run -i |docker run -dit |' \
    | sed 's| /bin/bash -ue [^ ]*$||' \
    | sed "s| --name [^ ]*| --name $CONTAINER_NAME -p $DEBUG_PORT:$DEBUG_PORT$SSH_MOUNT_FLAGS|")
MODIFIED="$MODIFIED sleep infinity"

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
    echo "==> Removing existing container '$CONTAINER_NAME'..."
    docker rm -f "$CONTAINER_NAME" >/dev/null
fi

echo "==> Launching:"
echo "    $MODIFIED"
echo
eval "$MODIFIED"

# ------------------------------------------------------------
# 3. Copy launch.json into the container (root, to avoid perm issues)
# ------------------------------------------------------------
echo "==> Installing launch.json at /home/ubuntu/.vscode/launch.json inside container"
docker exec -u 0 "$CONTAINER_NAME" mkdir -p "/home/ubuntu/.vscode"
docker cp "$TMP_LAUNCH" "$CONTAINER_NAME:/home/ubuntu/.vscode/launch.json"

echo
echo "==> Container '$CONTAINER_NAME' is up. To enter a shell inside:"
echo "    docker exec -it $CONTAINER_NAME bash"
echo
echo "==> For debugging in vscode:"
echo "    Generated launch.json (now in container at /home/ubuntu/.vscode/launch.json):"
echo "    Cmd+Shift+P -> Dev Containers: Attach to Running Container -> $CONTAINER_NAME"
echo
echo "==> after you are done, run:"
echo "    docker container stop nf-debug"
