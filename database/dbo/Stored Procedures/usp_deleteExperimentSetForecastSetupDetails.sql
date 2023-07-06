
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: December 12, 2022
-- Description: Delete experiment set forecast setup details
-- =============================================
CREATE PROCEDURE [dbo].[usp_deleteExperimentSetForecastSetupDetails] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  DELETE FROM [dbo].[experimentSetForecastSetupDetails]
		   WHERE [ExperimentSetID] = @ExperimentSetID
END