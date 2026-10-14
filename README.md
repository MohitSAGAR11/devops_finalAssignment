# Inventory Manager — DevOps Capstone

Inventory Manager is a small warehouse stock-control app. It tracks products by SKU, records stock coming in and going out, flags items that have fallen below their reorder level, and shows what the stock on hand is worth.

The app is the vehicle; the point of the project is the delivery pipeline around it: from a commit on a laptop, through automated tests, container builds and a security gate, into a Helm release on AWS EKS provisioned with Terraform, monitored with Prometheus and Grafana.

```text
 git push ──► GitHub Actions ─┬─ pytest + frontend build + helm lint + terraform validate
                              ├─ docker build (backend, frontend), tag = commit SHA
                              ├─ Trivy scan ── HIGH/CRITICAL found? ──► pipeline fails, nothing pushed
                              ├─ push to GHCR
                              └─ helm upgrade --install ──► EKS (OIDC role, no stored AWS keys)

 Terraform ──► AWS: VPC (2 public + 2 private subnets, NAT) ──► EKS + managed node group

 EKS ─ ingress-nginx (LoadBalancer)
        ├── /      ──► frontend Service ──► React + Nginx pods (×2)
        └── /api   ──► backend Service  ──► FastAPI pods (×2, HPA 2→8) ──► PostgreSQL StatefulSet (EBS)
                                              ▲
                     Prometheus (ServiceMonitor scrapes /metrics) ──► Grafana dashboard
```

---

## Features

| Area | What it does |
|---|---|
| Products | Create, edit, delete products with SKU, category, supplier, unit price and reorder level |
| Stock movements | One-click **receive (+)** / **ship (−)**; stock can never go below zero |
| Reorder alerts | Products at or below their reorder level are flagged *Low stock*, zero is *Out of stock* |
| Dashboard | Product count, units on hand, items needing reorder, total inventory value (₹) |
| Search & filter | By name / SKU / supplier, by category, or "needs reorder only" |
| Responsive UI | Table on desktop, stacked cards on phones |

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, served by unprivileged Nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic 2 |
| Database | PostgreSQL 16, schema managed by Alembic migrations |
| Tests | Pytest + FastAPI TestClient on an isolated SQLite database |
| Containers | Docker (multi-stage frontend, non-root users), Docker Compose |
| CI/CD | GitHub Actions → GitHub Container Registry |
| Security | Trivy image scanning; SHA-pinned actions; OIDC instead of AWS keys |
| Infrastructure | Terraform: AWS VPC + EKS + EBS CSI driver |
| Orchestration | Kubernetes, Helm chart, ingress-nginx, HPA, metrics-server |
| Observability | Prometheus (kube-prometheus-stack), Grafana, `prometheus-fastapi-instrumentator` |

## Repository layout

```text
.
├── backend/                  FastAPI service
│   ├── app/                  main.py (routes), models.py, schemas.py, db.py, config.py
│   ├── alembic/versions/     0001 create products, 0002 add sku/price/reorder level
│   ├── tests/                pytest suite (19 tests) + conftest.py
│   └── Dockerfile            python:3.12-slim, runs as uid 10001
├── frontend/                 React app
│   ├── src/                  App.jsx, ProductForm.jsx, api.js, styles.css
│   ├── nginx/                Nginx config template (BACKEND_URL injected at start)
│   └── Dockerfile            node build stage → nginx-unprivileged runtime (uid 101)
├── docker-compose.yml        postgres + backend + frontend
├── .github/workflows/        ci-cd.yml
├── terraform/                VPC, EKS, EBS CSI IRSA, GitHub OIDC deploy role
├── helm/inventory/           Helm chart (values.yaml, values-dev.yaml, values-prod.yaml)
├── k8s/                      namespaces, default gp3 StorageClass for EKS
├── monitoring/               prometheus-values.yaml, grafana-values.yaml
├── scripts/                  bootstrap-cluster.sh, load-test.sh
└── troubleshooting/          deliberately broken manifests for debugging practice
```

---

## REST API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness: process is up |
| GET | `/ready` | Readiness: database reachable |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/products` | List products (newest first); `?category=` filter |
| GET | `/api/products/stats` | Totals, low stock, out of stock, inventory value |
| GET | `/api/products/{id}` | One product |
| POST | `/api/products` | Create (409 on duplicate SKU, 422 on invalid input) |
| PUT | `/api/products/{id}` | Partial update |
| POST | `/api/products/{id}/adjust` | `{"delta": 10}` receive / `{"delta": -3}` ship |
| DELETE | `/api/products/{id}` | Delete |

Interactive docs: `http://localhost:8000/docs`.

