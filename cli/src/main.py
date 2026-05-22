#!/usr/bin/env python3
"""Cluster Heist: The Helm Job — Game Master CLI"""

import io
import json
import os
import subprocess
import sys
from pathlib import Path

# Force UTF-8 on Windows legacy consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

# ── Paths ────────────────────────────────────────────────────────────────────
# Resolve relative to repo root regardless of where the script is invoked from
_REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = _REPO_ROOT / "cli" / ".cluster-heist-state.json"
SETUP_SCRIPT = _REPO_ROOT / "scripts" / "setup.sh"

# ── State helpers ─────────────────────────────────────────────────────────────
DEFAULT_STATE = {
    "current_mission": 1,
    "score": 100,
    "hints_used": 0,
    "missions": {
        "mission_1": False, "mission_2": False, "mission_3": False,
        "mission_4": False, "mission_5": False, "mission_6": False,
        "mission_7": False, "final_boss": False,
    },
}

def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return dict(DEFAULT_STATE)

def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

# ── Mission data ──────────────────────────────────────────────────────────────
MISSIONS = {
    1: {
        "name": "The Sleeping Guard Pod",
        "objective": "A guard pod refuses to wake up. Diagnose the broken image and patch it.",
        "skill": "Pod Statuses & Diagnostics (ImagePullBackOff)",
        "hints": [
            "[cyan]Run [bold]kubectl get pods -n cluster-heist[/bold] and look for a pod stuck in [red]ImagePullBackOff[/red].[/cyan]",
            "[cyan]Use [bold]kubectl describe pod <pod-name> -n cluster-heist[/bold] and read the Events section carefully.[/cyan]",
            "[cyan]The image name contains a typo: [bold]nginxx[/bold] → fix it to [bold]nginx[/bold] using [bold]kubectl set image[/bold] or edit the deployment.[/cyan]",
        ],
    },
    2: {
        "name": "The Door With the Wrong Label",
        "objective": "The service doorway points nowhere. Fix the selector so traffic flows.",
        "skill": "Services, Label Matching & Endpoints",
        "hints": [
            "[cyan]Run [bold]kubectl get endpoints -n cluster-heist[/bold] — if the endpoint list is empty, the selector is broken.[/cyan]",
            "[cyan]Compare [bold]kubectl get svc <svc> -n cluster-heist -o yaml[/bold] selector vs [bold]kubectl get pods --show-labels[/bold].[/cyan]",
            "[cyan]The selector says [bold]app: gaurd[/bold] — fix the typo to [bold]app: guard[/bold] with [bold]kubectl edit svc[/bold].[/cyan]",
        ],
    },
    3: {
        "name": "The ConfigMap Combination Lock",
        "objective": "Inject VAULT_MODE and ROOM_NAME into the deployment via a ConfigMap.",
        "skill": "ConfigMaps & Environment Variables",
        "hints": [
            "[cyan]Check existing ConfigMaps: [bold]kubectl get configmap -n cluster-heist[/bold].[/cyan]",
            "[cyan]Create or edit a ConfigMap with keys [bold]VAULT_MODE=training[/bold] and [bold]ROOM_NAME=helm-lab[/bold].[/cyan]",
            "[cyan]Reference the ConfigMap in the deployment under [bold]envFrom.configMapRef[/bold] and rollout restart.[/cyan]",
        ],
    },
    4: {
        "name": "The Secret Vault Key",
        "objective": "Inject VAULT_TOKEN securely using a Kubernetes Secret.",
        "skill": "Kubernetes Secrets",
        "hints": [
            "[cyan]Run [bold]kubectl get secrets -n cluster-heist[/bold] to see what exists.[/cyan]",
            "[cyan]Create a secret: [bold]kubectl create secret generic vault-key --from-literal=VAULT_TOKEN=golden-yaml-42 -n cluster-heist[/bold].[/cyan]",
            "[cyan]Mount it as an env var in the deployment using [bold]secretKeyRef[/bold], then restart the pod.[/cyan]",
        ],
    },
    5: {
        "name": "The Sidecar Informant",
        "objective": "Extract hidden clue parameters from two sidecar container logs.",
        "skill": "Multi-container Pods & Log Streaming",
        "hints": [
            "[cyan]List pods: [bold]kubectl get pods -n cluster-heist[/bold] and find the multi-container pod.[/cyan]",
            "[cyan]Stream logs from the first sidecar: [bold]kubectl logs <pod> -c clue-log-1 -n cluster-heist[/bold].[/cyan]",
            "[cyan]Do the same for [bold]-c clue-log-2[/bold] and combine both clue values as instructed.[/cyan]",
        ],
    },
    6: {
        "name": "The Redis Red Herring",
        "objective": "Replace hardcoded localhost DB references with the redis-service DNS name.",
        "skill": "Internal Service Discovery & Cluster DNS",
        "hints": [
            "[cyan]Inspect the deployment env vars: [bold]kubectl describe deployment -n cluster-heist[/bold].[/cyan]",
            "[cyan]Find any env var pointing to [bold]localhost[/bold] for Redis.[/cyan]",
            "[cyan]Update it to [bold]redis-service[/bold] — Kubernetes DNS resolves service names within the same namespace.[/cyan]",
        ],
    },
    7: {
        "name": "The Helm Upgrade Gambit",
        "objective": "Edit values.yaml to scale replicas to 3, swap image tags, and enable vault settings.",
        "skill": "Helm Chart Architecture & helm upgrade",
        "hints": [
            "[cyan]Inspect the chart: [bold]helm show values charts/cluster-heist[/bold] or open [bold]charts/cluster-heist/values.yaml[/bold].[/cyan]",
            "[cyan]Set [bold]replicaCount: 3[/bold], update the image tag to the stable version, and set vault flags to true.[/cyan]",
            "[cyan]Apply with: [bold]helm upgrade cluster-heist charts/cluster-heist -n cluster-heist -f charts/cluster-heist/values.yaml[/bold].[/cyan]",
        ],
    },
    8: {
        "name": "Final Boss: The Two-Service Betrayal",
        "objective": "Fix inter-service Spring Boot env vars so DNS routing resolves through the Ingress.",
        "skill": "Ingress Rules & Cross-Service DNS",
        "hints": [
            "[cyan]Check both service deployments for hardcoded IPs or wrong service names in env vars.[/cyan]",
            "[cyan]Use [bold]kubectl get ingress -n cluster-heist[/bold] to confirm Ingress hostnames.[/cyan]",
            "[cyan]Update each service's env var to reference the other by its Kubernetes service name, not an IP.[/cyan]",
        ],
    },
}

