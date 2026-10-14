# Terraform — AWS VPC + EKS for Inventory Manager

Provisions everything the app needs in AWS (default region `ap-south-1`):

| Resource | Details |
|---|---|
| VPC | `10.30.0.0/16` across 2 AZs |
| Public subnets (2) | Load balancers (ingress-nginx) and the NAT gateway; tagged `kubernetes.io/role/elb` |
| Private subnets (2) | Worker nodes; tagged `kubernetes.io/role/internal-elb` |
| NAT gateway (1) | Outbound internet for nodes (pulling images from GHCR) |
| EKS cluster | Kubernetes `1.34`, public API endpoint, IRSA enabled |
| Managed node group | 2 × `m7i-flex.large` (AL2023), scales 2–3 |
| Add-ons | CoreDNS, kube-proxy, VPC CNI, EBS CSI driver (with its own IRSA role) |
| GitHub OIDC deploy role | Optional; lets the CI deploy job reach EKS without stored AWS keys |

## Usage

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # edit github_repository etc.
terraform init
terraform fmt -check
terraform validate
terraform plan -out tfplan
terraform apply tfplan          # ~15 minutes
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

AWS credentials come from `aws configure` (or `AWS_PROFILE` / environment variables). They are never stored in this folder.

## Tear down

```bash
# Remove Kubernetes-created load balancers and volumes first, or the VPC can't be deleted
helm uninstall inventory -n inventory
helm uninstall ingress-nginx -n ingress-nginx
kubectl delete pvc --all -n inventory
terraform destroy
```

> **Cost warning:** the EKS control plane (~$0.10/h), NAT gateway (~$0.06/h + data), 2 × m7i-flex.large and the
> ingress load balancer all bill while running. Destroy as soon as grading/demo is done.
