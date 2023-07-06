#Copyright (c) Microsoft. All rights reserved.
class DeploymentInfraManager(object):
    
    def __init__(self,params):
        self.environments = ["AKS", "AzureFunction"]
        self.OnlyAKSSupportingModels = ["DeepMC","TFT"]
        self.MODELSIZELIMITAZUREFUNCTION = 14
        self.HORIZONLIMIT = 24

        self.acceleratortype = params["acceleratortype"]
        self.modelname = params["modelname"]
        self.modeltype = params["modeltype"]
        self.cost = params["cost"]

        self.versiondependency = params["versiondependency"]
        self.horizon = params["horizon"]
        self.hostingmodel = params["hostingmodel"]

    def __extractModelSize__(self):
        raise NotImplementedError("TBD")


    def getTargetEnvironment(self):
        self.modelsize = 0 #self.__extractModelSize__()

        if (self.acceleratortype == "GPU" or self.modeltype == "multi" or self.modelname in self.OnlyAKSSupportingModels or self.cost == "medium"):
            return self.environments[0]
        elif (self.modelsize >= self.MODELSIZELIMITAZUREFUNCTION) or (self.versiondependency == "high") or self.horizon > self.HORIZONLIMIT:
            return self.environments[0]
        else:
            return self.environments[1]
        
