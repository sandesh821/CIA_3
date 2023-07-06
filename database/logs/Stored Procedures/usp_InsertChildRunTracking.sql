
CREATE PROCEDURE [logs].[usp_InsertChildRunTracking] @Experiment varchar(100),
@InternalRunId varchar(100),
@ModelName varchar(100),
@ChildAMLRunId varchar(100)
AS
BEGIN
  SET NOCOUNT ON;

  IF EXISTS (SELECT
      1
    FROM [logs].[childRunTracker]
    WHERE ChildAMLRunId = @ChildAMLRunId)
  BEGIN
    UPDATE [logs].[childRunTracker]
    SET EndDateTime = GETDATE()
    WHERE ChildAMLRunId = @ChildAMLRunId
  END
  ELSE
  BEGIN
    INSERT INTO [logs].[childRunTracker] (Experiment
    , [ModelName]
    , InternalRunId
    , [ChildAMLRunId]
    , StartDateTime)
      VALUES (@Experiment, @ModelName, @InternalRunId, @ChildAMLRunId, GETDATE())
  END
END