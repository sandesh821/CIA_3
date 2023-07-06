#Copyright (c) Microsoft. All rights reserved.
import pandas as pd
import numpy as np
import os
from masterConfiguration import mapproperty, ENVIRONMENT_DEFAULT_COLUMNS

class ExperimentConfigGenerator(object):
    def __init__(self,params,computeList,experimentList = None):
        print("==============Generating Configurations=============")
        self.csvFilePath = params.get("csvFilePath")
        self.experimentList = experimentList
        self.templatePath = params.get("templatePath")
        self.identifierColumn = 'sno'
        self.experimentIdentifierColumn =  params.get("experimentIdentifierField","")
        self.outputPath = params.get("outputPath")
        self.autocomputeEnabled = params.get("autocomputeEnabled")
        if(self.autocomputeEnabled):
            self.computeList = computeList
            self.computeField = params.get("computeField")
            self.internalComputeField = params.get("internalComputeField")
        
        self.mandatoryFields = [self.experimentIdentifierColumn,"algorithm"]
        

    # Read dataset as CSV
    def __readDataset__(self):
        print("Loading dataset")
        if self.experimentList is None:
            self.configDataset = pd.read_csv(self.csvFilePath)
        else:
            self.configDataset = self.experimentList
        self.columnList  = self.configDataset.columns[1:].tolist() # first column for sno
        self.noOfExperiments = len(self.configDataset)
        if(self.autocomputeEnabled):
            self.columnList.append(self.computeField)
            self.columnList.append(self.internalComputeField)

        # Validate Config CSV file
        if all(col in self.columnList for col in self.mandatoryFields):
            print("Valid Config")
        else:
            print("Manadatory columns missing")
    
    # Read template config
    def __readTemplate__(self):
        print("Loading template")
        with open(self.templatePath, 'r') as file:
            self.config = file.read()
            file.close()

    def __replacePlaceholders__(self,df,config):
        for placeholder in self.columnList:  
            try:
                if pd.isnull(df[placeholder].values[0]):
                    continue
                
                columnVal = df[placeholder].values[0]
                if np.isreal(df[placeholder].values[0]):
                    columnVal = int(df[placeholder].values[0])
                    
                config = config.replace("$$"+placeholder+"$$",str(columnVal))
            except Exception as ex:
                print(placeholder)
                raise ex
        return config
    
    def __saveFile__(self,fileName,updatedConfig):
        if not os.path.isdir(self.outputPath):
            os.makedirs(self.outputPath,exist_ok=True)
        with open(self.outputPath+str(fileName.replace("'",""))+'.yaml','w') as f:
            f.write(updatedConfig)

    def __allocateInternalPipelineClusters__(self):
        #===========Add allocation for internal pipelines======
        self.configDataset[self.internalComputeField] = ""
        for i, row in self.configDataset.iterrows():
            if row["algorithm"] == "DeepMC" and row["Status"] == 0:
                self.configDataset.loc[i,self.internalComputeField] = self.computeList.loc[row[self.experimentIdentifierColumn]+"Internal"][self.computeField]

    def __addDefaultConfigurationFields__(self):
        for col in ENVIRONMENT_DEFAULT_COLUMNS:
            self.configDataset[col] = self.configDataset.apply(mapproperty, axis=1,args=(col,1))
        
        self.columnList = self.columnList + ENVIRONMENT_DEFAULT_COLUMNS

    def prepareConfigYAMLs(self):
        self.__readDataset__()
        self.__readTemplate__()

        self.__addDefaultConfigurationFields__()

        if(self.autocomputeEnabled):
            self.configDataset = self.configDataset.merge(self.computeList,left_on=[self.experimentIdentifierColumn], right_on=["experimenttag"],how="inner")
            self.__allocateInternalPipelineClusters__()

        yamlFileList = []
        # Read all experimentConfigs and prepare yamls for each of them
        for k in range(1,self.noOfExperiments+1) :
            df = self.configDataset[self.configDataset[self.identifierColumn] == k]
            if not df.empty:
                # Generate config after replacing placeholders
                updatedConfig = self.__replacePlaceholders__(df,self.config)
                
                # Save the config
                self.__saveFile__(df[self.experimentIdentifierColumn].values[0],updatedConfig)
                yamlFileList.append(df[self.experimentIdentifierColumn].values[0]+".yaml")
        return yamlFileList