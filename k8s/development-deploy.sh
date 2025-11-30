#!/bin/bash

# Development deployment script for Mazarbul
set -e

NAMESPACE="mazarbul-development"
CHART_PATH="./helm/mazarbul"
VALUES_FILE="./helm/mazarbul/values-development.yaml"

echo "🚀 Deploying Mazarbul to development environment..."

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy using Helm
helm upgrade --install mazarbul-dev $CHART_PATH \
    --namespace $NAMESPACE \
    --values $VALUES_FILE \
    --set backend.image.tag=development-latest \
    --set frontend.image.tag=development-latest \
    --wait \
    --timeout 10m

echo "✅ Development deployment completed!"
echo ""
echo "Services:"
kubectl get services -n $NAMESPACE
echo ""
echo "Pods:"
kubectl get pods -n $NAMESPACE
echo ""
echo "🔗 Access the application:"
echo "   Frontend: kubectl port-forward -n $NAMESPACE svc/mazarbul-dev-frontend 3000:3000"
echo "   Backend:  kubectl port-forward -n $NAMESPACE svc/mazarbul-dev-backend 8000:8000"