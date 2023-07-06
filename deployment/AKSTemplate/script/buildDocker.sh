#Copyright (c) Microsoft. All rights reserved.
# Read arguments
#acrname:acrrepo
while getopts a:r:d:e: flag
do
    case "${flag}" in
        a) acrname=${OPTARG};;
        r) acrrepo=${OPTARG};;
        d) dockerpath=${OPTARG};;
        e) envyaml=${OPTARG};;
    esac
done

cd "$(dirname "${BASH_SOURCE[0]}")"
cd "../"
#Create a tag for the new image
image_tag=$(date '+%Y%m%d%H%M%S')

echo "ACR Name: $acrname";
echo "Release Tag: $image_tag";
echo "ACR Repository Name:$acrrepo";
echo "Docker Path:$dockerpath";
echo "Environment YAML:$envyaml";
#Build and deploy docker images 

docker build --build-arg ENVIRONMENT_YAML="$envyaml" --build-arg DOCKER_PATH="$dockerpath" --tag "$acrname"/"$acrrepo":"latest" .
az acr login --name "$acrname"
docker push  "$acrname"/"$acrrepo":"latest"