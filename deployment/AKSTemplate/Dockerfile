#Copyright (c) Microsoft. All rights reserved.
FROM mcr.microsoft.com/azureml/openmpi3.1.2-ubuntu18.04

RUN mkdir -p $HOME/.cache
WORKDIR /

ARG DOCKER_PATH
ARG ENVIRONMENT_YAML

# Print docker path
RUN echo "$DOCKER_PATH"

#Print environment yaml
RUN echo "$ENVIRONMENT_YAML"

ENV SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True

#COPY azureml-environment-setup/99brokenproxy /etc/apt/apt.conf.d/
RUN if dpkg --compare-versions `conda --version | grep -oE '[^ ]+$'` lt 22.11.1; then conda install conda==22.11.1; fi
COPY ./src/code/$ENVIRONMENT_YAML azureml-environment-setup/mutated_conda_dependencies.yml

RUN ldconfig /usr/local/cuda/lib64/stubs && conda env create -p /azureml-envs/$DOCKER_PATH -f azureml-environment-setup/mutated_conda_dependencies.yml && rm -rf "$HOME/.cache/pip" && conda clean -aqy && CONDA_ROOT_DIR=$(conda info --root) && rm -rf "$CONDA_ROOT_DIR/pkgs" && find "$CONDA_ROOT_DIR" -type d -name __pycache__ -exec rm -rf {} + && ldconfig
ENV PATH /azureml-envs/$DOCKER_PATH/bin:$PATH

RUN echo "Copying environment context"

ENV AZUREML_CONDA_ENVIRONMENT_PATH /azureml-envs/$DOCKER_PATH
ENV LD_LIBRARY_PATH /azureml-envs/$DOCKER_PATH/lib:$LD_LIBRARY_PATH
ENV CONDA_DEFAULT_ENV=$DOCKER_PATH CONDA_PREFIX=/azureml-envs/$DOCKER_PATH

#RUN conda install -c conda-forge cudatoolkit=11.2.2 cudnn=8.1.0
#ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CONDA_PREFIX/lib/

ENV AZUREML_ENVIRONMENT_IMAGE True

# Copy files to working directory
COPY ./src/ /app/src/
WORKDIR /app/src

# Run the script
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
ENTRYPOINT ["python", "main.py"]