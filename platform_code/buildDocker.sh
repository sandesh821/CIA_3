# Read arguments
#acrname:acrrepo
while getopts a:r:m:g:s: flag
do
    case "${flag}" in
        a) acrname=${OPTARG};;
        r) acrrepo=${OPTARG};;
        m) amlname=${OPTARG};;
        g) rgname=${OPTARG};;
        s) subid=${OPTARG};;
    esac
done

#Create a tag for the new image
image_tag=$(date '+%Y%m%d%H%M%S')

echo "ACR Name: $acrname";
echo "Release Tag: $image_tag";
echo "ACR Repository Name:$acrrepo";

echo "Subscription ID: $subid";
echo "AML workspace name:$amlname";
echo "RG name:$rgname";

image_identifier="$acrname"/"$acrrepo":"$image_tag"
export image_identifier


#Build and deploy docker images 

docker build --tag "$acrname"/"$acrrepo":"$image_tag" --build-arg AML_WORKSPACE_NAME="$amlname" --build-arg RESOURCE_GROUP_NAME="$rgname" --build-arg SUBSCRIPTION_ID="$subid" .
az acr login --name "$acrname"
docker push  "$acrname"/"$acrrepo":"$image_tag"

