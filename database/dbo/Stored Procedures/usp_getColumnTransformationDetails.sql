
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2023
-- Description: Get experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].[usp_getColumnTransformationDetails] @ExperimentSetID int
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON

		SELECT
			FileIdentifier, ColumnName, [Transformations]
		FROM [dbo].[columnTransformationDetails]
		WHERE [ExperimentSetID] = @ExperimentSetID
END