---

## Run locally

### Docker Compose (recommended)

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | Inventory Manager UI |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/metrics | Prometheus metrics |

Postgres is exposed on `localhost:5433` (user/password/db `inventory`). Stop with `docker compose down` (add `-v` to wipe the database).

### Without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # points at Postgres on localhost:5433
alembic upgrade head
uvicorn app.main:app --reload --port 8000

cd ../frontend
npm ci
npm run dev                                             # http://localhost:5173, proxies /api to :8000
```

---

## Testing

```bash
cd backend
pytest -v
```

19 tests cover health/readiness/metrics, create/list/get/update/delete, input validation, duplicate SKUs, stock adjustments (including refusing to go negative) and the stats calculation. `tests/conftest.py` points `DATABASE_URL` at a throwaway SQLite file and recreates the schema for every test, so the suite never touches the real Postgres database.

---

## CI/CD — `.github/workflows/ci-cd.yml`

Runs on every push and pull request to `main`.

| Job | Steps |
|---|---|
| `test` | Install deps → `pytest -v` (any failure stops the pipeline) → `npm ci && npm run build` |
| `lint-infra` | `helm lint` (dev + prod values), `terraform fmt -check`, `terraform validate` |
| `build-scan-push` | Build both images tagged `ghcr.io/<owner>/inventory-{backend,frontend}:<commit-sha>` → Trivy scan both → push to GHCR (push to `main` only) |
| `deploy` | Assume AWS role via GitHub OIDC → `aws eks update-kubeconfig` → `helm upgrade --install` with the new SHA tags → print rollout |

Images are tagged with the commit SHA, never `latest`, so every running pod can be traced back to the exact commit that produced it, and rolling back is just redeploying an older SHA.

### One-time GitHub setup

1. **Settings → Secrets and variables → Actions**
   - Secret `AWS_DEPLOY_ROLE_ARN`: from `terraform output github_deploy_role_arn`
   - Secret `POSTGRES_PASSWORD`: any strong password (keep it the same between deploys)
   - Variable `EKS_CLUSTER_NAME`: `inventory-eks` (delete it after `terraform destroy` so the deploy job is skipped)
   - Variable `AWS_REGION`: `ap-south-1` (optional, this is the default)
2. After the first successful push, open each package under **Your profile → Packages** (`inventory-backend`, `inventory-frontend`) and set visibility to **Public** so EKS can pull without credentials. (Alternatively create a `ghcr-pull` docker-registry secret and set `imagePullSecrets`.)

---

## DevSecOps — Trivy

Both images are scanned by Trivy in the pipeline before they are pushed. The scan looks at OS packages in the base image (Debian for the backend, Alpine for the frontend) and at application libraries (Python packages, npm packages left in the image). The job fails if any **HIGH** or **CRITICAL** vulnerability with an available fix is found (`exit-code: 1`, `ignore-unfixed: true`), so a vulnerable image never reaches the registry or the cluster.

**What the scan actually caught:** the first scan of this project failed. The backend shipped `starlette 0.41.3` (pulled in by an older FastAPI), which has **CVE-2025-62727**. Starlette merged overlapping HTTP `Range` headers inefficiently, so a single request with a crafted `Range` header could burn CPU and deny service to other users. The fix is in Starlette 0.49.1. The frontend's `nginx:1.27-alpine` base also carried fixable HIGH CVEs in `libxml2`, `musl`, `zlib` and `nghttp2`. The fix was upgrading FastAPI/Starlette, moving to `nginx-unprivileged:1.30-alpine` and running `apk upgrade` at build time. Both images now scan clean (0 HIGH/CRITICAL).

**Supply-chain hardening:** every GitHub Action is pinned to a full commit SHA. In March 2026 attackers force-pushed malicious code over most `aquasecurity/trivy-action` version tags (CVE-2026-33634); workflows referencing a tag ran the attacker's code, while a SHA can't be rewritten.

---

## Infrastructure — Terraform (AWS)

See [`terraform/README.md`](terraform/README.md) for details.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
$(terraform output -raw configure_kubectl)
```

