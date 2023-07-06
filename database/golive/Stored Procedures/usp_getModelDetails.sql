
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 28, 2023
-- Description: Get model details
-- EXEC [golive].[usp_getModelDetails] 38
-- =============================================
CREATE PROCEDURE [golive].[usp_getModelDetails] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			[ModelDetails]
		FROM golive.ModelSelection
		WHERE [ExperimentSetID] = @ExperimentSetID
		AND IsDeleted IS NULL
END