#Copyright (c) Microsoft. All rights reserved.
# func new --name APIDataManager --worker-runtime python --template "Timer trigger"
# func new --name PreprocessingModule --worker-runtime python --template "HTTP Trigger"
# func new --name InterpolationModule --worker-runtime python --template "Azure Blob Storage trigger"
# func new --name DataDriftModule --worker-runtime python --template "Azure Blob Storage trigger"
func new --name ModelRetraining --worker-runtime python --template "Timer Trigger"