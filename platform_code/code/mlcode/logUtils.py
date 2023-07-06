from dboperations.dboperations import executeStoredProcedure
import pathlib

def get_AMLRunId(modelPath):
    # Create a Path object for the output path
    pathlib_outputPath = pathlib.Path(modelPath)
    # Get parts of the path as a tuple
    _, _, ExperimentTag, InternalRunID = pathlib_outputPath.parts
    # Execute a stored procedure and retrieve a row of data
    row = executeStoredProcedure("usp_getAMLRunTrackerRow","@Experiment=?, @InternalRunID = ?", (ExperimentTag, InternalRunID), "logs", 1)
    # Get the fourth element of the row (assuming the row has at least 4 elements)
    AMLRunId = row and row[4]
    return AMLRunId


def update_parent_training_run(modelPath,AMLRunId, Status):
    # Create a Path object for the output path
    pathlib_outputPath = pathlib.Path(modelPath)
    # Get parts of the path as a tuple
    _, ExperimentName, ExperimentTag, InternalRunID = pathlib_outputPath.parts
    # Execute a stored procedure and retrieve a row of data
    executeStoredProcedure("usp_InsertRunTracking","@ExperimentSet=?,@Experiment = ?, @InternalRunID = ?, @AMLRunId = ?, @RunStatus = ?", (ExperimentName,ExperimentTag,InternalRunID,AMLRunId, Status),"logs",0)


def get_ChildAMLRunId(modelPath):
    # Create a Path object for the output path
    pathlib_outputPath = pathlib.Path(modelPath)
    # Get parts of the path as a tuple
    _, _, ExperimentTag, InternalRunID = pathlib_outputPath.parts
    # Execute a stored procedure and retrieve a row of data
    row = executeStoredProcedure("usp_getChildRunTrackerRow","@Experiment=?, @InternalRunID = ?", (ExperimentTag, InternalRunID), "logs", 1)
    # Get the fourth element of the row (assuming the row has at least 4 elements)
    ChildAMLRunId = row and row[4]
    return ChildAMLRunId


def update_training_status(AMLRunId,status,total_epoch,pred_idx,n_trials,trial_number,ChildAMLRunId,horizon):
    AMLRunId and executeStoredProcedure("usp_InsertStatusTracker", "@AMLRunId = ?, @Status = ?,  @TotalEpoch = ?,  @InternalModelNumber = ?, @N_Trials = ?, @Trial_Number = ? , @ChildAMLRunId = ?, @Horizon = ?", (AMLRunId,status,total_epoch,pred_idx,n_trials,trial_number,ChildAMLRunId,horizon),"logs",0)
