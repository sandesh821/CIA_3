from datetime import datetime
import pandas as pd
import pathlib

class TrainingLossUpdateCallback(object):
    def __init__(self, params):
        self.ModelName, self.outputPath = params
        pathlib_outputPath = pathlib.Path(self.outputPath)
        _, ExperimentName, ExperimentTag, InternalRunID = pathlib_outputPath.parts
        self.ExperimentName = ExperimentName
        self.InternalRunID = InternalRunID
        self.ExperimentTag = ExperimentTag
        self.StartDateTime = pd.to_datetime(datetime.now(), format='%Y.%m.%d %H:%M:%S')
        self.EndDateTime = None
        self.training_batch_loss_list = []
        self.evaluating_batch_loss_list = []
        self.training_epoch_loss_list = []
        self.training_epoch_val_loss_list = []
        self.evaluating_epoch_loss_list = []
        self.evaluating_epoch_val_loss_list = []
        self.epoch_loss = None
        self.epoch_val_loss = None
        self.batch = None
        self.epoch = None

    def _training_loss_dataframe(self):
        df = pd.DataFrame()
        if self.training_batch_loss_list:
            df['TrainingBatchLoss'] = self.training_batch_loss_list
        else:
            df['TrainingBatchLoss'] = None
        if self.training_epoch_loss_list:
            df['EpochLoss'] = self.training_epoch_loss_list
        else:
            df['EpochLoss'] = None
        if self.training_epoch_val_loss_list:
            df['EpochValLoss'] = self.training_epoch_val_loss_list
        else:
            df['EpochValLoss'] = None
        df['ModelName'] = self.ModelName
        df['Epoch'] = self.epoch
        df['Batch'] = self.batch
        df['ExperimentName'] = self.ExperimentName
        df['ExperimentTag'] = self.ExperimentTag
        df['InternalRunID'] = self.InternalRunID
        df['StartDateTime'] = self.StartDateTime
        df['EndDateTime'] = self.EndDateTime
        df['OutputPath'] = self.outputPath
        return df

    def _evaluating_loss_dataframe(self):
        df = pd.DataFrame()
        if self.evaluating_batch_loss_list:
            df['EvaluatingBatchLoss'] = self.evaluating_batch_loss_list
        else:
            df['EvaluatingBatchLoss'] = None
        if self.evaluating_epoch_loss_list:
            df['EpochLoss'] = self.evaluating_epoch_loss_list
        else:
            df['EpochLoss'] = None
        if self.evaluating_epoch_val_loss_list:
            df['EpochValLoss'] = self.evaluating_epoch_val_loss_list
        else:
            df['EpochValLoss'] = None
        df['ModelName'] = self.ModelName
        df['Epoch'] = self.epoch
        df['Batch'] = self.batch
        df['ExperimentName'] = self.ExperimentName
        df['ExperimentTag'] = self.ExperimentTag
        df['InternalRunID'] = self.InternalRunID
        df['StartDateTime'] = self.StartDateTime
        df['EndDateTime'] = self.EndDateTime
        df['OutputPath'] = self.outputPath
        return df