#Copyright (c) Microsoft. All rights reserved.
# Read arguments
#acrname:acrrepo
while getopts a:r:m:g:s:e: flag
do
    case "${flag}" in
        a) acrname=${OPTARG};;
        r) acrrepo=${OPTARG};;
        m) amlname=${OPTARG};;
        g) rgname=${OPTARG};;
        s) subid=${OPTARG};;
        e) envyaml=${OPTARG};;
    esac
done

# Working directory to "../func_app"
cd "src"

#Create a tag for the new image
image_tag=$(date '+%Y%m%d%H%M%S')

echo "ACR Name: $acrname";
echo "Release Tag: $image_tag";
echo "ACR Repository Name:$acrrepo";
echo "Env Yaml file:$envyaml";

#Build and deploy docker images 
echo "$acrname"/"$acrrepo":"$image_tag"

docker build --tag "$acrname"/"$acrrepo":"$image_tag" --build-arg ENVIRONMENT_YAML="$envyaml" --build-arg AML_WORKSPACE_NAME="$amlname" --build-arg RESOURCE_GROUP_NAME="$rgname" --build-arg SUBSCRIPTION_ID="$subid" .
az acr login --name "$acrname"
docker push  "$acrname"/"$acrrepo":"$image_tag"
