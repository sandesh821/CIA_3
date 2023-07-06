from datetime import datetime
import pandas as pd

from pytorch_lightning.callbacks import Callback

from logUtils import get_AMLRunId
from dboperations.dboperations import executeStoredProcedure


class TorchTrainingLossDatabaseUpdateCallback(Callback):
    def __init__(self,params,idx=None):
        self.ModelName, self.outputPath = params
        AMLRunId = get_AMLRunId(self.outputPath)
        self.AMLRunId = AMLRunId
        self.StartDateTime = pd.to_datetime(datetime.now(), format='%Y.%m.%d %H:%M:%S')
        self.epoch  = 0
        self.InternalModelNumber = idx

    def on_train_epoch_end(self, trainer, pl_module):
        batch_loss = trainer.callback_metrics
        epoch_train_loss = batch_loss.get('train_loss')
        epoch_val_loss = batch_loss.get('val_loss')
        epoch_train_loss = epoch_train_loss and float(epoch_train_loss)
        epoch_val_loss = epoch_val_loss and float(epoch_val_loss)
        self.epoch += 1
        EndDateTime = pd.to_datetime(datetime.now(), format='%Y.%m.%d %H:%M:%S')
        executeStoredProcedure("usp_InsertTrainingLossTracker","@EpochLoss=?, @EpochValLoss = ?, @Epoch = ?, @AMLRunId = ?, @InternalModelNumber = ?, @StartDateTime = ?, @EndDateTime = ?", (
            epoch_train_loss, epoch_val_loss, self.epoch, self.AMLRunId, self.InternalModelNumber, self.StartDateTime, EndDateTime
        ),"logs",0)
