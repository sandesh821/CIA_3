


-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Delete experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].usp_deleteNewColumnInfo @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  DELETE FROM [dbo].[newColumnInfo]
		   WHERE [ExperimentSetID] = @ExperimentSetID
END