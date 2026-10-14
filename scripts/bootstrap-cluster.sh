#!/usr/bin/env bash
# One-time cluster add-ons after `terraform apply` + `aws eks update-kubeconfig`:
# namespaces, default gp3 StorageClass, ingress-nginx, metrics-server (for HPA),
# and kube-prometheus-stack (Prometheus + Grafana).
set -euo pipefail
cd "$(dirname "$0")/.."

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storageclass-gp3.yaml

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  -n ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer \
  --wait

helm upgrade --install metrics-server metrics-server/metrics-server \
  -n kube-system --wait

helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f monitoring/prometheus-values.yaml \
  -f monitoring/grafana-values.yaml \
  --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD:-change-me}" \
  --wait --timeout 10m

echo
echo "Ingress load balancer (open this in the browser once the app is deployed):"
kubectl get svc -n ingress-nginx ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}{"\n"}'
