#!/bin/bash

# build operator-image
cd operator && docker build -t kapsa-operator:latest . && cd ..

# load to kind
kind load docker-image kapsa-operator:latest

# deploy crds
kubectl apply -f operator/crds/

# deploy development resources
kubectl apply -f development/

# restart operator
kubectl rollout restart deployment/kapsa-operator -n kapsa-system
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator