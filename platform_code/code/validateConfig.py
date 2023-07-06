#Copyright (c) Microsoft. All rights reserved.
import more_itertools as mit
from itertools import chain

def zip_equal(*iterables):
    ls = list(mit.zip_equal(*iterables))
    return ls

#Test scirpt
if __name__ == "__main__":
    print(zip_equal(['DeepMC'], ['deepmcFrameworkEnvironment'], ['deepmcenvironment.yml'], ['ds5v2-16c-56-112-cent'], ['mlcode/trainDeepMC.py'], ['deepmc_data']))