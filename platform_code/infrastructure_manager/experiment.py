#Copyright (c) Microsoft. All rights reserved.
class Experiment:
    def __init__(self, name, cores, nodes):
        self.__name = name
        self.__cores = cores
        self.__nodes = nodes

    @property
    def name(self):
        return self.__name
    
    @name.setter
    def name(self, value):
        self.__name=value
    
    @property
    def cores(self):
        return self.__cores
    
    @cores.setter
    def cores(self, value):
        self.__cores=value

    @property
    def nodes(self):
        return self.__nodes
    
    @nodes.setter
    def nodes(self, value):
        self.__nodes=value

    def requestedCores(self):
        return self.__nodes * self.cores