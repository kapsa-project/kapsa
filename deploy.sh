#!/bin/bash

# build operator-image
cd operator && docker build -t kapsa-operator:latest . && cd ..

# load to kind
kind load docker-image kapsa-operator:latest

# deploy crds
kubectl apply -f operator/crds/

# deploy development resources for kapsa operator
kubectl apply -f development/kapsa-system/

# deploy development kapsa-resources
kubectl apply -f development/dev-kapsa-resources/

# restart operator
kubectl rollout restart deployment/kapsa-operator -n kapsa-system
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator