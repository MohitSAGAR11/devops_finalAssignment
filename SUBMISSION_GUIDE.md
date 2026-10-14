# Submission Guide — Run Everything & Capture Every Screenshot

Follow this file **top to bottom, in order**. Each part says what to run, what you should see, and when to take a screenshot (marked **📸**).

All commands are for **Windows**. Use **PowerShell** unless a step says **Git Bash**.

> **PowerShell gotcha:** always type `curl.exe`, not `curl`. In Windows PowerShell, `curl` is a different command (`Invoke-WebRequest`) with different output.

---

## 0. The screenshots you need (checklist)

Create a folder for them first, for example `C:\Users\Mohit-PC\capstone-screenshots\`, and use these file names so nothing gets missed.

| #  | File name                         | What it shows                                                  | Rubric | Part |
| -- | --------------------------------- | -------------------------------------------------------------- | ------ | ---- |
| 1  | `01-compose-up.png`             | Terminal:`docker compose up --build` running, all 3 services | M1, M4 | A    |
| 2  | `02-app-localhost-3000.png`     | Browser: app at`http://localhost:3000` with products         | M1, M4 | A    |
| 3  | `03-swagger-docs.png`           | Browser:`http://localhost:8000/docs`                         | M1     | A    |
| 4  | `04-postgres-table.png`         | Terminal: rows from the`products` table                      | M1     | A    |
| 5  | `05-pytest-pass.png`            | Terminal:`pytest -v`, 19 passed                              | M2     | B    |
| 6  | `06-commit-history.png`         | GitHub commits page (15+ commits)                              | M3     | C    |
| 7  | `07-actions-green.png`          | GitHub Actions run, all jobs green                             | M5     | D    |
| 8  | `08-trivy-output.png`           | Trivy scan step log                                            | M6     | D    |
| 9  | `09-ghcr-packages.png`          | GHCR package page with SHA tags                                | M5     | D    |
| 10 | `10-terraform-plan.png`         | Terminal:`terraform plan` summary                            | M7     | E    |
| 11 | `11-aws-vpc.png`                | AWS console: VPC + subnets in ap-south-1                       | M7     | E    |
| 12 | `12-aws-eks.png`                | AWS console: EKS cluster + node group                          | M7     | E    |
| 13 | `13-kubectl-pods.png`           | `kubectl get pods -n inventory`, all Running                 | M8     | G    |
| 14 | `14-kubectl-svc.png`            | `kubectl get svc -n inventory`                               | M8     | G    |
| 15 | `15-helm-list.png`              | `helm list -n inventory`                                     | M8     | G    |
| 16 | `16-app-via-ingress.png`        | Browser: app at the load balancer address                      | M8     | G    |
| 17 | `17-metrics-curl.png`           | Terminal:`curl.exe .../metrics` output                       | M9     | H    |
| 18 | `18-prometheus-targets.png`     | Prometheus Targets page, backend**UP**                   | M9     | H    |
| 19 | `19-grafana-dashboard.png`      | Grafana dashboard with live panels                             | M9     | H    |
| 20 | `20-hpa.png` *(nice to have)* | `kubectl get hpa -n inventory`                               | M8     | H    |
| 21 | `21-terraform-destroy.png`      | Terminal:`Destroy complete!`                                 | M7     | K    |

You also need:

- the **GitHub repository URL**
- the **GitHub Actions run URL** of a green run (copy it from the browser address bar)
- the **Trivy explanation text** (ready to paste in Part D)
- a **live demo** or screen recording (script in Part I)

---

## 1. One-time setup: install the tools

Open **PowerShell** and run each line. Close and reopen PowerShell afterwards so the new commands are found.

```powershell
winget install -e --id Amazon.AWSCLI
winget install -e --id Hashicorp.Terraform
winget install -e --id Helm.Helm
```

Already installed on this PC: Docker Desktop, Git (with Git Bash), Node.js, Python, kubectl.

**Check that everything works.** Each command should print a version, not an error:

```powershell
docker --version
git --version
node --version
python --version
kubectl version --client
aws --version
terraform version
helm version
```

