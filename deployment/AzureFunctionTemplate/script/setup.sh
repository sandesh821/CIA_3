#Copyright (c) Microsoft. All rights reserved.
# Read arguments
#model:type
while getopts m:t: flag
do
    case "${flag}" in
        m) model=${OPTARG};;
        t) type=${OPTARG};;
    esac
done
echo "Model Name: $model";
echo "Function Type: $type";

# Working directory to "../func_app"
cd "src"

# Step 1: Create Function App code template using the parameters
func init --worker-runtime python --docker 
func new --name "func_${model}" --template "$type" #Azure Timer trigger

# cp -f ../requirements.txt requirements.txt

# Step 2: Update function app structure to call and score models
cp ../functiontemplate/main.py "func_${model}"/
cp ../functiontemplate/readBlob.py "func_${model}"/
cp ../functiontemplate/__init__.py "func_${model}"/
# cp -f ../../functiontemplate/function.json "func_${model}"/function.json