MISSION_KEYS = [
    "mission_1", "mission_2", "mission_3", "mission_4",
    "mission_5", "mission_6", "mission_7", "final_boss",
]

def mission_display_name(key: str) -> str:
    idx = MISSION_KEYS.index(key)
    m_num = idx + 1 if key != "final_boss" else 8
    return f"Mission {m_num}: {MISSIONS[m_num]['name']}"

def rank(score: int) -> tuple[str, str]:
    if score >= 90:   return "Cluster Heist Legend", "bold gold1"
    if score >= 75:   return "Helm Bender",          "bold cyan"
    if score >= 60:   return "DNS Diplomat",          "bold green"
    if score >= 40:   return "YAML Survivor",         "bold yellow"
    return               "CrashLoop Apprentice",      "bold red"

# ── CLI ───────────────────────────────────────────────────────────────────────
@click.group()
def cli():
    """[bold red]Cluster Heist: The Helm Job[/bold red] — Game Master CLI"""

@cli.command()
def start():
    """Display intro narrative, verify cluster, and print Mission 1."""
    console.print(Panel.fit(
        Text.from_markup(
            "[bold red]*** CLUSTER HEIST : THE HELM JOB ***[/bold red]\n\n"
            "[green]You are [bold]Ghost[/bold], an elite Kubernetes operative.\n"
            "Your target: [bold]ClusterBank[/bold] -- the most secure\n"
            "Kubernetes-powered vault in the world.\n\n"
            "Intel says the cluster is riddled with\n"
            "misconfigurations. That's your way in.\n\n"
            "[yellow]Fix what's broken. Don't get caught.\n"
            "The crew is counting on you.[/yellow][/green]"
        ),
        title="[bold red]// INCOMING TRANSMISSION //[/bold red]",
        border_style="red",
    ))

    console.print("\n[bold yellow]▶ Verifying cluster access...[/bold yellow]")
    result = subprocess.run(["kubectl", "cluster-info"], capture_output=True, text=True)
    if result.returncode != 0:
        console.print("[bold red][ERROR][/bold red] No cluster reachable. Run [bold]minikube start[/bold] first.")
        sys.exit(1)
    console.print("[bold green][OK][/bold green] Cluster is live.\n")

    # Alias tip
    script_path = Path(__file__).resolve()
    console.print(Panel.fit(
        f"[bold cyan]Save yourself some typing -- add this alias:[/bold cyan]\n\n"
        f"[bold yellow]echo \"alias cluster-heist='python3 {script_path}'\" >> ~/.bashrc && source ~/.bashrc[/bold yellow]\n\n"
        f"[dim]Then use [bold]cluster-heist <command>[/bold] instead of the full python3 path.[/dim]",
        title="[bold cyan]// QUICK SETUP //[/bold cyan]",
        border_style="cyan",
    ))

    # How to play
    console.print(Panel(
        "[bold white]HOW TO PLAY[/bold white]\n\n"
        "[green]1.[/green] Read the mission objective below\n"
        "[green]2.[/green] Use [bold]kubectl[/bold] and [bold]helm[/bold] commands to find and fix the misconfiguration\n"
        "[green]3.[/green] Run [bold cyan]cluster-heist verify[/bold cyan] to check your fix\n"
        "[green]4.[/green] Pass verification to unlock the next mission\n\n"
        "[bold white]COMMANDS[/bold white]\n\n"
        "  [bold cyan]cluster-heist status[/bold cyan]   -- live dashboard: mission, credits, checklist\n"
        "  [bold cyan]cluster-heist hint[/bold cyan]     -- reveal next hint (-5 credits each, max 3)\n"
        "  [bold cyan]cluster-heist verify[/bold cyan]   -- check your fix against the live cluster\n"
        "  [bold cyan]cluster-heist score[/bold cyan]    -- final rank and achievements\n\n"
        "[dim]Starting credits: 100  |  Ranks: Legend / Helm Bender / DNS Diplomat / YAML Survivor / CrashLoop Apprentice[/dim]",
        title="[bold green]// BRIEFING //[/bold green]",
        border_style="green",
    ))

    _print_mission(1)

