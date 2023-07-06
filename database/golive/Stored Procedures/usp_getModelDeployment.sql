
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 30, 2023
-- Description: Get data ingestion
-- =============================================
CREATE PROCEDURE [golive].usp_getModelDeployment @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			[deploymentManagerConfig]
		FROM golive.[modelDeployment]
		WHERE [ExperimentSetID] = @ExperimentSetID
END