CREATE PROCEDURE [logs].[usp_getChildRunTracker]
@ChildAMLRunId VARCHAR(100) = NULL
AS
BEGIN
	SET NOCOUNT ON;

	SELECT [Id]
		  ,[Experiment]
		  ,[ModelName]
		  ,[InternalRunId]
		  ,[ChildAMLRunId]
	  FROM [logs].[childRunTracker]
	  WHERE (@ChildAMLRunId IS NULL OR @ChildAMLRunId = ChildAMLRunId)
END