@cli.command()
def status():
    """Print the current game dashboard."""
    state = load_state()
    cur = state["current_mission"]
    score = state["score"]
    hints = state["hints_used"]
    r_name, _ = rank(score)

    # Header panel
    console.print(Panel.fit(
        f"[bold cyan]Mission:[/bold cyan]  {MISSIONS[min(cur, 8)]['name']}\n"
        f"[bold green]Credits:[/bold green]  [bold]{score}[/bold] / 100\n"
        f"[bold yellow]Hints Used:[/bold yellow] {hints}\n"
        f"[bold magenta]Current Rank:[/bold magenta] {r_name}",
        title="[bold red]// HEIST STATUS //[/bold red]",
        border_style="cyan",
    ))

    # Mission checklist
    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    table.add_column("", width=3)
    table.add_column("Mission", style="white")
    table.add_column("Status", justify="center")

    for key in MISSION_KEYS:
        done = state["missions"].get(key, False)
        icon = "[bold green]✔[/bold green]" if done else "[dim]○[/dim]"
        status_text = "[green]COMPLETE[/green]" if done else "[dim]LOCKED[/dim]"
        table.add_row(icon, mission_display_name(key), status_text)

    console.print(table)

@cli.command()
def score():
    """Show final score, rank, and achievements."""
    state = load_state()
    s = state["score"]
    r_name, r_style = rank(s)
    completed = sum(1 for v in state["missions"].values() if v)

    console.print(Panel.fit(
        f"[bold green]Credits Remaining:[/bold green] [bold]{s}[/bold] / 100\n"
        f"[bold yellow]Missions Completed:[/bold yellow] {completed} / 8\n"
        f"[bold cyan]Hints Used:[/bold cyan] {state['hints_used']}\n\n"
        f"[{r_style}]🏆  RANK: {r_name}[/{r_style}]",
        title="[bold red]// SCORE REPORT //[/bold red]",
        border_style="green",
    ))

    # Achievements
    achievements = []
    if state["hints_used"] == 0:
        achievements.append("[bold gold1]🥇 Ghost Operative[/bold gold1] — Completed without any hints")
    if s == 100:
        achievements.append("[bold gold1]💯 Perfect Heist[/bold gold1] — Full credits retained")
    if completed == 8:
        achievements.append("[bold cyan]🎯 Full Clearance[/bold cyan] — All missions complete")
    if state["missions"].get("final_boss"):
        achievements.append("[bold red]👑 Vault Breaker[/bold red] — Defeated the Final Boss")

    if achievements:
        console.print(Panel(
            "\n".join(achievements),
            title="[bold yellow]// ACHIEVEMENTS //[/bold yellow]",
            border_style="yellow",
        ))

