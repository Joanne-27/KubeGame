# SKILLS.md — Cluster Heist: The Helm Job

> Instructor reference: maps each heist mission to the professional Kubernetes competency it develops and the real-world debugging workflow it exercises.

---

## Competency Map

| Mission | Codename | Core K8s Skill | Debugging Workflow |
|---------|----------|----------------|--------------------|
| 1 | The Sleeping Guard Pod | Pod lifecycle & image resolution | `kubectl get pods` → `kubectl describe pod` → identify `ImagePullBackOff` → patch image |
| 2 | The Door With the Wrong Label | Service selectors & endpoint binding | `kubectl get endpoints` → `kubectl get svc -o yaml` → compare selector vs pod labels → `kubectl edit svc` |
| 3 | The ConfigMap Combination Lock | ConfigMaps & environment variable injection | `kubectl get configmap` → inspect `envFrom` / `env` blocks → create/edit ConfigMap → rollout restart |
| 4 | The Secret Vault Key | Kubernetes Secrets & `secretKeyRef` | `kubectl get secrets` → `kubectl create secret generic` → wire `secretKeyRef` in deployment → verify env |
| 5 | The Sidecar Informant | Multi-container pods & per-container log streaming | `kubectl get pods` → identify multi-container pod → `kubectl logs <pod> -c <container>` per sidecar |
| 6 | The Redis Red Herring | Cluster-internal DNS & service discovery | `kubectl describe deployment` → find hardcoded `localhost` → replace with `<service-name>` DNS → verify endpoints |
| 7 | The Helm Upgrade Gambit | Helm chart architecture, `values.yaml` overrides, `helm upgrade` | `helm show values` → edit `values.yaml` → `helm upgrade` → `helm get values` → `kubectl get pods` |
| ★ | The Two-Service Betrayal | Ingress rules, path routing & cross-service DNS | `kubectl get ingress` → inspect inter-service env vars → replace IPs with service DNS names → curl Ingress host |

---

## Skill Deep-Dives

### Mission 1 — Pod Statuses & Diagnostics

**What students learn:**  
Kubernetes pulls container images by name. A typo in `image.repository` causes `ImagePullBackOff` — the kubelet cannot fetch the image and backs off with exponential retry delays.

**Key commands:**
```bash
kubectl get pods -n cluster-heist
kubectl describe pod <pod-name> -n cluster-heist   # read Events section
kubectl set image deployment/greeting-deployment greeting=nginx:stable -n cluster-heist
```

**Professional relevance:** Image pull failures are among the most common production incidents. Rapid triage via `describe` is a day-one on-call skill.

---

### Mission 2 — Services, Selectors & Endpoints

**What students learn:**  
A Kubernetes Service routes traffic by matching its `selector` against pod `labels`. A single character typo (`gaurd` vs `guard`) produces zero endpoints — the service exists but is completely deaf.

**Key commands:**
```bash
kubectl get endpoints -n cluster-heist
kubectl get svc greeting-service -n cluster-heist -o yaml
kubectl get pods --show-labels -n cluster-heist
kubectl edit svc greeting-service -n cluster-heist
```

**Professional relevance:** Selector mismatches are a silent failure mode — the service returns no error, traffic simply drops. Endpoint inspection is the definitive diagnostic.

---

### Mission 3 — ConfigMaps & Environment Injection

**What students learn:**  
ConfigMaps decouple configuration from container images. Values can be injected as environment variables via `envFrom.configMapRef` (bulk) or `env[].valueFrom.configMapKeyRef` (individual keys).

**Key commands:**
```bash
kubectl get configmap heist-config -n cluster-heist -o yaml
kubectl edit configmap heist-config -n cluster-heist
kubectl rollout restart deployment/greeting-deployment -n cluster-heist
```

**Professional relevance:** Externalising config is a 12-factor app principle. Students learn to distinguish config that belongs in a ConfigMap vs a Secret.

---

### Mission 4 — Kubernetes Secrets

