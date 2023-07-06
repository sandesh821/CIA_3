CREATE VIEW [logs].[slicerView] 
AS SELECT 
[runTracker].[ExperimentSet] as  [Experiment Set Name],
[childRunTracker].[Experiment] as [Experiment Name],
[runTracker].[InternalRunID], 
[childRunTracker].[ModelName] as [Model Name],
[runTracker].[RunStatus] as [Experiment Run Status],
[statusTracker].[AMLRunId],
[statusTracker].[ChildAMLRunId]
 FROM 
[logs].[statusTracker] as [statusTracker]
JOIN [logs].[runTracker] as [runTracker]
ON [statusTracker].[AMLRunId] = [runTracker].[AMLRunId] 
JOIN [logs].[childRunTracker] as [childRunTracker]
ON [runTracker].[InternalRunID] = [childRunTracker].[InternalRunID]
AND 
[statusTracker].[ChildAMLRunId] = [childRunTracker].[ChildAMLRunId]