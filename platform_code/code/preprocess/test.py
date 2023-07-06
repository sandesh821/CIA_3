#Copyright (c) Microsoft. All rights reserved.
from azureml.core import Run
import os
import argparse
import random

parser = argparse.ArgumentParser()

parser.add_argument('--input-data', type=str,dest = 'input', default = 'input' ,help='Directory to output the processed training data')
parser.add_argument('--output-data', type=str,dest = 'output', default = 'output' ,help='Directory to output the processed training data')

args = parser.parse_args()

run = Run.get_context()
acc_key = run.get_secret(name="blobkv")
print(acc_key)
print(10)



# Get arguments from parser
print(args.output)
os.makedirs(output,exist_ok = True)
run.complete()