Creates a VPC (`10.30.0.0/16`) with 2 public and 2 private subnets across two AZs, one NAT gateway, an EKS 1.34 cluster with a 2-node `m7i-flex.large` managed node group, the EBS CSI driver (so Postgres gets a persistent volume), and an IAM role that GitHub Actions can assume via OIDC.

> **Always run `terraform destroy` after the demo.** EKS, the NAT gateway and the load balancer bill by the hour.

---

## Kubernetes + Helm

```bash
# once per cluster: namespaces, gp3 StorageClass, ingress-nginx, metrics-server, Prometheus + Grafana
./scripts/bootstrap-cluster.sh

# deploy (CI does this automatically on every push to main)
helm upgrade --install inventory ./helm/inventory \
  -n inventory --create-namespace \
  -f helm/inventory/values-prod.yaml \
  --set backend.image.tag=<commit-sha> --set frontend.image.tag=<commit-sha> \
  --set-string postgres.password=<password>

kubectl get pods -n inventory
kubectl get svc -n inventory
kubectl get ingress,hpa -n inventory
helm list -n inventory
```

The chart (`helm/inventory`) deploys:

| Resource | Notes |
|---|---|
| `inventory-backend` Deployment | 2+ replicas, `/ready` readiness + `/health` liveness probes, non-root, read-only root FS, waits for Postgres before migrating |
| `inventory-frontend` Deployment | 2 replicas, non-root Nginx on 8080 |
| `inventory-postgres` StatefulSet | 1 replica, PVC on gp3 EBS, credentials from a Secret |
| ClusterIP Services | backend :8000, frontend :80, postgres :5432 |
| Ingress | `/` → frontend, `/api` → backend (class `nginx`) |
| HorizontalPodAutoscaler | backend, 60 % CPU target, 2–8 replicas |
| ServiceMonitor + dashboard ConfigMap | picked up by Prometheus and Grafana automatically |

Every backend pod runs `alembic upgrade head` before starting. A Postgres advisory lock in `alembic/env.py` makes concurrent pods migrate one at a time instead of racing.

Open the app at the ingress load balancer hostname:

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

For a local cluster (minikube/kind with ingress-nginx) use `-f helm/inventory/values-dev.yaml` and map `inventory.local` in your hosts file.

---

## Observability — Prometheus + Grafana

The backend exposes request count, latency histograms and sizes at `/metrics`. A ServiceMonitor tells Prometheus to scrape it every 15 s, and the Grafana sidecar loads the bundled **Inventory Manager — API** dashboard:

| Panel | Query idea |
|---|---|
| Backend pods up | `sum(up{app="inventory-manager"})` |
| Requests / sec and by endpoint | `rate(http_requests_total[1m])` |
| 5xx error rate | 5xx requests ÷ all requests |
| p95 latency (overall and per endpoint) | `histogram_quantile(0.95, …)` |
| Responses by status class | 2xx / 4xx / 5xx |
| Backend CPU per pod | the signal the HPA scales on |

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090   # Status → Targets
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80        # admin / your password
URL=http://<ingress-host> ./scripts/load-test.sh                                    # generate traffic
kubectl get hpa -n inventory -w                                                     # watch it scale
```

---

## Troubleshooting lab

| Manifest | Symptom | How to diagnose |
|---|---|---|
| `troubleshooting/broken-image.yaml` | Pod stuck in `ImagePullBackOff` | `kubectl describe pod` → events show the tag doesn't exist |
| `troubleshooting/broken-service.yaml` | Service has no endpoints | `kubectl get endpoints` is empty; compare its selector with `kubectl get pods --show-labels` |

---

## Demo script

1. Open the app, add a product, receive/ship stock, watch the KPIs change.
2. Show Swagger at `/docs` and the `products` table in Postgres.
3. Change something visible (e.g. the subtitle in `frontend/src/App.jsx`), commit and push.
4. Watch GitHub Actions: tests → build → Trivy → push → Helm deploy.
5. Show the new SHA-tagged images in GHCR.
6. `kubectl get pods -n inventory -w`: pods roll to the new image; refresh the browser to see the change.
7. `helm list -n inventory`, `helm history inventory -n inventory` (and `helm rollback` if wanted).
8. Run the load test, show Grafana panels moving and `kubectl get hpa` scaling.
9. Apply a troubleshooting manifest and debug it live.
10. `terraform destroy`.
