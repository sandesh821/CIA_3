#Copyright (c) Microsoft. All rights reserved.
# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:4-python3.8-appservice
FROM mcr.microsoft.com/azure-functions/python:4-python3.8

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade -y

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /home/site/wwwroot