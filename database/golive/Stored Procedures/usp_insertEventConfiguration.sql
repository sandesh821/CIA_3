
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 30, 2023
-- Description: Insert go live event configuration details
-- =============================================
CREATE PROCEDURE [golive].[usp_insertEventConfiguration] 
@ExperimentSetID int,
@RetrainingSchedule VARCHAR(1000)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO golive.EventConfiguration
           (
			ExperimentSetID,
			[RetrainingSchedule]
			)
     VALUES
           (@ExperimentSetID
		   , @RetrainingSchedule
		 )
  END
END