#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="cluster-heist"
STATE_FILE="cli/.cluster-heist-state.json"
RELEASE_NAME="cluster-heist"

# ── Dependency checks ────────────────────────────────────────────────────────
for cmd in kubectl helm; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "[ERROR] '$cmd' is not installed or not in PATH." >&2
    exit 1
  fi
done
echo "[OK] kubectl and helm found."

# ── Cluster reachability ─────────────────────────────────────────────────────
if ! kubectl cluster-info &>/dev/null; then
  echo "[ERROR] No reachable Kubernetes cluster. Start Minikube with: minikube start" >&2
  exit 1
fi
echo "[OK] Cluster is reachable."

# ── Namespace ────────────────────────────────────────────────────────────────
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
  kubectl create namespace "$NAMESPACE"
  echo "[OK] Namespace '$NAMESPACE' created."
else
  echo "[OK] Namespace '$NAMESPACE' already exists."
fi

# ── State file ───────────────────────────────────────────────────────────────
mkdir -p "$(dirname "$STATE_FILE")"
cat > "$STATE_FILE" <<'EOF'
{
  "current_mission": 1,
  "score": 100,
  "hints_used": 0,
  "missions": {
    "mission_1": false,
    "mission_2": false,
    "mission_3": false,
    "mission_4": false,
    "mission_5": false,
    "mission_6": false,
    "mission_7": false,
    "final_boss": false
  }
}
EOF
echo "[OK] State file initialised at '$STATE_FILE'."

echo ""
echo "✅  Cluster Heist setup complete. Run: python cli/src/main.py"
