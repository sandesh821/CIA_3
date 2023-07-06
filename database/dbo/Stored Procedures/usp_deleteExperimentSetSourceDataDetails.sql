

-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 03, 2023
-- Description: Delete experiment set source data details
-- =============================================
CREATE PROCEDURE [dbo].[usp_deleteExperimentSetSourceDataDetails] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  DELETE FROM [dbo].[experimentSetSourceDataDetails]
		   WHERE [ExperimentSetID] = @ExperimentSetID
END