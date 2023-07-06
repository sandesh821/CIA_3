# To enable ssh & remote debugging on app service change the base image to the one below
# FROM mcr.microsoft.com/azure-functions/python:3.0-python3.8-appservice
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.8

RUN sed -i '/jessie/d' /etc/apt/sources.list \
 && apt-get update -y
RUN apt-get upgrade -y
RUN apt-get dist-upgrade

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY requirements.txt /requirements.txt
COPY azurefunctionenvironment.yml /environment.yml

# Install miniconda
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
     /bin/bash ~/miniconda.sh -b -p /opt/conda

# Put conda in path so we can use conda activate
ENV PATH=$CONDA_DIR/bin:$PATH

ARG AML_WORKSPACE_NAME
ARG RESOURCE_GROUP_NAME
ARG SUBSCRIPTION_ID

# Print AML
RUN echo "$AML_WORKSPACE_NAME"

#Print RG
RUN echo "$RESOURCE_GROUP_NAME"

#Print SUBSCRIPTION_ID
RUN echo "$SUBSCRIPTION_ID"

# Put conda in path so we can use conda activate
ENV SUBSCRIPTION_ID=$SUBSCRIPTION_ID

# Put conda in path so we can use conda activate
ENV RESOURCE_GROUP_NAME=$RESOURCE_GROUP_NAME

# Put conda in path so we can use conda activate
ENV AML_WORKSPACE_NAME=$AML_WORKSPACE_NAME

RUN conda init bash && \
    pip install -r /requirements.txt && \
    conda env update --name base --file /environment.yml

COPY . /home/site/wwwroot