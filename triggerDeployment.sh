# Read arguments
while getopts i:n:f:t: flag
do
    case "${flag}" in
        i) experimentsetid=${OPTARG};;
        n) experimentsetname=${OPTARG};;
        f) fileUpload=${OPTARG};;
        t) type=${OPTARG};;
    esac
done

echo "experimentsetid: $experimentsetid"
echo "experimentsetname: $experimentsetname"
echo "fileUpload: $fileUpload"
echo "type: $type"

python buildDeployGoLiveFunctionApp.py $experimentsetid $experimentsetname $fileUpload $type

python buildRunDeploymentManager.py $experimentsetid $experimentsetname $fileUpload $type