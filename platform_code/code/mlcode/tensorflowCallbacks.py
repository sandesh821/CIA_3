from datetime import datetime
import pandas as pd
import numpy as np

from tensorflow import keras

from logUtils import get_AMLRunId
from dboperations.dboperations import executeStoredProcedure


class TensorflowTrainingLossDatabaseUpdateCallback(keras.callbacks.Callback):
    def __init__(self,params,idx=None):
        self.ModelName, self.outputPath = params
        AMLRunId = get_AMLRunId(self.outputPath)
        self.AMLRunId = AMLRunId
        self.StartDateTime = pd.to_datetime(datetime.now(), format='%Y.%m.%d %H:%M:%S')
        self.InternalModelNumber = idx
        
    def on_epoch_end(self, epoch, logs=None):
        print("End epoch {} of training; got log keys: {}".format(epoch, logs))
        if np.isnan(logs['loss']):
            logs['loss'] = 0
        if np.isnan(logs['val_loss']):
            logs['val_loss'] = 0
        epoch_loss = logs['loss']
        epoch_loss = round(float(epoch_loss),15)
        epoch_val_loss = logs['val_loss']
        epoch_val_loss = round(float(epoch_val_loss),15)
        EndDateTime = pd.to_datetime(datetime.now(), format='%Y.%m.%d %H:%M:%S')
        print(epoch_loss,epoch_val_loss)
        executeStoredProcedure("usp_InsertTrainingLossTracker","@EpochLoss=?, @EpochValLoss = ?, @Epoch = ?, @AMLRunId = ?, @InternalModelNumber=?, @StartDateTime = ?, @EndDateTime = ?", (
                epoch_loss, epoch_val_loss, epoch, self.AMLRunId, self.InternalModelNumber, self.StartDateTime, EndDateTime
        ),"logs",0)
