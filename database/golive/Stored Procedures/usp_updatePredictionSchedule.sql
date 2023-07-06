-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 07, 2022
-- Description: Insert Prediction Schedule
-- EXEC [golive].[usp_updatePredictionSchedule]  38,'2023-04-04 00:00:00'
-- =============================================
CREATE PROCEDURE [golive].[usp_updatePredictionSchedule] 
@ExperimentSetID INT,
@PredictionDate [varchar](100) NULL,
@MergeResampling SMALLINT = NULL,
@APIDataRefresh SMALLINT = NULL,
@DataCleaning SMALLINT = NULL,
@DataDriftValidation SMALLINT = NULL,
@ModelDriftValidation SMALLINT = NULL
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
	IF @MergeResampling IS NULL AND @APIDataRefresh IS NULL AND @DataCleaning IS NULL AND @DataDriftValidation IS NULL AND @ModelDriftValidation IS NULL AND 
	EXISTS (SELECT 1 FROM golive.[predictionSchedule]  WHERE [PredictionDate] = @PredictionDate)
	BEGIN
		UPDATE golive.[predictionSchedule]
		SET Status = 'Processed'
		WHERE [PredictionDate] = @PredictionDate
		AND ExperimentSetId = @ExperimentSetID

		INSERT INTO golive.[predictionSchedule]
			   (
				ExperimentSetID,
				[PredictionDate],
				PreviousPredictionDate
				)
		 VALUES
			   (@ExperimentSetID
			   ,CONVERT(VARCHAR(100),DATEADD(day,1,@PredictionDate),120)
			   ,@PredictionDate
				)
	END
	ELSE IF @MergeResampling IS NOT NULL
		UPDATE golive.[predictionSchedule]
		SET MergedResampling = @MergeResampling
		WHERE [PredictionDate] = @PredictionDate
		AND ExperimentSetId = @ExperimentSetID
	ELSE IF @APIDataRefresh IS NOT NULL
		UPDATE golive.[predictionSchedule]
		SET APIDataRefresh = @APIDataRefresh
		WHERE [PredictionDate] = @PredictionDate
		AND ExperimentSetId = @ExperimentSetID
	ELSE IF @DataCleaning IS NOT NULL
		UPDATE golive.[predictionSchedule]
		SET DataCleaning = @DataCleaning
		WHERE [PredictionDate] = @PredictionDate
		AND ExperimentSetId = @ExperimentSetID
	ELSE IF @DataDriftValidation IS NOT NULL
		UPDATE golive.[predictionSchedule]
		SET DataDriftValidation = @DataDriftValidation
		WHERE [PredictionDate] = @PredictionDate
		AND ExperimentSetId = @ExperimentSetID
	ELSE IF @ModelDriftValidation IS NOT NULL
		UPDATE golive.[predictionSchedule]
		SET ModelDriftValidation = @ModelDriftValidation
		WHERE [PredictionDate] = @PredictionDate
		AND ExperimentSetId = @ExperimentSetID
  END
END