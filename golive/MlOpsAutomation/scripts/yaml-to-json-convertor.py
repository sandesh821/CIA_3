#Copyright (c) Microsoft. All rights reserved.
# Importing Libraries
import yaml
import json

# Converting YAML to JSON
with open('../config.yaml', 'r') as f_yaml:
    with open('./config.json', 'w') as f_json:
        json.dump(yaml.full_load(f_yaml), f_json)