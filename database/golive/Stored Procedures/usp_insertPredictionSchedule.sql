-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 07, 2022
-- Description: Insert Prediction Schedule
-- EXEC [golive].[usp_insertPredictionSchedule]  38,'00:00:00'
-- =============================================
CREATE PROCEDURE [golive].[usp_insertPredictionSchedule] 
@ExperimentSetID INT,
@PredictionDate [varchar](100) NULL
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
	
		INSERT INTO golive.[predictionSchedule]
			   (
				ExperimentSetID,
				[PredictionDate] 
				)
		 VALUES
			   (@ExperimentSetID
			   ,@PredictionDate
				)
	
END