@cli.command()
def hint():
    """Display the next progressive hint for the current mission (-5 credits)."""
    state = load_state()
    cur = state["current_mission"]
    m_key = MISSION_KEYS[min(cur - 1, 7)]
    mission = MISSIONS[min(cur, 8)]
    hints = mission["hints"]

    # Track per-mission hint index via hints_used scoped to current mission
    used_key = f"hints_used_m{cur}"
    hint_idx = state.get(used_key, 0)

    if hint_idx >= len(hints):
        console.print(Panel(
            "[yellow]No more hints available for this mission.[/yellow]",
            title="[bold red]// HINT //[/bold red]",
            border_style="yellow",
        ))
        return

    if state["score"] <= 0:
        console.print("[bold red]No credits left to spend on hints![/bold red]")
        return

    # Deduct and record
    state["score"] = max(0, state["score"] - 5)
    state["hints_used"] = state.get("hints_used", 0) + 1
    state[used_key] = hint_idx + 1
    save_state(state)

    console.print(Panel(
        Text.from_markup(
            f"[bold yellow]Hint {hint_idx + 1} / {len(hints)}[/bold yellow]\n\n"
            + hints[hint_idx] +
            f"\n\n[dim]-5 credits deducted. Credits remaining: {state['score']}[/dim]"
        ),
        title=f"[bold red]// HINT: {mission['name']} //[/bold red]",
        border_style="yellow",
    ))

# ── Internal helpers ──────────────────────────────────────────────────────────
def _print_mission(num: int) -> None:
    m = MISSIONS[num]
    console.print(Panel(
        f"[bold yellow]🎯 OBJECTIVE:[/bold yellow] {m['objective']}\n\n"
        f"[bold cyan]📚 SKILL TESTED:[/bold cyan] {m['skill']}\n\n"
        f"[dim]Use [bold]cluster-heist hint[/bold] if you're stuck (-5 credits each).[/dim]",
        title=f"[bold red]// MISSION {num}: {m['name'].upper()} //[/bold red]",
        border_style="red",
    ))

def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)

def _fail(msg: str) -> None:
    console.print(f"[bold red][FAIL][/bold red] {msg}")

def _ok(msg: str) -> None:
    console.print(f"[bold green][PASS][/bold green] {msg}")

# ── Mission verification routines ─────────────────────────────────────────────

def _verify_mission_1() -> bool:
    """Sleeping Guard Pod: greeting-deployment must have all pods Running with a valid image."""
    ns = "cluster-heist"
    result = _run(["kubectl", "get", "deployment", "greeting-deployment", "-n", ns,
                   "-o", "jsonpath={.spec.template.spec.containers[0].image}"])
    if result.returncode != 0:
        _fail("greeting-deployment not found."); return False

    image = result.stdout.strip()
    if "nginxx" in image:
        _fail(f"Image is still '{image}' — fix the typo in the repository name."); return False

    # Check at least one pod is Running
    pods = _run(["kubectl", "get", "pods", "-n", ns, "-l", "component=greeting",
                 "-o", "jsonpath={.items[*].status.phase}"])
    phases = pods.stdout.strip().split()
    if not any(p == "Running" for p in phases):
        _fail(f"No greeting pod is Running yet (phases: {phases})."); return False

    _ok(f"greeting-deployment image is '{image}' and pod is Running.")
    return True


