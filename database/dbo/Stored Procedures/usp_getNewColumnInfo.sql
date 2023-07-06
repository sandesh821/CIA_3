
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Get experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_getNewColumnInfo] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			ColumnDetails
		FROM [dbo].[newColumnInfo]
		WHERE [ExperimentSetID] = @ExperimentSetID
END