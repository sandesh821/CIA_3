#Copyright (c) Microsoft. All rights reserved.
# Initialize Function Environment - Python, Docker Deployment
func init --worker-runtime python --docker

# Functions Handler List
$functions = @("BlobCreated", "BlobDeleted", "ModelDeployment", "ModelRegistered", "RunCompleted")

# Creating Functions
for($i = 0; $i -lt $functions.length; $i++) { 
    func new --name $functions[$i] --template "Azure Event Grid trigger"
}