def _verify_mission_2() -> bool:
    """Door With the Wrong Label: greeting-service must have at least one ready endpoint."""
    ns = "cluster-heist"
    result = _run(["kubectl", "get", "endpoints", "greeting-service", "-n", ns,
                   "-o", "jsonpath={.subsets[0].addresses[0].ip}"])
    if result.returncode != 0:
        _fail("greeting-service not found."); return False
    if not result.stdout.strip():
        _fail("greeting-service has no endpoints. Fix the selector label (gaurd -> guard)."); return False

    _ok(f"greeting-service has active endpoint: {result.stdout.strip()}")
    return True


def _verify_mission_3() -> bool:
    """ConfigMap Combination Lock: heist-config must have correct VAULT_MODE and ROOM_NAME."""
    ns = "cluster-heist"
    passed = True
    for key, expected in [("VAULT_MODE", "training"), ("ROOM_NAME", "helm-lab")]:
        result = _run(["kubectl", "get", "configmap", "heist-config", "-n", ns,
                       "-o", f"jsonpath={{.data.{key}}}"])
        val = result.stdout.strip()
        if result.returncode != 0 or val != expected:
            _fail(f"heist-config[{key}] = '{val}', expected '{expected}'."); passed = False
        else:
            _ok(f"heist-config[{key}] = '{val}' ✔")
    return passed


def _verify_mission_4() -> bool:
    """Secret Vault Key: vault-key secret must exist with correct VAULT_TOKEN."""
    ns = "cluster-heist"
    import base64
    result = _run(["kubectl", "get", "secret", "vault-key", "-n", ns,
                   "-o", "jsonpath={.data.VAULT_TOKEN}"])
    if result.returncode != 0 or not result.stdout.strip():
        _fail("Secret 'vault-key' not found or missing VAULT_TOKEN key."); return False

    try:
        decoded = base64.b64decode(result.stdout.strip()).decode()
    except Exception:
        _fail("Could not decode VAULT_TOKEN from secret."); return False

    if decoded != "golden-yaml-42":
        _fail(f"VAULT_TOKEN = '{decoded}', expected 'golden-yaml-42'."); return False

    _ok("vault-key secret exists with correct VAULT_TOKEN ✔")
    return True


def _verify_mission_5() -> bool:
    """Sidecar Informant: both sidecar containers must have produced log output."""
    ns = "cluster-heist"
    # Find the sidecar pod (has both clue-log-1 and clue-log-2 containers)
    pods = _run(["kubectl", "get", "pods", "-n", ns,
                 "-o", "jsonpath={.items[*].metadata.name}"])
    if pods.returncode != 0:
        _fail("Could not list pods."); return False

    target_pod = None
    for pod in pods.stdout.split():
        containers = _run(["kubectl", "get", "pod", pod, "-n", ns,
                           "-o", "jsonpath={.spec.containers[*].name}"])
        names = containers.stdout.split()
        if "clue-log-1" in names and "clue-log-2" in names:
            target_pod = pod
            break

    if not target_pod:
        _fail("No pod with containers 'clue-log-1' and 'clue-log-2' found."); return False

    passed = True
    for container in ("clue-log-1", "clue-log-2"):
        logs = _run(["kubectl", "logs", target_pod, "-c", container, "-n", ns])
        if logs.returncode != 0 or not logs.stdout.strip():
            _fail(f"Container '{container}' has no log output."); passed = False
        else:
            _ok(f"Container '{container}' log output retrieved.")

    return passed


def _verify_mission_6() -> bool:
    """Redis Red Herring: redis-service exists on port 6379 and app env no longer uses localhost."""
    ns = "cluster-heist"

    # Check redis-service exists and exposes port 6379
    svc = _run(["kubectl", "get", "svc", "redis-service", "-n", ns,
                "-o", "jsonpath={.spec.ports[0].port}"])
    if svc.returncode != 0:
        _fail("Service 'redis-service' not found."); return False
    if svc.stdout.strip() != "6379":
        _fail(f"redis-service port is '{svc.stdout.strip()}', expected 6379."); return False
    _ok("redis-service is active on port 6379.")

    # Check no deployment env var still points to localhost for Redis
    envs = _run(["kubectl", "get", "deployments", "-n", ns,
                 "-o", "jsonpath={.items[*].spec.template.spec.containers[*].env[*].value}"])
    values = envs.stdout.split()
    if "localhost" in values:
        _fail("A deployment env var still references 'localhost'. Update it to 'redis-service'."); return False
    _ok("No deployment env vars reference 'localhost'.")
    return True


