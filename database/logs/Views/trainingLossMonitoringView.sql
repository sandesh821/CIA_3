CREATE VIEW [logs].[trainingLossMonitoringView]
AS
SELECT 
[statusTracker].[Status],
[statusTracker].[TotalEpoch],
[statusTracker].[AMLRunId],
[statusTracker].[CreatedOn] as [CreatedOn_statusTracker],
[statusTracker].[InternalModelNumber] as [InternalModelNumber_statusTracker],
[statusTracker].[ChildAMLRunId], [runTracker].[ExperimentSet],
[runTracker].[InternalRunID],
[runTracker].[RunStatus],
[runTracker].[CreatedOn] as [CreatedOn_runTracker],
[runTracker].[StartDateTime] as [StartDateTime_runTracker],
[runTracker].[EndDateTime] as [EndDateTime_runTracker], [childRunTracker].[Experiment],
[childRunTracker].[ModelName],
[childRunTracker].[CreatedOn] as [CreatedOn_childRunTracker],
[childRunTracker].[StartDateTime] as [StartDateTime_childRunTracker],
[childRunTracker].[EndDateTime] as [EndDateTime_childRunTracker],  [runTrainingLossTracker].[EpochLoss] as Loss,
'EpochLoss' as Loss_Type,
[runTrainingLossTracker].[Epoch],
[runTrainingLossTracker].[InternalModelNumber] as [InternalModelNumber_runTrainingLossTracker],
[runTrainingLossTracker].[CreatedOn] as [CreatedOn_runTrainingLossTracker],
[runTrainingLossTracker].[StartDateTime] as [StartDateTime_runTrainingLossTracker],
[runTrainingLossTracker].[EndDateTime] as [EndDateTime_runTrainingLossTracker] FROM 
[logs].[statusTracker] as [statusTracker] JOIN [logs].[runTracker] as [runTracker]
ON [statusTracker].[AMLRunId] = [runTracker].[AMLRunId] JOIN [logs].[childRunTracker] as [childRunTracker]
ON [runTracker].[InternalRunID] = [childRunTracker].[InternalRunID] AND 
[statusTracker].[ChildAMLRunId] = [childRunTracker].[ChildAMLRunId] JOIN [logs].[runTrainingLossTracker] as [runTrainingLossTracker]
ON [statusTracker].[AMLRunId] = [runTrainingLossTracker].[AMLRunId] WHERE 
[statusTracker].[InternalModelNumber] = -1
UNION 
SELECT 
[statusTracker].[Status],
[statusTracker].[TotalEpoch],
[statusTracker].[AMLRunId],
[statusTracker].[CreatedOn] as [CreatedOn_statusTracker],
[statusTracker].[InternalModelNumber] as [InternalModelNumber_statusTracker],
[statusTracker].[ChildAMLRunId], [runTracker].[ExperimentSet],
[runTracker].[InternalRunID],
[runTracker].[RunStatus],
[runTracker].[CreatedOn] as [CreatedOn_runTracker],
[runTracker].[StartDateTime] as [StartDateTime_runTracker],
[runTracker].[EndDateTime] as [EndDateTime_runTracker], [childRunTracker].[Experiment],
[childRunTracker].[ModelName],
[childRunTracker].[CreatedOn] as [CreatedOn_childRunTracker],
[childRunTracker].[StartDateTime] as [StartDateTime_childRunTracker],
[childRunTracker].[EndDateTime] as [EndDateTime_childRunTracker], 
[runTrainingLossTracker].[EpochValLoss] as Loss,
'EpochValLoss' as Loss_Type,
[runTrainingLossTracker].[Epoch],
[runTrainingLossTracker].[InternalModelNumber] as [InternalModelNumber_runTrainingLossTracker],
[runTrainingLossTracker].[CreatedOn] as [CreatedOn_runTrainingLossTracker],
[runTrainingLossTracker].[StartDateTime] as [StartDateTime_runTrainingLossTracker],
[runTrainingLossTracker].[EndDateTime] as [EndDateTime_runTrainingLossTracker] FROM 
[logs].[statusTracker] as [statusTracker] JOIN [logs].[runTracker] as [runTracker]
ON [statusTracker].[AMLRunId] = [runTracker].[AMLRunId] JOIN [logs].[childRunTracker] as [childRunTracker]
ON [runTracker].[InternalRunID] = [childRunTracker].[InternalRunID] AND 
[statusTracker].[ChildAMLRunId] = [childRunTracker].[ChildAMLRunId] JOIN [logs].[runTrainingLossTracker] as [runTrainingLossTracker]
ON [statusTracker].[AMLRunId] = [runTrainingLossTracker].[AMLRunId] WHERE 
[statusTracker].[InternalModelNumber] = -1