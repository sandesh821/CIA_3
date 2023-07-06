#Copyright (c) Microsoft. All rights reserved.
import os
from event_grid_setup import mleventsetup, storageeventsetup
import subprocess, sys
print("**********DOCKER-ACR DEPLOYMENT FOR AZURE FUNCTIONS CONTINUOUS DEPLOYMENT*****************")
p = subprocess.Popen(["powershell.exe", '.\msrc-full-automation-docker\setup.ps1'], stdout=sys.stdout)
p.communicate()
print("**********DEPLOYMENT COMPLETE********************")

print("**********DEPLOYING ML EVENTS ARM TEMPLATE*****************")
os.system(f"az deployment group create --resource-group forecast-msrc-rg --template-file {mleventsetup.path}")
print("**********DEPLOYMENT COMPLETE********************")

print("**********DEPLOYING STORAGE EVENTS ARM TEMPLATE*****************")
os.system(f"az deployment group create --resource-group forecast-msrc-rg --template-file {storageeventsetup.path}") 
print("**********DEPLOYMENT COMPLETE********************")