**Start Docker Desktop** from the Start menu and wait until the whale icon in the taskbar says *Docker Desktop is running*.

---

## PART A — Run the app locally with Docker Compose (M1, M4)

### A1. Start the stack

```powershell
cd C:\Users\Mohit-PC\devOps_capstone
docker compose down -v
docker compose up --build
```

The first time, this takes a few minutes. It's ready when the log stops scrolling and shows lines like:

```
backend-1   | INFO  [alembic.runtime.migration] Running upgrade 0001_create_products -> 0002_add_sku_price_reorder
backend-1   | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**📸 #1 `01-compose-up.png`:** the terminal showing the build finished and the `postgres-1`, `backend-1` and `frontend-1` log lines.

Leave this window running. Open a **second PowerShell window** for everything else.

### A2. Add some products

Open **http://localhost:3000** in your browser.

Click **+ Add product** and create 4 or 5 products. Use a mix so the badges look interesting:

| SKU      | Name                | Category    | Supplier  | Qty | Reorder level | Price |
| -------- | ------------------- | ----------- | --------- | --- | ------------- | ----- |
| KB-001   | Mechanical Keyboard | Peripherals | KeyCo     | 25  | 5             | 2499  |
| CB-USB-C | USB-C Cable 1m      | Cables      | WireWorks | 4   | 20            | 299   |
| MN-27    | 27in 4K Monitor     | Displays    | ViewTech  | 0   | 3             | 18999 |
| MS-WL    | Wireless Mouse      | Peripherals | KeyCo     | 60  | 15            | 899   |

Then try the features: press **+** / **−** on a stock number, use **Edit**, type in the search box, pick a category, tick **Needs reorder only**.

**📸 #2 `02-app-localhost-3000.png`:** the full browser window showing the KPI cards and the product table, with the address bar visible.

### A3. API docs

Open **http://localhost:8000/docs**. Expand **GET /api/products** → **Try it out** → **Execute**.

**📸 #3 `03-swagger-docs.png`:** Swagger showing the endpoint list (GET, POST, PUT, DELETE) and a response.

### A4. Check health and metrics

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:3000/api/products/stats
curl.exe -s http://localhost:8000/metrics | Select-Object -First 25
```

The first command should print `{"status":"UP"}`. The third should print lines starting with `# HELP` and `http_requests_total{...}`.

### A5. Show the database table

```powershell
docker compose exec postgres psql -U inventory -c "SELECT id, sku, name, quantity, reorder_level, unit_price FROM products;"
docker compose exec postgres psql -U inventory -c "SELECT * FROM alembic_version;"
```

**📸 #4 `04-postgres-table.png`:** both outputs. The second one proves Alembic manages the schema (`0002_add_sku_price_reorder`).

### A6. Check that both containers run as non-root (M4)

```powershell
docker compose exec backend id
docker compose exec frontend id
```

Expected: `uid=10001(appuser)` and `uid=101(nginx)`. You can add this to screenshot #1 or #4.

---

## PART B — Run the tests (M2)

```powershell
cd C:\Users\Mohit-PC\devOps_capstone\backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -v
```

(If `.venv` already exists, skip the `python -m venv .venv` line.)

Expected: 19 test names, each marked `PASSED`, ending with `19 passed`.

**📸 #5 `05-pytest-pass.png`:** the whole list plus the green `19 passed` line.

> **If asked:** the tests don't use the real Postgres. `tests/conftest.py` sets `DATABASE_URL=sqlite:///./test.db` and rebuilds the tables before every test.

---

## PART C — Put the code on GitHub (M3)

### C1. Create the repository

1. Go to https://github.com/new
2. Repository name: **`devops_finalAssignment`**. Use exactly this name; Terraform expects it. If you choose another name, change `github_repository` in Part E2.
3. Visibility: **Public**
4. **Don't** tick "Add a README", ".gitignore" or "license". The repo must be empty.
5. Click **Create repository**.

### C2. Push

```powershell
cd C:\Users\Mohit-PC\devOps_capstone
git status
git remote add origin https://github.com/MohitSAGAR11/devops_finalAssignment.git
git push -u origin main
```

