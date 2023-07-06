#Copyright (c) Microsoft. All rights reserved.
RESOURCE_GROUP="forecasting2"
AKS_CLUSTER="forecasting2aks"
ACR="fp2testamlcr"
IDENTITY_RESOURCE_GROUP="forecasting2"
IDENTITY_NAME="forecasting2identity"
POD_IDENTITY_NAME="forecasting2identityname"
POD_IDENTITY_NAMESPACE="forecasting2framework"

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

# Refer to (https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/ for latest version and command to download kubectl)
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl 

kubectl version --client

# Use In case cli throws Value error
# az upgrade 

az extension add --name aks-preview

az aks create --name $AKS_CLUSTER --resource-group $RESOURCE_GROUP --node-count 1 --generate-ssh-keys --enable-pod-identity --enable-pod-identity-with-kubenet
echo "AKS Created"

az aks update --attach-acr $ACR --name $AKS_CLUSTER
echo "ACR attached"

az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER  

az feature register --namespace "Microsoft.ContainerService" --name "EnablePodIdentityPreview" 
az provider register --namespace Microsoft.ContainerService --wait

(
    az identity create --resource-group ${IDENTITY_RESOURCE_GROUP} --name ${IDENTITY_NAME}
) && 
( echo "Identity Created"
export IDENTITY_CLIENT_ID="$(az identity show -g ${IDENTITY_RESOURCE_GROUP} -n ${IDENTITY_NAME} --query clientId -otsv)"
export IDENTITY_RESOURCE_ID="$(az identity show -g ${IDENTITY_RESOURCE_GROUP} -n ${IDENTITY_NAME} --query id -otsv)"
NODE_GROUP=$(az aks show -g $RESOURCE_GROUP -n $AKS_CLUSTER --query nodeResourceGroup -o tsv)
NODES_RESOURCE_ID=$(az group show -n $NODE_GROUP -o tsv --query "id")
)

az role assignment create --role "Virtual Machine Contributor" --assignee "$IDENTITY_CLIENT_ID" --scope $NODES_RESOURCE_ID

echo $IDENTITY_RESOURCE_ID
az aks pod-identity add --resource-group $RESOURCE_GROUP --cluster-name $AKS_CLUSTER --namespace ${POD_IDENTITY_NAMESPACE}  --name ${POD_IDENTITY_NAME} --identity-resource-id ${IDENTITY_RESOURCE_ID}
kubectl get azureidentity -n $POD_IDENTITY_NAMESPACE
kubectl get azureidentitybinding -n $POD_IDENTITY_NAMESPACE