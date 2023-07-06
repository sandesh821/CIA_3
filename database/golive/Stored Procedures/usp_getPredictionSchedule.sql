-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 07, 2022
-- Description: Insert Prediction Schedule
-- EXEC [golive].[usp_getPredictionSchedule]  38
-- =============================================
CREATE PROCEDURE golive.[usp_getPredictionSchedule] 
@ExperimentSetID INT
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
	SELECT [PredictionDate] FROM golive.[predictionSchedule]  WHERE Status is NULL AND ExperimentSetID = @ExperimentSetID
  END
END