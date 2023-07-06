
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 28, 2023
-- Description: Get model details
-- =============================================
CREATE PROCEDURE [golive].[usp_deleteEventConfiguration] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		DELETE
		FROM golive.EventConfiguration
		WHERE [ExperimentSetID] = @ExperimentSetID
END