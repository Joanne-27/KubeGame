# Cluster Heist: The Helm Job

> *A terminal-based educational Kubernetes adventure. Break into ClusterBank — one misconfiguration at a time.*

---

## Story

You are **Ghost**, an elite Kubernetes operative hired by a shadowy crew to crack **ClusterBank** — the most secure Kubernetes-powered vault in the world. Intel confirms the cluster is riddled with misconfigurations left behind by a careless admin. That's your way in.

The CLI acts as your **Game Master**: it narrates the story, hands you objectives, and verifies your work against the live cluster. It never fixes anything for you. Every `kubectl` and `helm` command you run is real.

**Estimated duration:** 45–50 minutes  
**Starting credits:** 100 (−5 per hint, max 3 hints per mission)

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| `kubectl` | ≥ 1.28 | https://kubernetes.io/docs/tasks/tools/ |
| `helm` | ≥ 3.12 | https://helm.sh/docs/intro/install/ |
| `minikube` | ≥ 1.32 | https://minikube.sigs.k8s.io/docs/start/ |
| Python | ≥ 3.11 | https://www.python.org/downloads/ |

### Enable the Ingress addon (required for Final Boss)

```bash
minikube start --driver=docker
minikube addons enable ingress
```

Verify the ingress controller is running:

```bash
kubectl get pods -n ingress-nginx
```

Add the game host to your local `/etc/hosts` (or `C:\Windows\System32\drivers\etc\hosts` on Windows):

```bash
echo "$(minikube ip)  cluster-heist.local" | sudo tee -a /etc/hosts
```

---

## Quickstart

### 1. Clone and enter the project

```bash
git clone <repo-url>
cd cluster-heist
```

### 2. Run setup

```bash
chmod +x scripts/setup.sh scripts/reset.sh
./scripts/setup.sh
```

This verifies your tools, creates the `cluster-heist` namespace, and initialises the game state file.

### 3. Deploy the target application

```bash
helm install cluster-heist charts/cluster-heist \
  --namespace cluster-heist \
  --create-namespace
```

### 4. Install CLI dependencies

```bash
cd cli
pip install -r requirements.txt
cd ..
```

### 5. Start the game

```bash
python cli/src/main.py start
```

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `python cli/src/main.py start` | Display intro narrative and Mission 1 brief |
| `python cli/src/main.py status` | Live dashboard: mission, credits, checklist |
| `python cli/src/main.py hint` | Reveal next hint for current mission (−5 credits) |
| `python cli/src/main.py verify` | Check your fix against the live cluster |
| `python cli/src/main.py score` | Final score, rank, and achievements |

---

## Split-Terminal Workflow (Recommended)

Open two terminal panes side by side:

**Left pane — Game Master (read-only)**
```bash
watch -n 3 python cli/src/main.py status
```

**Right pane — Operative (your kubectl/helm workspace)**
```bash
kubectl get pods -n cluster-heist -w
```

This lets you see mission progress update in real time as you fix each misconfiguration.

On **tmux**:
```bash
tmux new-session \; split-window -h \; send-keys -t 0 'watch -n 3 python cli/src/main.py status' Enter
```

---

## Mission Overview

| # | Codename | K8s Concept |
|---|----------|-------------|
| 1 | The Sleeping Guard Pod | `ImagePullBackOff` diagnosis |
| 2 | The Door With the Wrong Label | Service selectors & endpoints |
| 3 | The ConfigMap Combination Lock | ConfigMaps & env injection |
| 4 | The Secret Vault Key | Kubernetes Secrets |
| 5 | The Sidecar Informant | Multi-container pods & log streaming |
| 6 | The Redis Red Herring | Cluster DNS & service discovery |
| 7 | The Helm Upgrade Gambit | `helm upgrade` & values overrides |
| ★ | The Two-Service Betrayal | Ingress & cross-service DNS |

---

## Scoring & Ranks

| Credits | Rank |
|---------|------|
| 90–100 | Cluster Heist Legend |
| 75–89 | Helm Bender |
| 60–74 | DNS Diplomat |
| 40–59 | YAML Survivor |
| < 40 | CrashLoop Apprentice |

---

## Reset

To wipe the cluster state and start fresh:

```bash
./scripts/reset.sh
```

---

## Project Structure

```
cluster-heist/
  README.md
  SKILLS.md
  ARCHITECTURE.md
  cli/
    src/main.py
    requirements.txt
    .cluster-heist-state.json
  charts/
    cluster-heist/
      Chart.yaml
      values.yaml
      templates/
  k8s/
    broken/      ← instructor reference: pre-fix manifests
    fixed/       ← instructor reference: post-fix answer key
  scripts/
    setup.sh
    reset.sh
```
