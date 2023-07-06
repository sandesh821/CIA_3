
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: March 28, 2023
-- Description: Delete model details
-- =============================================
CREATE PROCEDURE [golive].usp_deleteModelDeployment @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		DELETE
		FROM golive.[modelDeployment]
		WHERE [ExperimentSetID] = @ExperimentSetID
END