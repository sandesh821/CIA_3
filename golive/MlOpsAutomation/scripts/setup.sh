#Copyright (c) Microsoft. All rights reserved.
# Converting YAML to JSON
python yaml-to-json-convertor.py

# Fetching Function Names from Config

# Reading JSON
# TODO: Check for the equivalent method of "ConvertFrom-JSON" in Unix Scripting
$config_json = cat config.json

# Dynamic (If doesn't work, the fixed function list in line 51 can be used to manually enter function names)
# Functions Handler List

functions = ("APITimerTrigger" "OnlineScoringTimerTrigger")

# First Loop - Traversing Main List
for($i = 0; $i -lt $config_json.FunctionNames.length; $i++) { 
    
    # Second Loop - Traversing Nested Lists
    for ($j = 0; $j -lt $config_json.FunctionNames[$i].length; $j++) {
        
        # Flag Variable to verify the function addition to final list
        $exist = "false"

        # Third Loop - Checking if function name added to final list
        for ($k = 0; $k -lt functions.length; $k++) {
            if($config_json.FunctionNames[$i][$j] -eq functions[$k]) {
                $exist = "true"
            }
        }

        # Adding function name to Final List
        if($exist -eq "false") {
            $functions += $config_json.FunctionNames[$i][$j]
        }
    }
}

# Initialize Function Environment - Python, Docker Deployment
func init --worker-runtime python --docker

# Creating Functions
for($i = 0; $i -lt functions.length; $i++) {
    func new --name functions[$i] --template "TimerTrigger"
}

# Dynamic (If doesn't work, the fixed variables in lines 60 - 66 can be used to manually enter the credentials)
$registry_server = $config_json.registry_server
$repository_name = $config_json.repository_name
$image_tag = $config_json.image_tag
$local_directory_folder = $config_json.local_directory_folder

# Functions Handler List - Static (Added in-case the code segment between 10 - 34 doesn't work)
# $functions = @("BlobCreated", "BlobDeleted", "ModelDeployment", "ModelRegistered", "RunCompleted")

# Copying Functions
for($i = 0; $i -lt $functions.length; $i++) { 
    cp -r "..\functions-repo\$($functions[$i])" $functions[$i]
}

# Pushing Code to ACR

# Docker Login
# docker login $registry_server
# -u $registry_userame -p $registry_password

# Building Docker Image
# docker build --tag $registry_server"/"$repository_name":"$image_tag $local_directory_folder

# Pushing Docker Image to ACR Repository
# docker push $registry_server"/"$repository_name":"$image_tag

# Removing Converted Config JSON
rm config.json

# Returning back to main directory
cd ..