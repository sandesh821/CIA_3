


-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Delete experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_deleteColumnTransformationDetails] @ExperimentSetID int, @FileIdentifier VARCHAR(100), @ColumnName VARCHAR(100)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

  DELETE FROM [dbo].columnTransformationDetails
		   WHERE [ExperimentSetID] = @ExperimentSetID
		   AND FileIdentifier = @FileIdentifier
		   AND ColumnName = @ColumnName
END