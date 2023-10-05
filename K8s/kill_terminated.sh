#!/bin/bash

# Get a list of namespaces with pods in the "Terminating" state
TERMINATING_NAMESPACES=$(kubectl get pods --all-namespaces | grep "Terminating" | awk '{print $1}' | sort -u)
# Loop through the list of namespaces
for NAMESPACE in $TERMINATING_NAMESPACES
do
    # Get a list of pod names in the "Terminating" state within the current namespace
    TERMINATING_PODS=$(kubectl get pods --namespace=$NAMESPACE | grep "Terminating" | awk '{print $1}')
    # Loop through the list and delete each pod in the current namespace
    for POD in $TERMINATING_PODS
    do
        kubectl delete pod $POD --namespace=$NAMESPACE --grace-period=0 --force
        echo "Deleted pod: $POD in namespace: $NAMESPACE"
    done
done
