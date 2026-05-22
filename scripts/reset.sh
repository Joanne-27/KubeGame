#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="cluster-heist"
STATE_FILE="cli/.cluster-heist-state.json"
RELEASE_NAME="cluster-heist"

# ── Safety confirmation ──────────────────────────────────────────────────────
echo "⚠️  This will uninstall the Helm release, purge all game resources in"
echo "   namespace '$NAMESPACE', and reset the state file."
read -rp "Type 'yes' to confirm: " confirm
if [[ "$confirm" != "yes" ]]; then
  echo "Aborted."
  exit 0
fi

# ── Uninstall Helm release ───────────────────────────────────────────────────
if helm status "$RELEASE_NAME" -n "$NAMESPACE" &>/dev/null; then
  helm uninstall "$RELEASE_NAME" -n "$NAMESPACE"
  echo "[OK] Helm release '$RELEASE_NAME' uninstalled."
else
  echo "[SKIP] No Helm release '$RELEASE_NAME' found."
fi

# ── Purge dangling resources ─────────────────────────────────────────────────
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
  kubectl delete all --all -n "$NAMESPACE" --ignore-not-found
  kubectl delete configmap,secret --all -n "$NAMESPACE" --ignore-not-found
  echo "[OK] Namespace '$NAMESPACE' purged."
else
  echo "[SKIP] Namespace '$NAMESPACE' not found."
fi

# ── Reset state file ─────────────────────────────────────────────────────────
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
echo "[OK] State file reset at '$STATE_FILE'."

echo ""
echo "✅  Reset complete. Run scripts/setup.sh to start fresh."
