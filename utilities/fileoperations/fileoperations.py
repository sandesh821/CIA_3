#Copyright (c) Microsoft. All rights reserved.
import os
import shutil
def __readFile__(path):
    try:
        with open(path, 'r') as file:
            content = file.read()
            file.close()
        return content
    except:
        print("Error in loading file")
        raise

def __updateFile__(outputPath,content):
    try:
        with open(outputPath, 'w') as f:
            f.write(content)
    except:
        print("Error in saving file")
        raise

def __copyAndOverwrite__(from_path, to_path):
    if not os.path.isdir(to_path): 
        os.makedirs(to_path)
    if os.path.exists(to_path):
        shutil.rmtree(to_path)
    shutil.copytree(from_path, to_path)