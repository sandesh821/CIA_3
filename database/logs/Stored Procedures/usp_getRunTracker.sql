CREATE PROCEDURE [logs].[usp_getRunTracker]
@ParentAMLRunId VARCHAR(100) = NULL,
@RunStatus VARCHAR(20) = NULL
AS
BEGIN
	SET NOCOUNT ON;

	SELECT [Id]
		  ,[ExperimentSet]
		  ,r.[Experiment]
		  ,r.InternalRunId
		  ,[AMLRunId]
		  ,[RunStatus]
	  FROM logs.runTracker r
	  INNER JOIN (SELECT [Experiment]
		  ,MAX(CONVERT(bigint,[InternalRunID])) InternalRunId
	  FROM logs.runTracker
	  GROUP BY Experiment) m ON r.Experiment = m.Experiment AND r.InternalRunID = m.InternalRunId
	  WHERE (@ParentAMLRunId IS NULL OR @ParentAMLRunId = AMLRunId) AND (@RunStatus IS NULL OR @RunStatus = RunStatus)
END