from azureml.core import Workspace, Environment

env = Environment('deepmcFrameworkEnvironment')

env.environment_variables['SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL'] = 'True'