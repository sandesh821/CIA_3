import yaml
import ast
import logging

#===================Load configurations===================
def loadYaml(filePath, objName):
    try:
        with open(filePath, 'r') as file:
            confg = yaml.safe_load(file)
    except (IOError, ValueError, EOFError, FileNotFoundError) as ex:
        logging.error("Config file not found")
        logging.error(ex)
        raise ex
    except Exception as YAMLFormatException:
        logging.error("Config file not found")
        logging.error(YAMLFormatException)
        raise YAMLFormatException
    config = str(confg.get(objName,{}))
    config_parsed = ast.literal_eval(config)
    return config_parsed

def saveYaml(dict, filePath):
    # use the yaml module to dump the dictionary to a string in YAML format
    yaml_str = yaml.dump(dict)

    # print the YAML string
    print(yaml_str)

    # write the YAML string to a file
    with open(filePath, 'w') as f:
        yaml.dump(yaml_str)