`git status` should say *nothing to commit, working tree clean*, apart from this guide file, which you can commit or keep private.

### C3. Commit history

Open `https://github.com/MohitSAGAR11/devops_finalAssignment/commits/main`.

**📸 #6 `06-commit-history.png`:** the list of commits with their descriptive messages (15+).

---

## PART D — CI/CD pipeline, Trivy, GHCR (M5, M6)

The push in C2 already started the pipeline. The **deploy** job is skipped for now; that's expected, because the AWS cluster doesn't exist yet.

### D1. Watch the pipeline

1. In the repo, click the **Actions** tab.
2. Click the run at the top (*Inventory Manager CI/CD*).
3. Wait until **Test backend & build frontend**, **Lint Helm chart & Terraform** and **Build, scan & push images** all have green ticks (about 5–8 minutes). **Deploy to EKS with Helm** shows as skipped (grey).

**📸 #7 `07-actions-green.png`:** the run summary graph with all the green jobs. **Copy the URL** from the address bar; that's your "GitHub Actions run URL".

### D2. Trivy output

Click **Build, scan & push images**, then expand **Trivy scan — backend** (and **— frontend**).

**📸 #8 `08-trivy-output.png`:** the scan table. A clean result shows the report summary with `0` findings.

**Trivy explanation to paste into the submission form:**

> Trivy scanned both container images in the CI pipeline before they were pushed: the OS packages of the base images (Debian for the backend, Alpine for the frontend) and the Python/npm libraries inside them. The pipeline fails on any HIGH or CRITICAL vulnerability that has a fix available. The first scan of this project failed: the backend contained starlette 0.41.3 with CVE-2025-62727, where a crafted HTTP `Range` header could make the server burn CPU and deny service to other users, and the nginx 1.27 base image had fixable HIGH CVEs in libxml2, musl and zlib. After upgrading FastAPI/Starlette and moving to nginx-unprivileged 1.30 with `apk upgrade`, both images scan clean with 0 HIGH/CRITICAL findings, which means no known fixable high-risk vulnerabilities are shipped.

### D3. GHCR packages, and make them public

1. Open `https://github.com/MohitSAGAR11?tab=packages`. You'll see **inventory-backend** and **inventory-frontend**.
2. Click **inventory-backend**. The page lists a tag that is a long commit SHA (for example `ed4c1a9…`).

**📸 #9 `09-ghcr-packages.png`:** the package page showing the SHA tag. Take one for each package, or one showing both in the packages list plus one detail page.

3. **Make both packages public.** EKS has no GitHub login, so it can only pull public images:
   - On the package page: **Package settings** (right side) → scroll to **Danger Zone** → **Change visibility** → **Public** → type the package name → confirm.
   - Repeat for **inventory-frontend**.

---

## PART E — Terraform: create the AWS infrastructure (M7)

> **💸 Cost:** from `terraform apply` until `terraform destroy`, AWS charges roughly **$0.30–0.35 per hour** (≈ $8/day): EKS control plane, NAT gateway, 2 × m7i-flex.large, a load balancer. Do Parts E → K in one sitting if you can, then destroy.

### E1. AWS credentials

1. Log in to the AWS console → **IAM** → **Users** → **Create user** (e.g. `capstone-admin`) → **Attach policies directly** → `AdministratorAccess` → create.
2. Open the user → **Security credentials** → **Create access key** → *Command Line Interface* → copy the **Access key ID** and **Secret access key**.
3. In PowerShell:

```powershell
aws configure
#  AWS Access Key ID:      <paste>
#  AWS Secret Access Key:  <paste>
#  Default region name:    ap-south-1
#  Default output format:  json

aws sts get-caller-identity
```

