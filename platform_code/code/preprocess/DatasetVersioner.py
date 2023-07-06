#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Dataset
from azureml.core import Workspace
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline, PipelineData
from azureml.core. runconfig import RunConfiguration
import DefaultParamSet

class DatasetVersioning:
    def __init__(self):
        self._workspace = Workspace.from_config()
        self._datastore = self.workspace.get_default_datastore()

    def retrieve_dataset(self, dataset_name, version_number):
        ds = Dataset.get_by_name(workspace=self._workspace, name=dataset_name, version=version_number)
        return ds

    def create_dataset(self, dataset_path_tuple_list):
        """

        :param dataset_path_tuple_list: [(datastore,path),...]
        :return:
        """
        ds = Dataset.File.from_files(path=dataset_path_tuple_list)


    def register_dataset(self, ds, dataset_name, dataset_description, is_new_version=True):
        ds.register(workspace=self._workspace, name = dataset_name,
                                         description = dataset_description,create_new_version = is_new_version)

    def delete_dataset(self):
        """
        In the Azure UI, use unregister to delete dataset
        :return:
        """
        pass

    def set_pipeline(self, input_dataset_name, input_dataset_version_number,
                     output_dataset_name,script_name, compute_target, project_folder,
                     conda_dependencies = DefaultParamSet().conda_dependencies_data_pipeline):

        # get input dataset
        input_ds = self.register_dataset(input_dataset_name, input_dataset_version_number)

        # register pipeline output as dataset
        output_ds = PipelineData(output_dataset_name, datastore=self._datastore).as_dataset()
        output_ds = output_ds.register(name=output_dataset_name, create_new_version=True)

        run_config = RunConfiguration()
        run_config.environment.docker.enabled = True
        run_config.environment.python.conda_dependencies = conda_dependencies

        # configure pipeline step to use dataset as the input and output
        prep_step = PythonScriptStep(script_name=script_name,
                                     inputs=[input_ds.as_named_input(input_dataset_name)],
                                     outputs=[output_ds],
                                     runconfig=run_config,
                                     compute_target=compute_target,
                                     source_directory=project_folder)
        return prep_step