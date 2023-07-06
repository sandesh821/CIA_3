CREATE PROCEDURE [logs].[usp_getRunIdsInfo]
AS
BEGIN
	SET NOCOUNT ON;

	SELECT p.AMLRunId as ParentRunId
		  ,c.ModelName
		  ,c.ChildAMLRunId as ChildRunId
	  FROM [logs].[runTracker] p
	  LEFT JOIN [logs].[childRunTracker] c ON p.Experiment = c.Experiment AND p.InternalRunID = c.InternalRunId
END