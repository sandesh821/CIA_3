# Read arguments
#acrname:acrrepo
while getopts a:r:m:g:s: flag
do
    case "${flag}" in
        a) acrname=${OPTARG};;
        r) acrrepo=${OPTARG};;
        m) appname=${OPTARG};;
        g) rgname=${OPTARG};;
    esac
done

cd "$(dirname "${BASH_SOURCE[0]}")"

#Create a tag for the new image
image_tag=$(date '+%Y%m%d%H%M%S')

echo "ACR Name: $acrname";
echo "Release Tag: $image_tag";
echo "ACR Repository Name:$acrrepo";
echo "RG Name: $rgname";
echo "App Name:$appname";

image_identifier="$acrname"/"$acrrepo":"$image_tag"
export image_identifier

#Build and deploy docker images 

docker build --tag "$acrname"/"$acrrepo":"$image_tag" .
az acr login --name "$acrname"
docker push  "$acrname"/"$acrrepo":"$image_tag"

# Deploy image to function app
# az functionapp config container show --name "eventManagerFunctionApp" --resource-group "forecasting"
# az functionapp config container set --name "eventManagerFunctionApp" --resource-group "forecasting" --docker-registry-server-url "https://acrforecasting.azurecr.io" --docker-custom-image-name "acrforecasting.azurecr.io/golivefapp:20230511121516"
az functionapp config container set --name $appname --resource-group "$rgname" --docker-registry-server-url "https://$acrname" --docker-custom-image-name "$acrname/$acrrepo":"$image_tag" 
