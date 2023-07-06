--EXEC [logs].[usp_InsertRunTracking] 'AmplusDemo', 'experiment7', '20230130222223', '0efd7472-1087-4a8e-b398-1fe661b6d1c7','Finished'
--EXEC [logs].[usp_InsertRunTracking] 'AmplusDemo', 'experiment1', '20230131044619', 'fe23fe19-18f7-4b38-8833-bdf425dce685','Failed'
CREATE PROCEDURE [logs].[usp_InsertRunTracking]
@ExperimentSet VARchar(100),
@Experiment VARCHAR(100),
@InternalRunID VARCHAR(100),
@AMLRunId VARCHAR(100),
@RunStatus VARCHAR(50)
AS
BEGIN
	SET NOCOUNT ON;

  IF EXISTS (SELECT 1 FROM [logs].[runTracker] WHERE [AMLRunId] = @AMLRunId)
  BEGIN

    UPDATE [logs].[runTracker]
    SET EndDateTime = GETDATE(),
	[RunStatus] = @RunStatus
    WHERE [AMLRunId] = @AMLRunId

	-- Remove experiment from scheduled list if experiment fails, is cancelled or finished
	IF (@RunStatus = 'Canceled' OR @RunStatus = 'Failed')
	BEGIN
		PRINT('Pipeline Failed')
		EXEC [dbo].[usp_updateExperimentStatus] @ExperimentSet, @Experiment, 2
	END
	IF (@RunStatus = 'Finished')
	BEGIN
		EXEC [dbo].[usp_updateExperimentStatus] @ExperimentSet, @Experiment, 3
	END
	IF (@RunStatus LIKE 'Batch%')
	BEGIN
		EXEC [dbo].[usp_updateExperimentStatus] @ExperimentSet, @Experiment, 5
	END

  END
  ELSE
	BEGIN
		INSERT INTO [logs].[runTracker]
				   ([ExperimentSet]
				   ,[Experiment]
				   ,[InternalRunID]
				   ,[AMLRunId]
				   ,[RunStatus]
				   ,[StartDateTime])
			 VALUES
				   (@ExperimentSet
				   ,@Experiment
				   ,@InternalRunID
				   ,@AMLRunId
				   ,@RunStatus
				   ,GETDATE())
	
			IF @RunStatus = 'Batch Scoring Started'
			BEGIN
				EXEC [dbo].[usp_updateExperimentStatus] @ExperimentSet, @Experiment, 4
			END
			ELSE
			BEGIN
				-- Move experiment to executing stage
				EXEC [dbo].[usp_updateExperimentStatus] @ExperimentSet, @Experiment, 1
			END
	END	
END