
-- =============================================
-- Author:      Astha Agarwal
-- Create Date: January 13, 2022
-- Description: Insert experiment set transformation details
-- =============================================
CREATE PROCEDURE [dbo].usp_insertInterpolationInfo 
@ExperimentSetID int,
@ColumnDetails NVARCHAR(MAX)
AS
BEGIN
  -- SET NOCOUNT ON added to prevent extra result sets from
  -- interfering with SELECT statements.
  SET NOCOUNT ON
  BEGIN
    INSERT INTO [dbo].[interpolationInfo]
           (
			ExperimentSetID,
			ColumnDetails)
     VALUES
           (@ExperimentSetID
		   , @ColumnDetails )
  END
END