The last command should print your account ID. These keys live only on your PC (`C:\Users\Mohit-PC\.aws\`). **Never** put them in the repo.

*(Recommended: AWS console → Billing → Budgets → create a $10 monthly budget alert.)*

### E2. Configure the variables

```powershell
cd C:\Users\Mohit-PC\devOps_capstone\terraform
copy terraform.tfvars.example terraform.tfvars
notepad terraform.tfvars
```

Check this line matches your GitHub repo **exactly** (capital letters matter):

```hcl
github_repository = "MohitSAGAR11/devops_finalAssignment"
```

Save and close. `terraform.tfvars` is git-ignored, so it is never committed.

### E3. init + plan

```powershell
terraform init
terraform validate
terraform plan
```

`init` ends with *Terraform has been successfully initialized!*, `validate` prints *Success!*, and `plan` lists resources and ends with something like **`Plan: 60+ to add, 0 to change, 0 to destroy.`**

**📸 #10 `10-terraform-plan.png`:** the end of the plan output with the `Plan: … to add` line (scroll up a little to include some `+ resource` lines).

> If `plan` fails with **`EntityAlreadyExists` … OpenIDConnectProvider** (only at apply time), your account already has a GitHub OIDC provider. Set `create_github_oidc_provider = false` in `terraform.tfvars` and run again.

### E4. apply

```powershell
terraform apply
```

Type **`yes`** when asked. This takes **15–20 minutes**. When it finishes you'll see `Apply complete!` and the outputs. **Copy `github_deploy_role_arn`**; you need it in Part F.

```powershell
terraform output
```

### E5. AWS console screenshots

Make sure the region at the top right of the console is **Asia Pacific (Mumbai) ap-south-1**.

- **VPC** → *Your VPCs* → `inventory-eks-vpc`. Then click **Subnets** and filter by that VPC to show 4 subnets (2 `public`, 2 `private`).

  **📸 #11 `11-aws-vpc.png`:** the VPC and its subnets.
- **EKS** → *Clusters* → `inventory-eks` (status **Active**). Then the **Compute** tab shows the node group `main` with 2 nodes.

  **📸 #12 `12-aws-eks.png`:** the cluster page (Active) and/or the Compute tab with the node group.

### E6. Connect kubectl to the cluster

```powershell
aws eks update-kubeconfig --region ap-south-1 --name inventory-eks
kubectl get nodes
```

Expected: 2 nodes with `STATUS Ready`.

---

## PART F — Prepare the cluster and connect GitHub to it

### F1. Install the cluster add-ons (Git Bash)

Open **Git Bash** (Start menu → *Git Bash*):

```bash
cd /c/Users/Mohit-PC/devOps_capstone
export GRAFANA_ADMIN_PASSWORD='ChooseAGrafanaPassword123'
./scripts/bootstrap-cluster.sh
```

This takes 5–10 minutes. It installs the namespaces, the gp3 storage class, ingress-nginx (which creates the AWS load balancer), metrics-server (for the HPA), and Prometheus + Grafana.

The last line printed is the **load balancer address**, something like
`a1b2c3d4e5…elb.ap-south-1.amazonaws.com`. **Copy it.** If it's empty, wait a minute and run:

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

and copy the `EXTERNAL-IP` column.

### F2. Add GitHub secrets and variables

In the repo: **Settings → Secrets and variables → Actions**.

**Secrets** tab → **New repository secret**, twice:

| Name                    | Value                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------- |
| `AWS_DEPLOY_ROLE_ARN` | the`github_deploy_role_arn` from `terraform output` (starts with `arn:aws:iam::`) |
| `POSTGRES_PASSWORD`   | any strong password;**keep it the same from now on**                              |

**Variables** tab → **New repository variable**, twice:

| Name                 | Value             |
| -------------------- | ----------------- |
| `EKS_CLUSTER_NAME` | `inventory-eks` |
| `AWS_REGION`       | `ap-south-1`    |

### F3. Run the pipeline again, now with deploy

**Actions** tab → **Inventory Manager CI/CD** (left side) → **Run workflow** → branch `main` → **Run workflow**.

Wait for all 4 jobs, including **Deploy to EKS with Helm**, to go green (about 10–15 minutes the first time, because Postgres needs a disk). The last step, **Show rollout**, prints the pods and the image tags.

> This is a better run for screenshot #7 because the deploy job is green too. Retake it and use this run's URL.

---

## PART G — Kubernetes + Helm screenshots (M8)

```powershell
kubectl get pods -n inventory
```

Expected: 2 × `inventory-backend-…`, 2 × `inventory-frontend-…` and `inventory-postgres-0`, all `Running` with `READY 1/1`.

**📸 #13 `13-kubectl-pods.png`**

```powershell
kubectl get svc -n inventory
```

Expected: `inventory-backend`, `inventory-frontend`, `inventory-postgres`, all `TYPE ClusterIP`.

**📸 #14 `14-kubectl-svc.png`**

```powershell
helm list -n inventory
```

Expected: release `inventory`, `STATUS deployed`, `CHART inventory-1.0.0`.

**📸 #15 `15-helm-list.png`**

Extra proof (optional, can go in the same screenshots):

```powershell
kubectl get ingress -n inventory
kubectl get deploy -n inventory -o wide
```

The second shows the image tag is the Git commit SHA.

### The app through the Ingress

Open `http://<load-balancer-address>` (from F1) in your browser. A brand-new AWS load balancer can take **3–5 minutes** before it responds. The database in the cluster is empty, so add 3–4 products again.

**📸 #16 `16-app-via-ingress.png`:** the app with the long `…elb.ap-south-1.amazonaws.com` address visible in the address bar.

---

## PART H — Monitoring screenshots (M9)

### H1. Generate some traffic first (Git Bash)

```bash
cd /c/Users/Mohit-PC/devOps_capstone
URL=http://<load-balancer-address> REQUESTS=3000 ./scripts/load-test.sh
```

### H2. `/metrics` from the backend running in Kubernetes (PowerShell)

```powershell
kubectl port-forward -n inventory svc/inventory-backend 8000:8000
```

Leave that running. In another PowerShell window:

```powershell
curl.exe -s http://localhost:8000/metrics | Select-String "http_requests_total"
```

**📸 #17 `17-metrics-curl.png`:** the `http_requests_total{handler="/api/products",…}` lines.

Stop the port-forward with **Ctrl+C**.

> If the local Docker Compose stack is still using port 8000, run `docker compose down` first, or use `8001:8000` and `localhost:8001`.

### H3. Prometheus Targets

```powershell
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
```

Open **http://localhost:9090/targets**. Find **`serviceMonitor/inventory/inventory-backend/0`**. It should say **(2/2 up)**, with both endpoints in green **UP**. Type `inventory` in the filter box to find it quickly.

**📸 #18 `18-prometheus-targets.png`**

### H4. Grafana dashboard

```powershell
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
```

1. Open **http://localhost:3001**. Log in as user `admin` with the `GRAFANA_ADMIN_PASSWORD` you chose in F1.
2. **Dashboards** → open **Inventory Manager — API**.
3. Run the load test (H1) again in Git Bash while the dashboard is open. The panels refresh every 10 seconds.

**📸 #19 `19-grafana-dashboard.png`:** the dashboard with the *Requests / sec*, *Request rate by endpoint* and *Latency* panels showing lines.

### H5. Autoscaling (nice to have)

```powershell
kubectl get hpa -n inventory
```

Expected: `inventory-backend`, `TARGETS cpu: X%/60%`, `MINPODS 2`, `MAXPODS 8`. To try to make it scale, run a heavier load test (`REQUESTS=30000 CONCURRENCY=50`) and watch with `kubectl get hpa -n inventory -w`.

**📸 #20 `20-hpa.png`**

---

## PART I — Live demo script (M10: commit → pipeline → deployment updates)

Practise this once before the real presentation. It takes about 15 minutes, mostly waiting for the pipeline.

1. Open the app through the load balancer in one browser tab and GitHub **Actions** in another.
2. Make a visible change. Open `frontend\src\App.jsx`, find

   ```jsx
   <small>Warehouse stock control</small>
   ```

   and change it to

   ```jsx
   <small>Warehouse stock control · v2</small>
   ```
3. Commit and push:

   ```powershell
   cd C:\Users\Mohit-PC\devOps_capstone
   git add frontend/src/App.jsx
   git commit -m "Show version label in the header"
   git push
   ```
4. In the Actions tab, walk through the jobs as they run: tests → lint → build → **Trivy** → push → **deploy**.
5. In PowerShell, watch the pods roll over to the new image:

   ```powershell
   kubectl get pods -n inventory -w
   ```

   (Ctrl+C to stop.) Then `kubectl get deploy -n inventory -o wide` shows the **new commit SHA** as the image tag.
6. Refresh the app in the browser and point out that the header now says **v2**.
7. Optional extras: `helm history inventory -n inventory` shows each deploy as a numbered revision. `helm rollback inventory <previous-revision> -n inventory` rolls back.

**Troubleshooting lab (if time allows):**

```powershell
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n inventory          # shows ImagePullBackOff
kubectl describe pod -n inventory -l app=broken-image   # Events: tag "does-not-exist" not found
kubectl delete -f troubleshooting/broken-image.yaml

kubectl apply -f troubleshooting/broken-service.yaml
kubectl get endpoints -n inventory inventory-broken-service   # <none>: no pods match
kubectl get pods -n inventory --show-labels                   # pods are component=backend, not "api"
kubectl delete -f troubleshooting/broken-service.yaml
```

To record instead of presenting live, press **Win + Alt + R** (Xbox Game Bar) to record the screen, or use OBS.

---

## PART J — Final local re-check before submitting

Run this the day you submit, to be sure everything still works from a clean state:

```powershell
cd C:\Users\Mohit-PC\devOps_capstone
git status                          # clean
git log --oneline | Measure-Object  # Count should be 15 or more
docker compose down -v
docker compose up --build -d
curl.exe http://localhost:8000/health    # {"status":"UP"}
cd backend
.venv\Scripts\python -m pytest -q        # 19 passed
cd ..
docker compose down
```

---

## PART K — Tear everything down (do NOT skip — M7 and your wallet)

Do this right after your screenshots and demo are done. The order matters: Kubernetes created a load balancer and an EBS disk **outside** Terraform, and `terraform destroy` gets stuck deleting the VPC if they still exist.

```powershell
helm uninstall inventory -n inventory
kubectl delete pvc --all -n inventory
helm uninstall kube-prometheus-stack -n monitoring
helm uninstall ingress-nginx -n ingress-nginx
```

Wait about 2 minutes for AWS to delete the load balancer, then:

```powershell
cd C:\Users\Mohit-PC\devOps_capstone\terraform
terraform destroy
```

Type **`yes`**. This takes 10–15 minutes and ends with **`Destroy complete! Resources: NN destroyed.`**

**📸 #21 `21-terraform-destroy.png`**

Then:

1. **GitHub → Settings → Secrets and variables → Actions → Variables** → delete **`EKS_CLUSTER_NAME`**. Future pushes then skip the deploy job and the pipeline stays green.
2. **AWS console (ap-south-1)**, to check nothing is left:
   - EC2 → *Load Balancers*: empty
   - EC2 → *Volumes*: no `available` volumes left over
   - VPC → *NAT gateways*: none (or *Deleted*)
   - VPC → *Elastic IPs*: none
   - EKS → *Clusters*: none
3. Optional: IAM → Users → delete the `capstone-admin` access key if you no longer need it.

---

## Common problems and fixes

| Problem                                                                              | Fix                                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docker compose` says it can't connect to the Docker daemon                        | Start Docker Desktop and wait until it says*running*.                                                                                                                                                                                                                                           |
| `port is already allocated` on 3000, 8000 or 5433                                  | Another program is using the port. Run`docker ps`, then `docker stop <name>` for the conflicting container.                                                                                                                                                                                   |
| `.venv\Scripts\Activate.ps1 cannot be loaded`                                      | Don't activate; call`.venv\Scripts\python -m pytest -v` directly as shown in Part B.                                                                                                                                                                                                            |
| `git push` asks for a password                                                     | Use the GitHub CLI:`gh auth login`, then push again.                                                                                                                                                                                                                                            |
| Pipeline fails at**Trivy** with a new CVE                                      | A new vulnerability was published after this project was built. Read the table: it names the package and the*Fixed Version*. Bump that package in `backend/requirements.txt` (or rebuild for Alpine fixes), commit, push. This is the scan doing its job; screenshot it for your explanation. |
| Deploy fails:`Not authorized to perform sts:AssumeRoleWithWebIdentity`             | `github_repository` in `terraform.tfvars` doesn't exactly match `Owner/RepoName` on GitHub (case matters). Fix it, `terraform apply`, re-run the workflow.                                                                                                                                |
| Deploy fails:`Set the POSTGRES_PASSWORD repository secret`                         | Add the secret (F2) and re-run.                                                                                                                                                                                                                                                                   |
| Pods stuck in`ImagePullBackOff`                                                    | The GHCR packages are still private. Make both public (D3), then`kubectl delete pod -n inventory --all`.                                                                                                                                                                                        |
| `inventory-postgres-0` stuck `Pending`                                           | Storage class missing. Run`kubectl apply -f k8s/storageclass-gp3.yaml` and check `kubectl get pvc -n inventory`.                                                                                                                                                                              |
| Backend pods show`Init:0/1` for a long time                                        | They're waiting for Postgres, usually because of the problem above. Fix Postgres and they continue on their own.                                                                                                                                                                                  |
| Load balancer address doesn't open in the browser                                    | New load balancers need 3–5 minutes for DNS. Use`http://` (not https), and check `kubectl get ingress -n inventory` shows an ADDRESS.                                                                                                                                                        |
| Prometheus target missing                                                            | Check that`kubectl get servicemonitor -n inventory` lists `inventory-backend`. If not, re-run the deploy (the CRD must exist first, which `bootstrap-cluster.sh` provides).                                                                                                                 |
| Grafana panels say*No data*                                                        | Run the load test again, set the time range (top right) to*Last 15 minutes*, wait 30 seconds.                                                                                                                                                                                                   |
| `terraform destroy` hangs on VPC or subnets                                        | A load balancer or disk still exists. Run the`helm uninstall` / `kubectl delete pvc` commands above (or delete the load balancer in EC2 → Load Balancers), then run `terraform destroy` again.                                                                                             |
| You changed`POSTGRES_PASSWORD` after the first deploy and the backend can't log in | Postgres kept the old password on its disk. Put the old one back, or`kubectl delete pvc --all -n inventory` (this wipes the data) and redeploy.                                                                                                                                                 |

---

## Submission checklist (from GRADING.md)

```text
Application
  [ ] GitHub repository URL submitted                      (Part C)
  [ ] docker compose up --build works        📸 1, 2       (Part A)
  [ ] 4+ REST endpoints                      📸 3          (Part A3)
  [ ] Alembic migration present              📸 4          (Part A5)
Testing
  [ ] pytest passes, 19 tests                📸 5          (Part B)
Git
  [ ] 10+ meaningful commits                 📸 6          (Part C3)
Docker
  [ ] backend Dockerfile builds, frontend multi-stage, both non-root   (Part A6)
CI/CD
  [ ] Green pipeline + run URL               📸 7          (Part D1 / F3)
  [ ] Images in GHCR with SHA tags           📸 9          (Part D3)
Security
  [ ] Trivy step + output + explanation      📸 8          (Part D2)
  [ ] No secrets in Git (keys only in ~/.aws, tfvars git-ignored)
Terraform
  [ ] terraform plan                         📸 10         (Part E3)
  [ ] VPC + EKS in AWS console               📸 11, 12     (Part E5)
  [ ] terraform destroy                      📸 21         (Part K)
Kubernetes + Helm
  [ ] pods Running                           📸 13         (Part G)
  [ ] services                               📸 14
  [ ] helm list                              📸 15
  [ ] app via Ingress                        📸 16
Observability
  [ ] /metrics                               📸 17         (Part H)
  [ ] Prometheus target UP                   📸 18
  [ ] Grafana dashboard with data            📸 19
Documentation
  [ ] README.md present
  [ ] Live demo / recording                                (Part I)
```