def _verify_mission_7() -> bool:
    """Helm Upgrade Gambit: replicaCount=3, image.tag=stable, vault.enabled=true."""
    result = _run(["helm", "get", "values", "cluster-heist",
                   "-n", "cluster-heist", "--output", "json"])
    if result.returncode != 0:
        _fail("Could not retrieve Helm values. Is the release deployed?"); return False

    try:
        values = json.loads(result.stdout)
    except json.JSONDecodeError:
        _fail("Helm values output is not valid JSON."); return False

    passed = True

    replica = values.get("replicaCount")
    if replica != 3:
        _fail(f"replicaCount is '{replica}', expected 3."); passed = False
    else:
        _ok("replicaCount = 3 ✔")

    tag = values.get("image", {}).get("tag")
    if tag != "stable":
        _fail(f"image.tag is '{tag}', expected 'stable'."); passed = False
    else:
        _ok("image.tag = stable ✔")

    vault_enabled = values.get("vault", {}).get("enabled")
    if vault_enabled is not True:
        _fail(f"vault.enabled is '{vault_enabled}', expected true."); passed = False
    else:
        _ok("vault.enabled = true ✔")

    return passed


def _verify_final_boss() -> bool:
    """Two-Service Betrayal: spin up a curl pod and hit http://cluster-heist.local/greeting."""
    ns = "cluster-heist"
    pod_name = "heist-verify-curl"
    target_url = "http://cluster-heist.local/greeting"
    expected = "VAULT OPENED"

    # Clean up any leftover probe pod
    _run(["kubectl", "delete", "pod", pod_name, "-n", ns, "--ignore-not-found"])

    console.print(f"[dim]Launching probe pod '{pod_name}'...[/dim]")
    launch = _run([
        "kubectl", "run", pod_name,
        "--image=curlimages/curl:8.7.1",
        "--restart=Never",
        "--rm", "-i",
        "-n", ns,
        "--command", "--",
        "curl", "-s", "--max-time", "10",
        "-H", "Host: cluster-heist.local",
        target_url,
    ])

    # Clean up regardless
    _run(["kubectl", "delete", "pod", pod_name, "-n", ns, "--ignore-not-found"])

    if launch.returncode != 0:
        _fail(f"Probe pod failed to execute. stderr: {launch.stderr.strip()}"); return False

    output = launch.stdout.strip()
    if expected not in output:
        _fail(f"Expected '{expected}' in response, got: '{output}'"); return False

    _ok(f"Received '{expected}' from {target_url} ✔")
    return True


# ── verify command ────────────────────────────────────────────────────────────
_VERIFIERS = {
    1: ("mission_1", _verify_mission_1),
    2: ("mission_2", _verify_mission_2),
    3: ("mission_3", _verify_mission_3),
    4: ("mission_4", _verify_mission_4),
    5: ("mission_5", _verify_mission_5),
    6: ("mission_6", _verify_mission_6),
    7: ("mission_7", _verify_mission_7),
    8: ("final_boss", _verify_final_boss),
}

@cli.command()
def verify():
    """Run the verification check for the current mission."""
    state = load_state()
    cur = state["current_mission"]

    if cur not in _VERIFIERS:
        console.print(
            f"[yellow]Mission {cur} has no automated verifier. "
            "Check your work manually and use 'cluster-heist status'.[/yellow]"
        )
        return

    m_key, verifier = _VERIFIERS[cur]
    mission_name = MISSIONS[cur]["name"]
    console.print(Panel(
        f"[bold cyan]Verifying:[/bold cyan] {mission_name}",
        title="[bold red]// VERIFICATION //[/bold red]",
        border_style="cyan",
    ))

    passed = verifier()

    if passed:
        state["missions"][m_key] = True
        state["current_mission"] = min(cur + 1, 8)
        save_state(state)
        console.print(Panel(
            f"[bold green]Mission {cur} complete! Moving to Mission {state['current_mission']}.[/bold green]",
            border_style="green",
        ))
        if state["current_mission"] <= 8:
            _print_mission(state["current_mission"])
    else:
        console.print(Panel(
            "[bold red]Verification failed. Fix the issues above and try again.[/bold red]",
            border_style="red",
        ))


if __name__ == "__main__":
    cli()
