#Copyright (c) Microsoft. All rights reserved.
class ComputeCluster:
    def __init__(self, name, cores, idlenodes, location):
        self.__name = name
        self.__cores = cores
        self.__idlenodes = idlenodes
        self.__location = location

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
    def idlenodes(self):
        return self.__idlenodes
    
    @idlenodes.setter
    def nodes(self, value):
        self.__idlenodes=value

    @property
    def location(self):
        return self.__location
    
    @location.setter
    def location(self, value):
        self.__location=value