**What students learn:**  
Secrets store sensitive data (tokens, passwords, keys) base64-encoded and separate from application code. They are referenced in pods via `secretKeyRef`, keeping plaintext values out of deployment manifests.

**Key commands:**
```bash
kubectl get secrets -n cluster-heist
kubectl create secret generic vault-key \
  --from-literal=VAULT_TOKEN=golden-yaml-42 -n cluster-heist
kubectl describe secret vault-key -n cluster-heist
```

**Professional relevance:** Hardcoding credentials in environment variables or ConfigMaps is a security anti-pattern. Secrets enforce separation of sensitive data.

---

### Mission 5 — Multi-Container Pods & Log Streaming

**What students learn:**  
Pods can run multiple containers sharing the same network namespace and volumes. Each container has independent logs accessible via `-c <container-name>`. Sidecars are used for logging agents, proxies, and data collectors.

**Key commands:**
```bash
kubectl get pods -n cluster-heist
kubectl describe pod sidecar-informant -n cluster-heist   # lists all containers
kubectl logs sidecar-informant -c clue-log-1 -n cluster-heist
kubectl logs sidecar-informant -c clue-log-2 -n cluster-heist
```

**Professional relevance:** Sidecar patterns (Envoy, Fluentd, Vault Agent) are ubiquitous in production. Knowing how to target individual containers is essential for debugging service meshes and log pipelines.

---

### Mission 6 — Cluster DNS & Service Discovery

**What students learn:**  
Kubernetes provides automatic DNS for every Service: `<service-name>.<namespace>.svc.cluster.local` (or simply `<service-name>` within the same namespace). Hardcoding `localhost` breaks inter-pod communication entirely.

**Key commands:**
```bash
kubectl describe deployment message-deployment -n cluster-heist
kubectl set env deployment/message-deployment REDIS_HOST=redis-service -n cluster-heist
kubectl get endpoints redis-service -n cluster-heist
```

**Professional relevance:** Service discovery via DNS is the standard pattern for microservice communication in Kubernetes. IP-based addressing is fragile; pod IPs change on every restart.

---

### Mission 7 — Helm Package Management

**What students learn:**  
Helm packages Kubernetes manifests into reusable charts. `values.yaml` provides defaults that operators override at install/upgrade time. `helm upgrade` applies changes without deleting and recreating the release.

**Key commands:**
```bash
helm show values charts/cluster-heist
helm upgrade cluster-heist charts/cluster-heist \
  --namespace cluster-heist \
  --set replicaCount=3 \
  --set greeting.image.tag=stable \
  --set vault.enabled=true
helm get values cluster-heist -n cluster-heist
helm history cluster-heist -n cluster-heist
```

**Professional relevance:** Helm is the de-facto Kubernetes package manager. Understanding chart structure, values overrides, and release history is required for any production deployment workflow.

---

### Final Boss — Ingress & Cross-Service DNS

**What students learn:**  
An Ingress controller (nginx) routes external HTTP traffic to internal Services by hostname and path. Inter-service communication must use Kubernetes DNS names, not external hostnames or IPs, to avoid routing loops and latency.

**Key commands:**
```bash
kubectl get ingress -n cluster-heist
kubectl describe ingress heist-ingress -n cluster-heist
kubectl set env deployment/greeting-deployment \
  MESSAGE_SERVICE_URL=http://message-service:8080/message -n cluster-heist
curl http://cluster-heist.local/greeting
```

**Professional relevance:** Ingress is the standard entry point for HTTP workloads. Cross-service DNS correctness is critical in microservice architectures — a single wrong URL can silently break an entire request chain.

---

## Scoring & Rank Thresholds

| Credits | Rank | Interpretation |
|---------|------|----------------|
| 90–100 | Cluster Heist Legend | Solved all missions with zero or minimal hints |
| 75–89 | Helm Bender | Strong independent problem-solving |
| 60–74 | DNS Diplomat | Competent with occasional guidance |
| 40–59 | YAML Survivor | Completed with significant hint usage |
| < 40 | CrashLoop Apprentice | Needs further practice with core concepts |
