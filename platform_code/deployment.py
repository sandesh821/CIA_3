import gitinfo
import json
import subprocess
import os

with open('code/codeversiondetails.json', 'w') as f:
    json.dump(gitinfo.get_git_info(), f)






